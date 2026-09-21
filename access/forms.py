from django import forms
from django.conf import settings

from access.enrolment import is_valid_enrolment_code


class EnrolmentCodeSignupForm(forms.Form):
    enrolment_code = forms.CharField(
        label="Enrolment code",
        error_messages={"required": "Enter the enrolment code you were given."},
    )

    def clean_enrolment_code(self):
        submitted = self.cleaned_data["enrolment_code"]
        if not is_valid_enrolment_code(submitted, configured=settings.ANVILLE_ENROLMENT_CODE):
            raise forms.ValidationError("That enrolment code is not recognised.")
        return submitted

    def signup(self, request, user):
        pass
