import re

from django import forms

from .models import Inquiry

PHONE_RE = re.compile(r"^\+?[0-9()\-\s]{7,20}$")


class InquiryForm(forms.ModelForm):
    # Honeypot: real visitors never see or fill this field, bots usually do.
    website = forms.CharField(
        required=False,
        label="Leave this field empty",
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )
    consent = forms.BooleanField(
        required=True,
        error_messages={"required": "Please confirm so we can store your brief and contact you."},
    )

    class Meta:
        model = Inquiry
        fields = [
            "name", "email", "phone", "company", "industry", "service", "project_type",
            "requirements", "budget", "timeline", "description",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your full name", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@company.com", "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": "+91 98765 43210 (optional)", "autocomplete": "tel", "inputmode": "tel"}),
            "company": forms.TextInput(attrs={"placeholder": "Company or organisation (optional)", "autocomplete": "organization"}),
            "industry": forms.TextInput(attrs={"placeholder": "e.g. Retail, Healthcare, Education (optional)", "list": "industryList"}),
            "service": forms.RadioSelect(),
            "project_type": forms.TextInput(attrs={"placeholder": "e.g. New website, support chatbot (optional)"}),
            "requirements": forms.Textarea(attrs={"rows": 4, "placeholder": "Answer the prompt shown above (optional)"}),
            "description": forms.Textarea(attrs={"rows": 5, "maxlength": 2000, "placeholder": "Tell us what you want to achieve, who it is for and any key context."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].choices = Inquiry.SERVICE_CHOICES  # no blank option
        self.fields["service"].error_messages["required"] = "Please choose the closest area of expertise."
        self.fields["budget"].choices = [("", "Select a range (optional)")] + Inquiry.BUDGET_CHOICES
        self.fields["timeline"].choices = [("", "Select a timeline (optional)")] + Inquiry.TIMELINE_CHOICES
        self.fields["name"].error_messages["required"] = "Please tell us your name."
        self.fields["email"].error_messages["required"] = "We need an email address to reply to you."
        self.fields["description"].error_messages["required"] = "Please describe your project."

    def clean_name(self):
        value = self.cleaned_data["name"].strip()
        if len(value) < 2:
            raise forms.ValidationError("Please enter your full name.")
        return value

    def clean_phone(self):
        value = self.cleaned_data.get("phone", "").strip()
        if value and not PHONE_RE.match(value):
            raise forms.ValidationError("Enter a valid phone number, for example +91 98765 43210.")
        return value

    def clean_description(self):
        value = self.cleaned_data["description"].strip()
        if len(value) < 20:
            raise forms.ValidationError("Please write at least 20 characters so the team can understand your project.")
        if len(value) > 2000:
            raise forms.ValidationError("Please keep the overview under 2000 characters.")
        return value

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""


class TrackForm(forms.Form):
    reference = forms.CharField(max_length=12)
    email = forms.EmailField()

    def clean_reference(self):
        return self.cleaned_data["reference"].strip().upper()
