# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from allauth.account.forms import LoginForm
from allauth.core import context as allauth_context
from django import forms
from django.conf import settings

from access.enrolment import is_valid_enrolment_code
from access.models import DISPLAY_NAME_MAX_LENGTH, Account
from organisations.joining import holds_a_working_join_link


class SignInForm(LoginForm):
    """✨ allauth's sign-in form, with "Remember me" in sentence case like the rest of Anville's wording, and
    read as a statement beside its box, so without a colon."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "remember" in self.fields:  # ✨ allauth drops it when ACCOUNT_SESSION_REMEMBER is set
            self.fields["remember"].label = "Remember me"
            self.fields["remember"].label_suffix = ""


class EnrolmentCodeSignupForm(forms.Form):
    # ✨ allauth puts added fields straight after the email, but the name comes first, as on the prototype's account
    # form. A field left off this list would land after the passwords, so a new one must be listed here. "I am 18 or
    # over" is asked on the wizard's first page instead, after the account is made (ADR 0021).
    field_order = ["display_name", "email", "enrolment_code", "password1", "password2"]

    # ✨ The prototype's wording for the name its account form asks for first. Kept as the display name (ticket 37).
    display_name = forms.CharField(
        label="First name",
        max_length=DISPLAY_NAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Ed", "autocomplete": "off"}),
        error_messages={"required": "Add your first name."},
    )
    enrolment_code = forms.CharField(
        label="Enrolment code",
        error_messages={"required": "Enter the enrolment code you were given."},
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✨ Not asked for at all when turned off from the environment, or while the visitor holds a group's join link,
        # which admits them in its place (organisations-and-groups spec). allauth hands this form no request, so it is
        # read from the one allauth's middleware is handling.
        request = allauth_context.request
        if not settings.ANVILLE_ENROLMENT_REQUIRED or (
            request is not None and holds_a_working_join_link(request.session)
        ):
            del self.fields["enrolment_code"]

    def clean_enrolment_code(self):
        submitted = self.cleaned_data["enrolment_code"]
        if not is_valid_enrolment_code(submitted, configured=settings.ANVILLE_ENROLMENT_CODE):
            raise forms.ValidationError("That enrolment code is not recognised.")
        return submitted

    def signup(self, request, user):
        # ✨ Called by allauth once the user is saved (the ACCOUNT_SIGNUP_FORM_CLASS contract). The enrolment code
        # grants access only, and is not stored. The display name is.
        Account.objects.create(participant=user, display_name=self.cleaned_data["display_name"])
