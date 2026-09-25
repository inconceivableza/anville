from allauth.account.forms import LoginForm
from django import forms
from django.conf import settings

from access.enrolment import is_valid_enrolment_code


class SignInForm(LoginForm):
    """✨ allauth's sign-in form, with "Remember me" in sentence case like the rest of Anville's wording, and
    read as a statement beside its box, so without a colon."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "remember" in self.fields:  # ✨ allauth drops it when ACCOUNT_SESSION_REMEMBER is set
            self.fields["remember"].label = "Remember me"
            self.fields["remember"].label_suffix = ""


class EnrolmentCodeSignupForm(forms.Form):
    # ✨ allauth puts added fields straight after the email; the age confirmation belongs just above the button.
    # A field left off this list would land after it, so a new one must be listed here.
    field_order = ["email", "enrolment_code", "password1", "password2", "is_adult"]

    enrolment_code = forms.CharField(
        label="Enrolment code",
        error_messages={"required": "Enter the enrolment code you were given."},
    )
    # ✨ Adults only (ADR 0004). A threshold, so it is asked as one: no date of birth, and nothing kept.
    is_adult = forms.BooleanField(
        label="I am 18 or over",
        label_suffix="",  # ✨ a statement beside its box, not a heading above a field, so no colon
        error_messages={"required": "You need to be 18 or over to take part."},
    )

    def clean_enrolment_code(self):
        submitted = self.cleaned_data["enrolment_code"]
        if not is_valid_enrolment_code(submitted, configured=settings.ANVILLE_ENROLMENT_CODE):
            raise forms.ValidationError("That enrolment code is not recognised.")
        return submitted

    def signup(self, request, user):
        # ✨ Required by allauth's ACCOUNT_SIGNUP_FORM_CLASS contract. Nothing to save: the enrolment
        # code grants access only, and the age confirmation admits an adult; neither is stored.
        pass
