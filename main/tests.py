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
