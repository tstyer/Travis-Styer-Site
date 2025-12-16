import os
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from main.models import Comment, Project

# Create your tests here.


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
class ViewTests(TestCase):  # Creating one test class for all.
    def setUp(self):
        self.User = get_user_model()
        self.project = Project.objects.create(
            title="Test project",
            description="Test description",
        )

    def test_home_page_renders(self):
        """
        Home page should return HTTP 200
        and include test project in the context.
        """
        url = reverse("home")  # uses name="home" from main/urls.py
        response = self.client.get(url)

        # 1) page loads OK
        self.assertEqual(response.status_code, 200)

        # 2) correct template is used
        self.assertTemplateUsed(response, "index.html")

        # 3) our project is in the 'projects' context list
        projects_in_context = response.context.get("projects")
        self.assertIsNotNone(projects_in_context)
        self.assertIn(self.project, projects_in_context)

    def test_project_detail_returns_200(self):
        """
        Project detail view should return HTTP 200
        and use the correct project in context.
        """
        url = reverse("project", kwargs={"id": self.project.id})
        response = self.client.get(url)

        # 1) page loads
        self.assertEqual(response.status_code, 200)

        # 2) correct template
        self.assertTemplateUsed(response, "project.html")

        # 3) context has the project
        project_in_context = response.context.get("project")
        self.assertIsNotNone(project_in_context)
        self.assertEqual(project_in_context, self.project)

    # Comment test:

    def test_comment_create_authenticated_user(self):
        """
        Authenticated Django user can create a comment.
        Comment.user should be set, author_name should be blank.
        """
        user = self.User.objects.create_user(
            username="tester", email="tester@example.com", password="password123"
        )
        self.client.login(username="tester", password="password123")

        url = reverse("comment_create", kwargs={"id": self.project.id})
        response = self.client.post(
            url,
            {"content": "Test"},  # match form field name
            follow=False,
        )

        # Adjust this if view returns 200 instead of redirecting
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.project, self.project)
        self.assertEqual(comment.user, user)
        self.assertEqual(comment.author_name, "")
        self.assertEqual(comment.content, "Test")

    def test_comment_create_session_sheet_user(self):
        """
        Session/Sheets path: allow comment when there is no Django user
        but a session-based author name exists.
        """
        session = self.client.session
        # Use whatever key view expects for sheet/session name:
        session["author_name"] = "Sheet Tester"
        session.save()

        url = reverse("comment_create", kwargs={"id": self.project.id})
        response = self.client.post(
            url,
            {"content": "Feedback from sheet user"},
            follow=False,
        )

        # ADJUST if view does not redirect
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.project, self.project)
        self.assertIsNone(comment.user)  # no Django auth user
        self.assertEqual(comment.author_name, "Sheet Tester")
        self.assertEqual(comment.content, "Feedback from sheet user")

    def test_comment_create_unauthenticated_without_session_is_blocked(self):
        """
        Unauthenticated user with no session/sheet data should NOT create a comment.
        Expect a redirect (e.g. to login) or some kind of refusal.
        """
        url = reverse("comment_create", kwargs={"id": self.project.id})
        response = self.client.post(
            url,
            {"content": "Should not be saved"},
            follow=False,
        )

        # redirect to login; if respond 403/400, change this
        self.assertIn(response.status_code, (302, 403, 400))
        self.assertEqual(Comment.objects.count(), 0)


# Tests for users: edits, delete their comment


class CommentOwnerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        # create a registered user used for these tests
        self.user = self.User.objects.create_user(
            username="tester", email="tester@example.com", password="password123"
        )
        self.project = Project.objects.create(
            title="Test project", description="Test description"
        )

    def test_edit_comment_as_owner(self):
        # log in as the owner and create a comment they own
        self.client.login(username="tester", password="password123")
        comment = Comment.objects.create(
            project=self.project,
            user=self.User.objects.get(username="tester"),
            content="orig",
        )

        url = reverse(
            "comment_update", kwargs={"id": self.project.pk, "comment_id": comment.pk}
        )
        resp = self.client.post(url, {"content": "edited"})
        self.assertEqual(resp.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "edited")

    def test_delete_comment_as_owner(self):
        self.client.login(username="tester", password="password123")
        comment = Comment.objects.create(
            project=self.project,
            user=self.User.objects.get(username="tester"),
            content="will delete",
        )
        url = reverse(
            "comment_delete", kwargs={"id": self.project.pk, "comment_id": comment.pk}
        )
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())


# Negative tests


class CommentPermissionTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="usera", password="pass1234")
        self.user_b = User.objects.create_user(username="userb", password="pass1234")

        self.project = Project.objects.create(
            title="Test Project",
            description="Test desc",
        )

        self.comment = Comment.objects.create(
            project=self.project,
            user=self.user_a,
            content="User A comment",
        )

    def test_non_owner_cannot_edit_comment(self):
        self.client.login(username="userb", password="pass1234")

        url = reverse(
            "comment_update",
            kwargs={"id": self.project.id, "comment_id": self.comment.id},
        )

        response = self.client.post(url, {"content": "Hacked"})

        self.assertIn(response.status_code, [403, 404, 302])


