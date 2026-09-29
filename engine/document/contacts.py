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


def contacts_from_form(names, emails):
    """✨ The people a submitted list names, as [{"name", "email"}] in the order written, or AnswerRefused.

    A row left empty is dropped, and space around each entry is trimmed. The list is refused whole, so a slip
    in one row never keeps the others half-changed.
    """
    rows = [(name.strip(), email.strip()) for name, email in _padded(names, emails)]
    contacts = []
    for number, (name, email) in enumerate(rows, start=1):
        if not name and not email:
            continue
        if not name or not email:
            missing = "email" if name else "name"
            raise AnswerRefused(f"Add both a name and an email address in row {number}.", number, missing)
        if len(name) > NAME_MAX_LENGTH:
            raise AnswerRefused(f"The name in row {number} is too long.", number, "name")
        if not _looks_like_email(email):
            raise AnswerRefused(f"Check the email address in row {number}.", number, "email")
        contacts.append({"name": name, "email": email})
    if len(contacts) > MAX_CONTACTS:
        raise AnswerRefused(f"Add no more than {MAX_CONTACTS} people.")
    return contacts


def rows_to_show(block, contacts, asked=0):
    """✨ How many rows the list shows: its authored number, every saved person, or as many as were asked for by
    "add another" without JavaScript, whichever is most, and never more than the list may hold."""
    return min(max(block.get("min_rows", DEFAULT_ROWS), len(contacts), asked), MAX_CONTACTS)


def _padded(names, emails):
    # ✨ A form always sends both fields of a row; one that did not is treated as leaving the other empty.
    length = max(len(names), len(emails))
    return zip([*names, *[""] * (length - len(names))], [*emails, *[""] * (length - len(emails))])


def _looks_like_email(email):
    if len(email) > EMAIL_MAX_LENGTH:
        return False
    try:
        _is_email(email)
    except ValidationError:
        return False
    return True
