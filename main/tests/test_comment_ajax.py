from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main.models import Comment, Project

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
