import logging

import gspread
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.http import HttpResponseForbidden, HttpResponseTooManyRequests, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CommentForm, ContactForm
from .models import Comment, Project, Tag

logger = logging.getLogger(__name__)

# Google Sheet header constants
USER_SHEET_HEADERS = ["User Name", "Email", "Date Joined", "Password (Now Hashed)"]
PASSWORD_HEADER = "Password (Now Hashed)"  # must match sheet header


# --------------------
# BASIC PAGES
# --------------------
def home(request):
    projects = Project.objects.all()
    tags = Tag.objects.all()
    return render(request, "index.html", {"projects": projects, "tags": tags})


def contact(request):
    """
    Handle contact form submissions and render the contact page.
    """
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, "Message sent successfully.")
            return redirect("contact")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})


def about(request):
    return render(request, "about.html")


def project(request, id):
    """
    Full project detail page.
    """
    project_obj = get_object_or_404(Project, pk=id)
    comments = project_obj.comments.select_related("user").order_by("-created_at")

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
            "form": form,
        },
    )


# --------------------
# COMMENTS: PARTIAL + CRUD
# --------------------
def project_comments_partial(request, id):
    """
    Render just the comments + (optional) form for a specific project.
    Used by the home page popup/modal.
    """
    project_obj = get_object_or_404(Project, pk=id)
    comments = project_obj.comments.select_related("user").order_by("-created_at")

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


@require_POST
def comment_create(request, id):
    """
    Create a new comment on a project.

    - Normal POST: redirect back to the project page
    - AJAX (from home-page modal): return updated comments partial HTML
    """
    project_obj = get_object_or_404(Project, pk=id)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    # detect auth method
    is_django_user = request.user.is_authenticated
    sheet_email = request.session.get("user_email")
    sheet_name = request.session.get("user_name")
    session_author_name = request.session.get("author_name")
    has_sheet_identity = bool(sheet_email or sheet_name or session_author_name)

    # block if neither is present
    if not is_django_user and not has_sheet_identity:
        if is_ajax:
            return HttpResponseForbidden("Sign in required.")
        messages.error(request, "Sign in is required to comment.")
        return redirect(reverse("project", kwargs={"id": project_obj.pk}))

    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.project = project_obj

        if is_django_user:
            comment.user = request.user
        else:
            # comments coming from sheet/session auth
            comment.author_name = sheet_name or session_author_name or sheet_email
            comment.author_email = sheet_email or ""

        comment.save()

        if is_ajax:
            comments = project_obj.comments.select_related("user").order_by(
                "-created_at"
            )
            can_comment = is_django_user or has_sheet_identity
            new_form = CommentForm() if can_comment else None

            return render(
                request,
                "partials/project_comments.html",
                {
                    "project": project_obj,
                    "comments": comments,
                    "form": new_form,
                },
            )

        messages.success(request, "Comment posted.")
    else:
        if is_ajax:
            comments = project_obj.comments.select_related("user").order_by(
                "-created_at"
            )
            return render(
                request,
                "partials/project_comments.html",
                {
                    "project": project_obj,
                    "comments": comments,
                    "form": form,
                },
            )
        messages.error(request, "Please fix the errors and try again.")

    return redirect(reverse("project", kwargs={"id": project_obj.pk}))


