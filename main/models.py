from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True) # So there cannot be duplicate names.

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="projects") # Many-to-many because many projects can have many tags. 
    link = models.URLField(max_length=200, blank=True) # Blank = True (Ok if no link for project).

    def __str__(self):
        return self.title


# Because there's multiple images per project, there's a separate model for the images.
# There can be multiple images per project — use ForeignKey (many-to-one).
class ProjectImage(models.Model):
    # If the project is deleted, then this cascades to delete the image.
    project = models.ForeignKey(Project, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="project_images/")

    def __str__(self):
        return f"{self.project.title} Image"
    

# Added models to satisfy CRUD for comments

class Profile(models.Model):
    """
    Simple viewer profile tied to Django's auth User.
    - Gives a place to store display info for commenters.
    - A Profile can be auto-created on user signup via a post_save signal (optional).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=120, blank=True)  # Optional public name
    joined_at = models.DateTimeField(default=timezone.now)       # Date user/profile created

    def __str__(self):
        # Prefer a friendly name if set, else fall back to the username
        return self.display_name or self.user.get_username()


class Comment(models.Model):
    """
    User comments on a Project.
    - ForeignKey to Project (what the comment is about)
    - ForeignKey to User (who wrote it) – kept, but made optional so session/sheet users can also comment
    - Content text field for the comment body
    - created_at / updated_at for audit & edit history
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="comments")

    # Made nullable/blank so comments coming from the Google Sheet session can be stored.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )

    # For comments created by session/sheet users (not in Django's auth).
    # Stores a display name pulled from Google Sheets or the session.
    author_name = models.CharField(max_length=120, blank=True)

    content = models.TextField()                                  # "Give me suggestions or leave feedback!"
    created_at = models.DateTimeField(default=timezone.now)       # Date Posted
    updated_at = models.DateTimeField(auto_now=True)              # Date Updated (auto on save)

    class Meta:
        ordering = ["-created_at"]  # Newest first

    def __str__(self):
        # Show either the Django user or the sheet/session name
        who = self.user if self.user else (self.author_name or "Anon")
        return f"Comment by {who} on {self.project}"
    

# *Self-learn note:
#     To create a model, need to include models.Model in parens to use a single model for the class. 
#     Then, followed by dot notation, what sub-categories to install? title, textfield, etc.
