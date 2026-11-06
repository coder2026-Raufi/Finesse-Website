from django import forms

from .models import Inquiry

LANGS = [("en", "en"), ("fa", "fa"), ("ps", "ps"), ("ar", "ar")]


class ContactForm(forms.Form):
    """Server-side validation. Limits match the HTML form, because the browser
    checks can always be bypassed - the server must never trust them."""

    name = forms.CharField(min_length=2, max_length=40)
    email = forms.EmailField(max_length=60)
    subject = forms.ChoiceField(choices=Inquiry.Subject.choices)
    message = forms.CharField(min_length=10, max_length=5000)
    language = forms.ChoiceField(choices=LANGS, required=False)
    # Honeypot: invisible to people, bots fill it in.
    website = forms.CharField(required=False, max_length=200)

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())  # collapse spaces/newlines
        if len(name) < 2:
            raise forms.ValidationError("too short", code="min_length")
        return name

    def clean_message(self):
        msg = self.cleaned_data["message"].strip()
        if len(msg) < 10:
            raise forms.ValidationError("too short", code="min_length")
        return msg

    def clean_language(self):
        return self.cleaned_data.get("language") or "en"