@require_POST
def comment_update(request, id, comment_id):
    """
    Update an existing comment.

    - Django users: can edit comments where comment.user == request.user
    - Sheet/session users: can edit comments where author_name OR author_email matches their session
    - AJAX: return updated partial; normal POST: redirect back to project
    """
    project_obj = get_object_or_404(Project, pk=id)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    is_django_user = request.user.is_authenticated
    sheet_email = request.session.get("user_email")
    sheet_name = request.session.get("user_name")
    session_author = request.session.get("author_name")
    has_sheet_identity = bool(sheet_email or sheet_name or session_author)

    # locate comment + ownership
    if is_django_user:
        comment = get_object_or_404(
            Comment,
            pk=comment_id,
            project=project_obj,
            user=request.user,
        )
    elif has_sheet_identity:
        identities = {v for v in [sheet_name, session_author, sheet_email] if v}
        comment = get_object_or_404(
            Comment,
            pk=comment_id,
            project=project_obj,
            user__isnull=True,
        )

        is_owner = (comment.author_name and comment.author_name in identities) or (
            comment.author_email and comment.author_email in identities
        )

        if not is_owner:
            if is_ajax:
                return HttpResponseForbidden("Not allowed.")
            messages.error(request, "You cannot edit this comment.")
            return redirect(reverse("project", kwargs={"id": project_obj.pk}))
    else:
        if is_ajax:
            return HttpResponseForbidden("Not allowed.")
        messages.error(request, "You must be signed in to edit comments.")
        return redirect(reverse("project", kwargs={"id": project_obj.pk}))

    form = CommentForm(request.POST, instance=comment)
    if form.is_valid():
        form.save()

        if is_ajax:
            comments = project_obj.comments.select_related("user").order_by(
                "-created_at"
            )
            can_comment = is_django_user or has_sheet_identity
            new_form = CommentForm() if can_comment else None

            return render(
                request,
                "partials/project_comments.html",
                {
                    "project": project_obj,
                    "comments": comments,
                    "form": new_form,
                },
            )

        messages.success(request, "Comment updated.")
    else:
        if is_ajax:
            comments = project_obj.comments.select_related("user").order_by(
                "-created_at"
            )
            return render(
                request,
                "partials/project_comments.html",
                {
                    "project": project_obj,
                    "comments": comments,
                    "form": form,
                },
            )
        messages.error(request, "Please fix the errors and try again.")

    return redirect(reverse("project", kwargs={"id": project_obj.pk}))


@require_POST
def comment_delete(request, id, comment_id):
    """
    Delete a comment.

    - Django users: can delete comments where comment.user == request.user
    - Sheet/session users: can delete comments where author_name OR author_email matches their session
    - AJAX: return updated partial; normal POST: redirect back to project
    """
    project_obj = get_object_or_404(Project, pk=id)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    is_django_user = request.user.is_authenticated
    sheet_email = request.session.get("user_email")
    sheet_name = request.session.get("user_name")
    session_author = request.session.get("author_name")
    has_sheet_identity = bool(sheet_email or sheet_name or session_author)

    if is_django_user:
        comment = get_object_or_404(
            Comment,
            pk=comment_id,
            project=project_obj,
            user=request.user,
        )
    elif has_sheet_identity:
        identities = {v for v in [sheet_name, session_author, sheet_email] if v}
        comment = get_object_or_404(
            Comment,
            pk=comment_id,
            project=project_obj,
            user__isnull=True,
        )

        is_owner = (comment.author_name and comment.author_name in identities) or (
            comment.author_email and comment.author_email in identities
        )

        if not is_owner:
            if is_ajax:
                return HttpResponseForbidden("Not allowed.")
            messages.error(request, "You cannot delete this comment.")
            return redirect(reverse("project", kwargs={"id": project_obj.pk}))
    else:
        if is_ajax:
            return HttpResponseForbidden("Not allowed.")
        messages.error(request, "You must be signed in to delete comments.")
        return redirect(reverse("project", kwargs={"id": project_obj.pk}))

    comment.delete()

    if not is_ajax:
        messages.success(request, "Comment deleted.")

    if is_ajax:
        comments = project_obj.comments.select_related("user").order_by("-created_at")
        can_comment = is_django_user or has_sheet_identity
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

    return redirect(reverse("project", kwargs={"id": project_obj.pk}))


# --------------------
# GOOGLE SHEET AUTH HELPERS
# --------------------
def get_users_sheet():
    """
    Return the Google Sheet worksheet for users.
    """
    if getattr(settings, "GOOGLE_CREDS_DICT", None):
        gc = gspread.service_account_from_dict(settings.GOOGLE_CREDS_DICT)
    else:
        gc = gspread.service_account(filename=settings.GOOGLE_SERVICE_ACCOUNT_FILE)

    sh = gc.open_by_key(settings.GOOGLE_SHEET_ID)
    ws = sh.worksheet("user")
    return ws


