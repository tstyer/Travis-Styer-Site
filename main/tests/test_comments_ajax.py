from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main.models import Comment, Project

User = get_user_model()


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
