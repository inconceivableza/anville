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
from engine.hub import COMPLETE, LABELS, LOCKED, NOT_STARTED

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


def rows_of(block, held, asked=0):
    """✨ How many rows the list shows while it holds `held` people: the rows to fill, or a row for each person once
    there are more, or the `asked` rows once "Add another person" has asked for more than either, never past the most
    it may hold. Filling every row adds none: "Add another person" does, below them (ticket 70)."""
    return min(max(rows_to_fill(block), held, asked), MAX_CONTACTS)


def can_add_row(shown):
    """✨ Whether "Add another person" is offered below `shown` rows: until the list shows the most it may hold."""
    return shown < MAX_CONTACTS


def voices_card(block, card, invited, answered, minimum, frozen=False):
    """✨ The side card holding a contact list, as the Five trusted voices card shows it (ticket 51a): a tag, a line under
    it or None, and its meters, how many people have a working link (`invited`) and how many observer assessments have
    been sent (`answered`), each out of the rows the list asks to be filled. Engine wording, as the section statuses
    are, and never anyone's name.

    The tag reads the card's section (`card`, as the hub sees it) first: locked, it says so. While answer collection is
    `frozen`, it is complete and says no more answers are added (ticket 55). While fewer of the `needed` people than
    that have a working link, it says how many more are needed, unless the section is not started, when it says so;
    once complete it asks again after a removal, while the card stays complete (ticket 81, in place of ticket 51a's
    "Complete"), and says when the comparison shows only while fewer than `minimum` have answered. Then it follows the
    answers: links issued with none sent, some sent while fewer than `minimum`, then all of them once everyone with a
    working link has sent, or else enough (fix-2)."""
    tag, line = _voices_tag(card, needed(block), invited, answered, minimum, frozen)
    return {
        "tag": tag,
        # ✨ The pill's colours follow the tag's meaning, not the section's status (fix-12): "waiting" for a count of
        # people still needed, grey like "Locked"; None leaves them following the section's status.
        "tone": "waiting" if not frozen and card.status not in (LOCKED, NOT_STARTED) and more_needed(
            needed(block), invited) else None,
        "line": line,
        # ✨ How many more people need a working link, as the tag says it, or None once enough have; the results page
        # says it beside "Invite people who know you →" (ticket 88), whatever the tag says meanwhile.
        "more_needed": more_needed(needed(block), invited),
        "invited": invited,
        "answered": answered,
        "out_of": max(rows_to_fill(block), invited, answered, 1),
    }


def _voices_tag(card, needed, invited, answered, minimum, frozen):
    if not card.is_locked and frozen:
        return LABELS[COMPLETE], "You've seen your results, so no more answers are added."
    if card.status in (LOCKED, NOT_STARTED):
        return card.label, None
    if invited < needed:
        line = f"You'll see how others see you once {minimum} people have answered." if answered < minimum else None
        return more_needed(needed, invited), line
    if answered == 0:
        return "Links issued", None
    if answered < minimum:
        return "Some answers received", None
    if answered == invited:
        return "All answers received", None
    return "Enough answers received", None


def more_needed(needed, invited):
    """✨ How many more of the `needed` people need a working link, in words ("2 more needed", ticket 81), or None once
    `invited` is enough."""
    return f"{needed - invited} more needed" if invited < needed else None


def is_email_address(email):
    """✨ Whether mail could be sent to this address: Django's own check, within the longest address mail can carry."""
    if len(email) > EMAIL_MAX_LENGTH:
        return False
    try:
        _is_email(email)
    except ValidationError:
        return False
    return True
