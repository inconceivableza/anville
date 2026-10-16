# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A contact list's people, each added or changed on their own: a first name and an email address apiece.

The people are other than the participant, so each is held to these rules before being kept. Saving one person at a
time, never the whole list, means a page left open can only ever change the person it saves (ticket 51a). Nothing here
touches the database or a request.
"""

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from engine.document.answers import AnswerRefused

# ✨ The most people one list may hold.
MAX_CONTACTS = 50
# ✨ How many of a list's rows are marked as needed, and how many more as optional, when its author does not say: none
# needed, and the prototype's five rows.
DEFAULT_NEEDED = 0
DEFAULT_OPTIONAL = 5
NAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254  # ✨ the longest address mail can carry (RFC 5321), and the column's width

_is_email = EmailValidator()


def contact_from_form(name, email):
    """✨ One person as a form sends them, as {"name", "email"} with space around each trimmed, or AnswerRefused, whose
    `field` names the entry at fault."""
    name, email = (name or "").strip(), (email or "").strip()
    if not name or not email:
        raise AnswerRefused("Add both a name and an email address.", field="email" if name else "name")
    if len(name) > NAME_MAX_LENGTH:
        raise AnswerRefused("The name is too long.", field="name")
    if not is_email_address(email):
        raise AnswerRefused("Check the email address.", field="email")
    return {"name": name, "email": email}


# ✨ Why a person cannot be added to a list already holding the most it may.
LIST_FULL = f"Add no more than {MAX_CONTACTS} people."


def needed(block):
    """✨ How many of the list's rows are marked as needed."""
    return block.get("needed", DEFAULT_NEEDED)


def rows_to_fill(block):
    """✨ How many rows the author asks to be filled: those needed, then those optional."""
    return needed(block) + block.get("optional", DEFAULT_OPTIONAL)


def rows_of(block, held):
    """✨ How many rows the list shows while it holds `held` people: the rows to fill, or, once those are all filled,
    one more for the next person, never past the most it may hold."""
    return min(max(rows_to_fill(block), held + 1), MAX_CONTACTS)


def is_email_address(email):
    """✨ Whether mail could be sent to this address: Django's own check, within the longest address mail can carry."""
    if len(email) > EMAIL_MAX_LENGTH:
        return False
    try:
        _is_email(email)
    except ValidationError:
        return False
    return True