@require_POST
def auth_register(request):
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "").strip()
    username = request.POST.get("username", "").strip()

    if not email or not password:
        return JsonResponse(
            {"success": False, "error": "All fields required."}, status=400
        )

    if not username:
        username = email.split("@")[0]

    try:
        ws = get_users_sheet()
        records = ws.get_all_records(expected_headers=USER_SHEET_HEADERS)
    except Exception:
        logger.exception("auth_register: sheet read failure")
        return JsonResponse(
            {
                "success": False,
                "error": "Registration is temporarily unavailable. Please try again later.",
            },
            status=503,
        )

    for row in records:
        if row.get("Email", "").strip().lower() == email:
            return JsonResponse(
                {"success": False, "error": "Email already registered."}, status=400
            )

    hashed_password = make_password(password)
    now = timezone.localtime(timezone.now())
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    new_row = [username, email, now_str, hashed_password]

    try:
        ws.append_row(new_row)
    except Exception:
        logger.exception("auth_register: sheet write failure")
        return JsonResponse(
            {"success": False, "error": "Registration failed. Please try again later."},
            status=503,
        )

    request.session["user_email"] = email
    request.session["user_name"] = username

    return JsonResponse({"success": True, "username": username})


# Simple in-memory rate limiting for login attempts
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60  # 15 min


def auth_login(request):
    """
    Handles both AJAX (modal) and normal HTML login.
    Includes simple IP-based rate limiting to reduce brute-force attempts.
    """
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    # Rate limit key per IP (good enough for learning project)
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"login_attempts:{ip}"
    attempts = cache.get(key, 0)

    if attempts >= MAX_ATTEMPTS:
        if is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Too many login attempts. Try again later.",
                },
                status=429,
            )
        return HttpResponseTooManyRequests("Too many login attempts. Try again later.")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": "Email and password are required."},
                    status=400,
                )
            messages.error(request, "Email and password are required.")
            return render(request, "auth_login.html", {"email": email})

        try:
            ws = get_users_sheet()
            records = ws.get_all_records(expected_headers=USER_SHEET_HEADERS)
        except Exception:
            logger.exception("auth_login: sheet read failure")
            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": "Login is temporarily unavailable."},
                    status=503,
                )
            messages.error(request, "Login is temporarily unavailable.")
            return render(request, "auth_login.html", {"email": email})

        matched = None
        for row in records:
            row_email = row.get("Email", "").strip().lower()
            raw_value = row.get(PASSWORD_HEADER, "")
            row_pass = str(raw_value or "").strip()

            if row_email == email and row_pass and check_password(password, row_pass):
                matched = row
                break

        if not matched:
            # increment attempts on failure
            cache.set(key, attempts + 1, timeout=LOCKOUT_SECONDS)

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": "Invalid credentials."}, status=401
                )
            messages.error(request, "Invalid credentials.")
            return render(request, "auth_login.html", {"email": email})

        # success: reset attempts
        cache.delete(key)

        request.session["user_email"] = matched.get("Email")
        username = matched.get("User Name") or matched.get("Username") or "Guest"
        request.session["user_name"] = username

        if is_ajax:
            messages.success(request, f"Signed in as {username}.")
            return JsonResponse({"success": True, "username": username})

        messages.success(request, f"Signed in as {username}.")

        next_url = (
            request.POST.get("next")
            or request.GET.get("next")
            or request.META.get("HTTP_REFERER")
            or reverse("home")
        )

        if next_url and "comments/partial" in next_url:
            try:
                path = next_url.split("?", 1)[0]
                parts = path.strip("/").split("/")
                idx = parts.index("project")
                project_id = int(parts[idx + 1])
                next_url = reverse("project", kwargs={"id": project_id})
            except Exception:
                next_url = reverse("home")

        return redirect(next_url)

    if is_ajax:
        return JsonResponse({"success": False, "error": "GET not allowed."}, status=405)

    return render(request, "auth_login.html")


@require_POST
def auth_logout(request):
    """
    Clears both sheet-based and Django auth session, then redirects home.
    """
    request.session.pop("user_email", None)
    request.session.pop("user_name", None)
    request.session.pop("author_name", None)

    django_logout(request)

    messages.success(request, "Signed out.")
    return redirect("home")
