# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ The homepage's "Stay in touch" form (ticket 74, ADR 0023): what a press of its button stores and what the form
shows after it. Since ticket 111 (ADR 0027) it asks what the visitor wants: their church on the waitlist, news by
email, or to be contacted, at least one."""

from typing import NamedTuple

from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Lower

from engine.document.contacts import is_email_address
from engine.models import SignUp, SignUpChoice

# ✨ The version of the form's wording, in templates/engine/stay_in_touch.html, kept with each sign-up and each choice.
# Raise it whenever a change alters what a visitor signs up to (not for a typo). Version 1 was the one sentence with no
# choices (ticket 74); version 2 asks for at least one of the three (ticket 111).
WORDING_VERSION = 2

# ✨ The field no person sees or fills: a bot that fills every field is turned away by it.
TRAP = "website"

# ✨ The query a link to the form names a choice by, to open it with that one ticked and the address ready to type in:
# "Join the waitlist" and "Contact us" (ticket 111; the address since sprint-3d-r1-fix-4), with or without JavaScript.
OPENS_WITH = "stay"

NO_ADDRESS = "Add your email address."
NOT_AN_ADDRESS = "Check your email address."
NO_CHOICE = "Tick what you’d like."


class StayInTouch(NamedTuple):
    """✨ What the form shows: the thanks in its place, for what was ticked, or the form again with each refusal, what
    was typed and what was ticked. `focus_email` is for a form a link opened with a choice, whose address takes the
    focus; a plain visit leaves it where it was, and so does a refusal, beside the button that was pressed."""

    subscribed: bool = False
    address_refusal: str = ""
    choice_refusal: str = ""
    typed: str = ""
    chosen: tuple = ()
    focus_email: bool = False

    @property
    def refused(self):
        return bool(self.address_refusal or self.choice_refusal)


def _chosen(values):
    """✨ The choices among `values` that are one of the three, in the form's order; anything else is dropped."""
    return tuple(choice for choice in SignUpChoice.Choice.values if choice in values)


def opened_with(query):
    """✨ The form as a link opens it: with the choice the link names ticked, nothing refused, and, when a choice was
    named, the address ready to type in. A visit that names none, or none of the three, is a plain one."""
    chosen = _chosen(query.getlist(OPENS_WITH))
    return StayInTouch(chosen=chosen, focus_email=bool(chosen))


def subscribe(posted):
    """✨ Keep the address a press sent, with each choice ticked, the time and the wording's version. A repeat
    address, in any case, adds the choices it had not made, each with its own time and version, and never loses one;
    it is thanked as a new one is, so the form tells nobody who has signed up. So is a press that filled the trap,
    which stores nothing at all. An empty or impossible address, or a press with none of the three ticked, is refused,
    storing nothing, and each refusal says what is missing."""
    chosen = _chosen(posted.getlist("choice"))
    if posted.get(TRAP):
        return StayInTouch(subscribed=True, chosen=chosen)
    email = (posted.get("email") or "").strip()
    refused = StayInTouch(
        address_refusal=NO_ADDRESS if not email else "" if is_email_address(email) else NOT_AN_ADDRESS,
        choice_refusal="" if chosen else NO_CHOICE,
        typed=email,
        chosen=chosen,
    )
    if refused.refused:
        return refused
    with transaction.atomic():
        # ✨ ON CONFLICT DO NOTHING: an address kept already, perhaps by a press sent at the same moment, stays as it
        # was left; and so does a choice it made already, with its first time and version.
        SignUp.objects.bulk_create([SignUp(email=email, wording_version=WORDING_VERSION)], ignore_conflicts=True)
        sign_up = SignUp.objects.alias(address=Lower("email")).get(address=Lower(Value(email)))
        SignUpChoice.objects.bulk_create(
            [SignUpChoice(sign_up=sign_up, choice=choice, wording_version=WORDING_VERSION) for choice in chosen],
            ignore_conflicts=True,
        )
    return StayInTouch(subscribed=True, chosen=chosen)
