from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),

    # Project detail (uses existing view name 'project')
    path("project/<int:id>/", views.project, name="project"),

    # partial comments for modal on home page
    path("project/<int:id>/comments/partial/", views.project_comments_partial, name="project_comments_partial"),

    # CRUD for comments
    path("project/<int:id>/comments/create/", views.comment_create, name="comment_create"),
    path("project/<int:id>/comments/<int:comment_id>/update/", views.comment_update, name="comment_update"),
    path("project/<int:id>/comments/<int:comment_id>/delete/", views.comment_delete, name="comment_delete"),

    # For user log-in
    path("auth/login/", views.auth_login, name="auth_login"),
    path("auth/register/", views.auth_register, name="auth_register"),
]
