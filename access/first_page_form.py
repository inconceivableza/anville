# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

# ✨ Apart from access/forms.py, which allauth loads as its sign-up form class: the engine's views import this one, and
# importing that module from them would import it in a circle.

from django import forms

from access.models import DISPLAY_NAME_MAX_LENGTH


class FirstPageForm(forms.Form):
    """✨ The wizard's first page (ADR 0021): the first name, changeable, "I am 18 or over" and the consent tick, each
    required. Adults only (ADR 0004): a threshold, so it is asked as one, with no date of birth. The consent text's
    version is checked by the view, as the consent page checks it."""

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