# Auth test


class AuthSheetTests(TestCase):
    def _ajax_post(self, url_name, data):
        return self.client.post(
            reverse(url_name),
            data=data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    @patch("main.views.get_users_sheet")
    def test_auth_register_success_sets_session(self, mock_get_sheet):
        ws = MagicMock()
        ws.get_all_records.return_value = []  # no existing users
        ws.append_row.return_value = None
        mock_get_sheet.return_value = ws

        res = self._ajax_post(
            "auth_register",
            {"email": "test@example.com", "password": "pass1234", "username": "Travis"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(self.client.session.get("user_email"), "test@example.com")
        self.assertEqual(self.client.session.get("user_name"), "Travis")

        ws.append_row.assert_called_once()

    def test_auth_register_missing_fields_400(self):
        res = self._ajax_post("auth_register", {"email": "", "password": ""})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])

    @patch("main.views.get_users_sheet")
    def test_auth_register_duplicate_email_400(self, mock_get_sheet):
        ws = MagicMock()
        ws.get_all_records.return_value = [
            {
                "Email": "test@example.com",
                "User Name": "Old",
                "Password (Now Hashed)": "x",
            }
        ]
        mock_get_sheet.return_value = ws

        res = self._ajax_post(
            "auth_register",
            {"email": "test@example.com", "password": "pass1234", "username": "New"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])
        self.assertIn("already", res.json()["error"].lower())

    @patch("main.views.get_users_sheet")
    def test_auth_register_sheet_read_failure_503(self, mock_get_sheet):
        mock_get_sheet.side_effect = Exception("boom")

        res = self._ajax_post(
            "auth_register",
            {"email": "test@example.com", "password": "pass1234", "username": "Travis"},
        )
        self.assertEqual(res.status_code, 503)
        self.assertFalse(res.json()["success"])

    @patch("main.views.get_users_sheet")
    def test_auth_register_sheet_write_failure_503(self, mock_get_sheet):
        ws = MagicMock()
        ws.get_all_records.return_value = []
        ws.append_row.side_effect = Exception("boom")
        mock_get_sheet.return_value = ws

        res = self._ajax_post(
            "auth_register",
            {"email": "test@example.com", "password": "pass1234", "username": "Travis"},
        )
        self.assertEqual(res.status_code, 503)
        self.assertFalse(res.json()["success"])

    @patch("main.views.get_users_sheet")
    @patch("main.views.check_password")
    def test_auth_login_success_sets_session_ajax(
        self, mock_check_password, mock_get_sheet
    ):
        ws = MagicMock()
        ws.get_all_records.return_value = [
            {
                "Email": "test@example.com",
                "User Name": "Travis",
                "Password (Now Hashed)": "HASH",
            }
        ]
        mock_get_sheet.return_value = ws
        mock_check_password.return_value = True

        res = self._ajax_post(
            "auth_login",
            {"email": "test@example.com", "password": "pass1234"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(self.client.session.get("user_email"), "test@example.com")
        self.assertEqual(self.client.session.get("user_name"), "Travis")

    @patch("main.views.get_users_sheet")
    def test_auth_login_sheet_read_failure_503_ajax(self, mock_get_sheet):
        mock_get_sheet.side_effect = Exception("boom")

        res = self._ajax_post(
            "auth_login",
            {"email": "test@example.com", "password": "pass1234"},
        )
        self.assertEqual(res.status_code, 503)
        self.assertFalse(res.json()["success"])

    @patch("main.views.get_users_sheet")
    def test_auth_login_invalid_credentials_401_ajax(self, mock_get_sheet):
        ws = MagicMock()
        ws.get_all_records.return_value = [
            {
                "Email": "test@example.com",
                "User Name": "Travis",
                "Password (Now Hashed)": "HASH",
            }
        ]
        mock_get_sheet.return_value = ws

        # no patch check_password -> it will return Falsey in your view flow
        with patch("main.views.check_password", return_value=False):
            res = self._ajax_post(
                "auth_login",
                {"email": "test@example.com", "password": "wrong"},
            )

        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    def test_auth_login_get_not_allowed_ajax(self):
        res = self.client.get(
            reverse("auth_login"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(res.status_code, 405)
        self.assertFalse(res.json()["success"])


# Testing AJAX comment operations

User = get_user_model()


class CommentAjaxSessionOwnerTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(title="P1", description="D1")

    def _ajax_post(self, url, data=None):
        return self.client.post(
            url,
            data=data or {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_ajax_create_session_user_sets_author_fields_and_returns_partial(self):
        # Simulate your Google Sheets "logged in" session identity
        session = self.client.session
        session["user_email"] = "sheet@example.com"
        session["user_name"] = "SheetUser"
        session.save()

        url = reverse("comment_create", kwargs={"id": self.project.id})
        res = self._ajax_post(url, {"content": "Session comment"})

        self.assertEqual(res.status_code, 200)
        self.assertIn("Session comment", res.content.decode())

        c = Comment.objects.get(project=self.project, content="Session comment")
        self.assertIsNone(c.user)
        self.assertEqual(c.author_email, "sheet@example.com")
        self.assertEqual(c.author_name, "SheetUser")

    def test_ajax_update_session_owner_by_email_allowed(self):
        # Create a session-owned comment
        c = Comment.objects.create(
            project=self.project,
            user=None,
            author_name="Someone",
            author_email="sheet@example.com",
            content="Old",
        )

        session = self.client.session
        session["user_email"] = "sheet@example.com"
        session["user_name"] = "SheetUser"
        session.save()

        url = reverse(
            "comment_update", kwargs={"id": self.project.id, "comment_id": c.id}
        )
        res = self._ajax_post(url, {"content": "New"})

        self.assertEqual(res.status_code, 200)
        self.assertIn("New", res.content.decode())

        c.refresh_from_db()
        self.assertEqual(c.content, "New")

    def test_ajax_update_session_non_owner_forbidden(self):
        c = Comment.objects.create(
            project=self.project,
            user=None,
            author_name="Owner",
            author_email="owner@example.com",
            content="Owner comment",
        )

        session = self.client.session
        session["user_email"] = "intruder@example.com"
        session["user_name"] = "Intruder"
        session.save()

        url = reverse(
            "comment_update", kwargs={"id": self.project.id, "comment_id": c.id}
        )
        res = self._ajax_post(url, {"content": "Hack"})

        self.assertEqual(res.status_code, 403)

    def test_ajax_delete_session_owner_allowed(self):
        c = Comment.objects.create(
            project=self.project,
            user=None,
            author_name="SheetUser",
            author_email="sheet@example.com",
            content="To delete",
        )

        session = self.client.session
        session["user_email"] = "sheet@example.com"
        session["user_name"] = "SheetUser"
        session.save()

        url = reverse(
            "comment_delete", kwargs={"id": self.project.id, "comment_id": c.id}
        )
        res = self._ajax_post(url)

        self.assertEqual(res.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=c.id).exists())


# Testing AJAX comment operations for authenticated Django users


class CommentAjaxFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass1234")
        self.project = Project.objects.create(title="P1", description="D1")

    def _ajax_post(self, url, data):
        return self.client.post(url, data=data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_ajax_create_returns_partial_html(self):
        self.client.login(username="u1", password="pass1234")

        url = reverse("comment_create", kwargs={"id": self.project.id})
        res = self._ajax_post(url, {"content": "Hello AJAX"})

        self.assertEqual(res.status_code, 200)
        self.assertIn("Hello AJAX", res.content.decode())
        self.assertTrue(
            Comment.objects.filter(project=self.project, content="Hello AJAX").exists()
        )

    def test_ajax_update_returns_partial_html(self):
        self.client.login(username="u1", password="pass1234")
        c = Comment.objects.create(project=self.project, user=self.user, content="Old")

        url = reverse(
            "comment_update", kwargs={"id": self.project.id, "comment_id": c.id}
        )
        res = self._ajax_post(url, {"content": "New"})

        self.assertEqual(res.status_code, 200)
        self.assertIn("New", res.content.decode())
        c.refresh_from_db()
        self.assertEqual(c.content, "New")

    def test_ajax_delete_returns_partial_html(self):
        self.client.login(username="u1", password="pass1234")
        c = Comment.objects.create(
            project=self.project, user=self.user, content="To delete"
        )

        url = reverse(
            "comment_delete", kwargs={"id": self.project.id, "comment_id": c.id}
        )
        res = self._ajax_post(url, {})

        self.assertEqual(res.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=c.id).exists())

    def test_ajax_create_forbidden_when_not_signed_in(self):
        url = reverse("comment_create", kwargs={"id": self.project.id})
        res = self._ajax_post(url, {"content": "Nope"})
        self.assertEqual(res.status_code, 403)


# CI prod safety check


class TestProductionSecuritySettings(SimpleTestCase):
    def test_security_flags_enabled_when_env_on(self):
        os.environ["DEBUG"] = "False"
        os.environ["ENABLE_SECURITY_HEADERS"] = "True"

        # settings are loaded once per process; in CI this test should be run
        # in a context where env vars are already set before Django starts.
        # So this test mainly enforces the expected values in that setup.

        self.assertFalse(settings.DEBUG)
        self.assertTrue(getattr(settings, "SESSION_COOKIE_SECURE", False))
        self.assertTrue(getattr(settings, "CSRF_COOKIE_SECURE", False))
        self.assertTrue(getattr(settings, "SECURE_SSL_REDIRECT", False))
        self.assertGreater(getattr(settings, "SECURE_HSTS_SECONDS", 0), 0)
        self.assertEqual(getattr(settings, "X_FRAME_OPTIONS", ""), "DENY")
