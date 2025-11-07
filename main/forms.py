from django import forms
from .models import Comment

# This will create the comment form for registered users
class CommentForm(forms.ModelForm):
    content = forms.CharField(
        label="",
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Give me suggestions or leave feedback!"
        }),
    )
    class Meta:
        model = Comment
        fields = ["content"]
