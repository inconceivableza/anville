# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from allauth.core import context as allauth_context
from django import forms
from django.conf import settings

from access.enrolment import asks_for_the_code, is_valid_enrolment_code
from access.models import DISPLAY_NAME_MAX_LENGTH, Account

# ✨ No form of allauth's own is imported here (they are in access/allauth_forms.py): allauth builds them on the sign-up
# form class below, so importing one would import this module in a circle.


class EnrolmentCodeSignupForm(forms.Form):
    # ✨ allauth puts added fields straight after the email, but the name comes first, as on the prototype's account
    # form. A field left off this list would land after the passwords, so a new one must be listed here. "I am 18 or
    # over" is asked on the entry page instead, after the account is made (ADR 0021).
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
        # ✨ Not asked for at all when turned off from the environment, or while the visitor holds a group's join link.
        # allauth hands this form no request, so it is read from the one allauth's middleware is handling.
        if not asks_for_the_code(allauth_context.request):
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


class EntryPageForm(forms.Form):
    """✨ The entry page (ADR 0021): the first name, changeable, "I am 18 or over" and the consent tick, each required.
    Adults only (ADR 0004): a threshold, so it is asked as one, with no date of birth. The consent text's version is
    checked by the view, as the consent page checks it."""

    # ✨ Required by the server alone, so a refusal shows only once Continue is pressed (ticket 83's way), and never by
    # the browser beforehand.
    use_required_attribute = False

    display_name = forms.CharField(
        label="First name",
        max_length=DISPLAY_NAME_MAX_LENGTH,
        error_messages={"required": "Add your first name."},
    )
    is_adult = forms.BooleanField(
        label="I am 18 or over",
        error_messages={"required": "You need to be 18 or over to take part."},
    )
    consents = forms.BooleanField(
        label="I agree to Whatever You Do storing my answers, including anything about my faith, work or health, as "
        "set out in the privacy notice.",
        error_messages={"required": "You need to agree to take part."},
    )
