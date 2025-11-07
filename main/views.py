from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone

from .models import Project, Tag, Comment
from .forms import CommentForm

from datetime import datetime

# Create views here.

def home(request):
    projects = Project.objects.all()  # Gives access to all projects on the home page.
    tags = Tag.objects.all()
    # Rendering just means to show on the screen.
    return render(request, "index.html", {"projects": projects, "tags": tags})


def contact(request):
    """
    Handle contact form submissions and render the contact page.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message_text = request.POST.get("message", "").strip()

        # Form data can be processed here if needed 

        messages.success(request, "Message received. A response will be sent if required.")
        return redirect("contact")

    return render(request, "contact.html")


def about(request):
    return render(request, "about.html")


def project(request, id):
    # Look for the pk specified, within the project model.
    project_obj = get_object_or_404(Project, pk=id)

    # ADDED: list comments and show empty form
    comments = project_obj.comments.select_related("user").all()

    # allow either Django-auth or sheet-auth to post
    can_comment = request.user.is_authenticated or bool(
        request.session.get("user_email")
    )
    form = CommentForm() if can_comment else None

    return render(
        request,
        "project.html",
        {
            "project": project_obj,
            "comments": comments,
            "form": form,  # used for the "create comment" form
        },
    )


# partial view so the home page modal can load comments for a single project
def project_comments_partial(request, id):
    """
    Render just the comments + (optional) form for a specific project.
    Used by the home page popup.
    """
    project_obj = get_object_or_404(Project, pk=id)
    comments = project_obj.comments.select_related("user").order_by("-created_at")

    # if logged in via Django OR via sheet, show form
    can_comment = request.user.is_authenticated or bool(
        request.session.get("user_email")
    )
    form = CommentForm() if can_comment else None

    return render(
        request,
        "partials/project_comments.html",
        {
            "project": project_obj,
            "comments": comments,
            "form": form,
        },
    )


# Below is the ability to add comments to satisfy CRUD.

@require_POST
def comment_create(request, id):
    """
    Create a new comment on a project.
    only accepts:
    - Django authenticated users
    - Sheet/session users (email + name stored in session)
    """
    project_obj = get_object_or_404(Project, pk=id)

    # detect auth method
    is_django_user = request.user.is_authenticated
    sheet_email = request.session.get("user_email")
    sheet_name = request.session.get("user_name")

    # block if neither is present
    if not is_django_user and not sheet_email:
        messages.error(request, "Sign in is required to comment.")
        return redirect(reverse("project", kwargs={"id": project_obj.pk}))

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.project = project_obj

        if is_django_user:
            # normal Django user FK
            comment.user = request.user
        else:
            # sheet/session path — model must have author_name for this to work
            comment.author_name = sheet_name or sheet_email

        comment.save()
        messages.success(request, "Comment posted.")
    else:
        messages.error(request, "Please fix the errors and try again.")

    return redirect(reverse("project", kwargs={"id": project_obj.pk}))


@login_required
def comment_update(request, id, comment_id):
    """
    Update an existing comment (only by its owner).
    """
    project_obj = get_object_or_404(Project, pk=id)
    comment = get_object_or_404(
        Comment, pk=comment_id, project=project_obj, user=request.user
    )

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, "Comment updated.")
        else:
            messages.error(request, "Please fix the errors and try again.")

    return redirect(reverse("project", kwargs={"id": project_obj.pk}))


@login_required
@require_POST
def comment_delete(request, id, comment_id):
    """
    Delete a comment (only by its owner).
    """
    project_obj = get_object_or_404(Project, pk=id)
    comment = get_object_or_404(
        Comment, pk=comment_id, project=project_obj, user=request.user
    )

    comment.delete()
    messages.success(request, "Comment deleted.")

    return redirect(reverse("project", kwargs={"id": project_obj.pk}))


# this is a Google Sheet helper / auth 
def get_users_sheet():
    """
    Returns the Google Sheet worksheet that stores users.
    Assumes credentials configured in settings.
    """
    import gspread 
    
    gc = gspread.service_account(filename=settings.GOOGLE_SERVICE_ACCOUNT_FILE)
    sh = gc.open_by_key(settings.GOOGLE_SHEET_ID)  # set in settings
    ws = sh.worksheet("user")  # sheet/tab name
    return ws


@require_POST
def auth_register(request):
    """
    Register a new user in Google Sheets.
    Expected fields: username, email, password.
    """
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "").strip()
    username = request.POST.get("username", "").strip()

    if not email or not password or not username:
        return JsonResponse(
            {"success": False, "error": "All fields required."},
            status=400,
        )

    # open sheet
    try:
        ws = get_users_sheet()
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Sheet error: {e}"},
            status=500,
        )

    # read rows using the exact header order in the sheet
    try:
        records = ws.get_all_records(
            expected_headers=["User Name", "Email", "Date Joined", "Password"]
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Read error: {e}"},
            status=500,
        )

    # check for duplicate email
    for row in records:
        if row.get("Email", "").strip().lower() == email:
            return JsonResponse(
                {"success": False, "error": "Email already registered."},
                status=400,
            )
        
    hashed_password = make_password(password)

    # build row in same order as header
    now = timezone.localtime(timezone.now())   # UK time
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    new_row = [username, email, now_str, hashed_password]

    # write to sheet
    try:
        ws.append_row(new_row)
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Write error: {e}"},
            status=500,
        )

    # store mini-session for comments
    request.session["user_email"] = email
    request.session["user_name"] = username

    return JsonResponse({"success": True, "username": username})


@require_POST
def auth_login(request):
    """
    Logs a user in by checking email + password against Google Sheet.
    """
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "").strip()

    if not email or not password:
        return JsonResponse(
            {"success": False, "error": "Email and password required."}, status=400
        )

    try:
        ws = get_users_sheet()
        records = ws.get_all_records(
            expected_headers=["User Name", "Email", "Date Joined", "Password"]
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Sheet error: {e}"}, status=500)

    matched = None
    for row in records:
        row_email = row.get("Email", "").strip().lower()
        row_pass = row.get("Password", "").strip() if "Password" in row else ""
        if row_email == email:
            # check hashed password
            if check_password(password, row_pass):
                matched = row
                break

    if not matched:
        return JsonResponse(
            {"success": False, "error": "Invalid credentials."}, status=401
        )

    # set session for comment posting
    request.session["user_email"] = matched.get("Email")
    request.session["user_name"] = (
        matched.get("User Name") or matched.get("Username") or "Guest"
    )

    return JsonResponse(
        {
            "success": True,
            "username": request.session["user_name"],
        }
    )

# Self-learn note:
#  Views are functions called when wanting to display a page.
#  Models need to be imported for this file to work.
#  Session values can be used to show/hide UI parts on the template.
