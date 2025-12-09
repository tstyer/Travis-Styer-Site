from django import forms

from .models import Comment


# This will create the comment form for registered users
class CommentForm(forms.ModelForm):
    content = forms.CharField(
        label="",
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Give me suggestions or leave feedback!"}
        ),
    )

    class Meta:
        model = Comment
        fields = ["content"]


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        label="Name",
        widget=forms.TextInput(attrs={"placeholder": "Your name"}),
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Your email"}),
    )
    subject = forms.CharField(
        required=True,
        label="Subject",
        widget=forms.TextInput(attrs={"placeholder": ""}),
    )
    message = forms.CharField(
        required=True,
        label="Message",
        widget=forms.Textarea(attrs={"placeholder": "Ask me anything!"}),
    )

    # extra custom validation example
    def clean_message(self):
        data = self.cleaned_data["message"]
        if len(data.strip()) < 10:
            raise forms.ValidationError(
                "Please enter at least 10 characters so I can respond meaningfully."
            )
        return data
