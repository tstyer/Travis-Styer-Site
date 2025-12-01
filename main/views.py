from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
import gspread
from django.views.decorators.csrf import csrf_exempt


from .models import Project, Tag, Comment
from .forms import CommentForm, ContactForm

from datetime import datetime

USER_SHEET_HEADERS = ["User Name", "Email", "Date Joined", "Password (Now Hashed)"]
PASSWORD_HEADER = "Password (Now Hashed)"   # must match sheet header 


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
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message_text = form.cleaned_data["message"]

            messages.success(request, "Message sent successfully.")
            return redirect("contact")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})


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
    session_author_name = request.session.get("author_name")

    # consider any of these as valid sheet/session identity
    has_sheet_identity = bool(sheet_email or sheet_name or session_author_name)

    # block if neither is present
    if not is_django_user and not has_sheet_identity:
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
            comment.author_name = sheet_name or session_author_name or sheet_email

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
    if getattr(settings, "GOOGLE_CREDS_DICT", None):
        gc = gspread.service_account_from_dict(settings.GOOGLE_CREDS_DICT)
    else:
        gc = gspread.service_account(filename=settings.GOOGLE_SERVICE_ACCOUNT_FILE)

    sh = gc.open_by_key(settings.GOOGLE_SHEET_ID)
    ws = sh.worksheet("user")
    return ws

@csrf_exempt
@require_POST
def auth_register(request):
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "").strip()
    username = request.POST.get("username", "").strip()

    # only email + password are truly required
    if not email or not password:
        return JsonResponse(
            {"success": False, "error": "All fields required."},
            status=400,
        )

    # if no username was sent (your current modal), derive from email
    if not username:
        username = email.split("@")[0]

    try:
        ws = get_users_sheet()
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Sheet error: {e}"},
            status=500,
        )

    # read rows using the exact header order in the sheet
    try:
        records = ws.get_all_records(expected_headers=USER_SHEET_HEADERS)
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

    now = timezone.localtime(timezone.now())
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # build row in same order as USER_SHEET_HEADERS:
    # ["User Name", "Email", "Date Joined", "Password (Now Hashed)"]
    new_row = [username, email, now_str, hashed_password]

    try:
        ws.append_row(new_row)
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Write error: {e}"},
            status=500,
        )

    request.session["user_email"] = email
    request.session["user_name"] = username

    return JsonResponse({"success": True, "username": username})


def auth_login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "auth_login.html", {"email": email})

        try:
            ws = get_users_sheet()
            records = ws.get_all_records(expected_headers=USER_SHEET_HEADERS)
        except Exception as e:
            messages.error(request, f"Sheet error: {e}")
            return render(request, "auth_login.html", {"email": email})

        matched = None
        for row in records:
            row_email = row.get("Email", "").strip().lower()

            # Safe conversion (fixes the int/no-strip error)
            raw_value = row.get(PASSWORD_HEADER, "")
            row_pass = str(raw_value or "").strip()

            if row_email == email and row_pass and check_password(password, row_pass):
                matched = row
                break

        if not matched:
            messages.error(request, "Invalid credentials.")
            return render(request, "auth_login.html", {"email": email})

        request.session["user_email"] = matched.get("Email")
        request.session["user_name"] = (
            matched.get("User Name") or matched.get("Username") or "Guest"
        )

        next_url = request.POST.get("next") or request.GET.get("next") or reverse("home")
        return redirect(next_url)

    return render(request, "auth_login.html")


# Self-learn note:
#  Views are functions called when wanting to display a page.
#  Models need to be imported for this file to work.
#  Session values can be used to show/hide UI parts on the template.
