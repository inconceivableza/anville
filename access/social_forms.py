# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

# ✨ Apart from access/forms.py: allauth builds its sign-up forms on the sign-up form class there, so importing them
# into that module would import it in a circle.

from allauth.socialaccount.forms import SignupForm
from django import forms
from django.urls import reverse
from django.utils.html import format_html


class GoogleSignupForm(SignupForm):
    """✨ allauth's form finishing a sign-up begun with Google (ticket 77). The address is the one Google gave, shown
    read-only and checked here, so the refusal of an address that already has an account cannot be stepped round by
    sending another, and the username, which is the email, is Google's address too."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["readonly"] = True
        # ✨ The first name is Google's, changeable on the wizard's first page, so the form asks only for the
        # enrolment code, and is shown only where that is asked for (ADR 0021) or the address is refused.
        del self.fields["display_name"]

    def signup(self, request, user):
        # ✨ The adapter has already made the account and named it from Google; the code is not stored.
        pass

    def clean_email(self):
        if self.cleaned_data["email"].lower() != self.initial.get("email", "").lower():
            raise forms.ValidationError("Use the email address your Google account gave.")
        return super().clean_email()

    def validate_unique_email(self, value):
        try:
            return super().validate_unique_email(value)
        except forms.ValidationError:
            # ✨ The refusal's way on (the adapter's "email_taken"), shown just under the address. Set on the bound
            # field the page draws, which took the field's help text before validation began.
            self["email"].help_text = format_html(
                '<a href="{}">Sign in</a> · <a href="{}">Forgot your password?</a>',
                reverse("account_login"),
                reverse("account_reset_password"),
            )
            raise
