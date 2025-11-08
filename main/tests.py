from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Project, Comment

# Create your tests here.


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")

class ViewTests(TestCase): # Creating one test class for all.
    def setUp(self):
        self.project = Project.objects.create(
            title="Test project",
            description="Test description",
        )

    def test_home_page_renders(self):
        """
        Home page should return HTTP 200
        and include test project in the context.
        """
        url = reverse("home")          # uses name="home" from main/urls.py
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

        url = reverse("comment_create", kwargs={"project_id": self.project.id})
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

        url = reverse("comment_create", kwargs={"project_id": self.project.id})
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
        url = reverse("comment_create", kwargs={"project_id": self.project.id})
        response = self.client.post(
            url,
            {"content": "Should not be saved"},
            follow=False,
        )

        # redirect to login; if respond 403/400, change this
        self.assertIn(response.status_code, (302, 403, 400))
        self.assertEqual(Comment.objects.count(), 0)