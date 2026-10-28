# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ The homepage's "Stay in touch" form (ticket 74, ADR 0023): what a press of "Subscribe" stores and what the form
shows after it."""

from typing import NamedTuple

from django.db import IntegrityError, transaction

from engine.document.contacts import is_email_address
from engine.models import SignUp

# ✨ The version of the form's sentence, in templates/engine/stay_in_touch.html, kept with each sign-up. Raise it
# whenever a change alters what a visitor signs up to (not for a typo).
WORDING_VERSION = 1

# ✨ The field no person sees or fills: a bot that fills every field is turned away by it.
TRAP = "website"

NO_ADDRESS = "Add your email address."
NOT_AN_ADDRESS = "Check your email address."


class StayInTouch(NamedTuple):
    """✨ What the form shows: the thanks in its place, or the form again with its refusal and what was typed."""

    subscribed: bool = False
    refusal: str = ""
    typed: str = ""


def subscribe(posted):
    """✨ Keep the address a press of "Subscribe" sent, with the time and the sentence's version. A repeat address, in
    any case, is thanked the same and stores nothing new, so the form tells nobody who has signed up; so is a press
    that filled the trap, which stores nothing at all. An empty or impossible address is refused, storing nothing."""
    if posted.get(TRAP):
        return StayInTouch(subscribed=True)
    email = (posted.get("email") or "").strip()
    if not email:
        return StayInTouch(refusal=NO_ADDRESS)
    if not is_email_address(email):
        return StayInTouch(refusal=NOT_AN_ADDRESS, typed=email)
    if not SignUp.objects.filter(email__iexact=email).exists():
        try:
            with transaction.atomic():
                SignUp.objects.create(email=email, wording_version=WORDING_VERSION)
        except IntegrityError:
            pass  # ✨ The same address, sent twice at once: the other press kept it.
    return StayInTouch(subscribed=True)
