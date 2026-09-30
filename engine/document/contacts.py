"""✨ A contact list as a form sends it: one first name and one email address per row, in order.

The rows are people other than the participant, so the whole list is held to these rules before any of it is
kept, and a refusal names the row it is about. Nothing here touches the database or a request.
"""

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from engine.document.answers import AnswerRefused

# ✨ The most people one list may hold, and so the most rows a page will show.
MAX_CONTACTS = 50
# ✨ How many empty rows a list opens with when its author does not say: the prototype's five.
DEFAULT_ROWS = 5
NAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254  # ✨ the longest address mail can carry (RFC 5321), and the column's width

_is_email = EmailValidator()


def contacts_from_form(names, emails, ids):
    """✨ The people a submitted list names, as [{"name", "email", "id", "row"}] in the order written, or
    AnswerRefused.

    `id` is the contact id the row sent back ("" for a row not saved before), taken as given: whether it is the
    participant's own is for whoever keeps the list to check. `row` is the row's number on the form, from 1.
    A row left empty is dropped, and space around each entry is trimmed. The list is refused whole, so a slip
    in one row never keeps the others half-changed.
    """
    rows = [(name.strip(), email.strip(), sent_id) for name, email, sent_id in _padded(names, emails, ids)]
    contacts = []
    for number, (name, email, sent_id) in enumerate(rows, start=1):
        if not name and not email:
            continue
        if not name or not email:
            missing = "email" if name else "name"
            raise AnswerRefused(f"Add both a name and an email address in row {number}.", number, missing)
        if len(name) > NAME_MAX_LENGTH:
            raise AnswerRefused(f"The name in row {number} is too long.", number, "name")
        if not is_email_address(email):
            raise AnswerRefused(f"Check the email address in row {number}.", number, "email")
        contacts.append({"name": name, "email": email, "id": sent_id, "row": number})
    if len(contacts) > MAX_CONTACTS:
        raise AnswerRefused(f"Add no more than {MAX_CONTACTS} people.")
    return contacts


def rows_to_show(block, contacts, asked=0):
    """✨ How many rows the list shows: its authored number, every saved person, or as many as were asked for by
    "add another" without JavaScript, whichever is most, and never more than the list may hold."""
    return min(max(block.get("min_rows", DEFAULT_ROWS), len(contacts), asked), MAX_CONTACTS)


def rows_as_typed(names, emails, ids):
    """✨ Every row of a submitted list as it was typed, empty ones included, as [{"name", "email", "id"}]: what a
    refused list shows again, so nothing typed is lost."""
    return [{"name": name, "email": email, "id": sent_id} for name, email, sent_id in _padded(names, emails, ids)]


def rows_posted(names, emails):
    """✨ How many rows a submitted list had, empty ones included."""
    return max(len(names), len(emails))


def contact_id_per_row(people, saved_ids, rows):
    """✨ Each row's contact id once `people` (as `contacts_from_form` read them) are saved as `saved_ids`, in the
    same order: "" for a row left empty, over all `rows` the form had."""
    by_row = {person["row"]: saved_id for person, saved_id in zip(people, saved_ids, strict=True)}
    return [by_row.get(row, "") for row in range(1, rows + 1)]


def _padded(names, emails, ids):
    # ✨ A form always sends every field of a row; one that did not is treated as leaving it empty. Contact ids
    # past the last row are ignored.
    length = rows_posted(names, emails)
    return zip(*([*fields[:length], *[""] * (length - len(fields))] for fields in (names, emails, ids)))


def is_email_address(email):
    """✨ Whether mail could be sent to this address: Django's own check, within the longest address mail can carry."""
    if len(email) > EMAIL_MAX_LENGTH:
        return False
    try:
        _is_email(email)
    except ValidationError:
        return False
    return True
