# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ What the pathway document says about observers: inviting them, and how many must answer (ADR 0005).

Nothing here touches the database or a request.
"""

import re
from datetime import timedelta

from engine.document.answers import AnswerRefused
from engine.document.text import text_for

# ✨ Long enough for a ten-to-fifteen-minute task someone may take a while to get to (ADR 0005).
DEFAULT_LINK_LIFETIME_DAYS = 30

# ✨ Fewer would come too close to exposing one observer's answers. The schema lets a document raise it, never lower it.
DEFAULT_MINIMUM_OBSERVERS = 3

# ✨ A stand-in for a document that has written no notice of its own, plainly marked as one so it is never mistaken for
# the real thing. It still says the few things an observer must hear before any question (ADR 0005), and never
# "completely anonymous".
DEFAULT_PRIVACY_NOTICE = (
    "[Draft notice: this pathway has not written its own privacy notice yet.]"
    "\n\n"
    "{name} has asked you to answer some questions about them. Your answers are kept, and your name is never shown "
    "to {name} with them. Once {name} has looked at the combined results, no new answers are added. You can withdraw "
    "at any time, and your answers will be removed: through this link while it works, and after that by asking the "
    "people who run the service. If you haven't answered, we'll email you a reminder once a week until your link runs "
    "out, and every reminder lets you stop them."
)

# ✨ The engine's stand-in for a document that has written no reminder email, marked as a draft as the notice is. It still
# says where the observer's details came from, what they are used for, how often and until when (ticket 43a).
DEFAULT_REMINDER = {
    "subject": "A reminder from {name}",
    "body": (
        "[Draft email: this pathway has not written its own reminder yet.]"
        "\n\n"
        "Hi {observer}, {name} asked you to answer some questions about them. Please answer through the link {name} "
        "sent you, or with the button below. Your link works until {until}."
        "\n\n"
        "{name} gave us your name and email address; we use them only to remind you, once a week until you answer or "
        "your link runs out."
    ),
    "stop": "Don't want these reminders? Stop reminders about {name}",
    # ✨ The button that gives the observer a fresh link, and the link beside it to the same page (ticket 43b).
    "answer": "Answer for {name} →",
    "details": "How we handle your details",
}


def link_lifetime(document):
    """✨ How long an observer's link works once issued: the document's `link_lifetime_days`, or 30 days."""
    days = document.get("observers", {}).get("link_lifetime_days", DEFAULT_LINK_LIFETIME_DAYS)
    return timedelta(days=days)


def minimum_observers(document):
    """✨ How many observers must answer before any number from their answers is shown: the document's, or three."""
    return document.get("observers", {}).get("minimum_observers", DEFAULT_MINIMUM_OBSERVERS)


def privacy_notice(document, name):
    """✨ The notice an observer reads before any question, in the observer's wording, naming the participant.

    `{name}` is replaced as plain text, never through `format()`, as in the results title. The engine's draft stands
    in for a document that has none, so no observer is ever asked anything without one.
    """
    notice = document.get("observers", {}).get("privacy_notice", DEFAULT_PRIVACY_NOTICE)
    return text_for(notice, "observer").replace("{name}", name)


def reminder_email(document, name, observer, until):
    """✨ The reminder email's wording, as {"subject", "body", "stop", "answer", "details"}, in the observer's wording, naming the participant
    as {name}, the observer as {observer} and the day their link stops working as {until} (ticket 43a). Each field the
    document leaves out is the engine's draft's."""
    authored = document.get("observers", {}).get("reminder", {})
    values = {"name": name, "observer": observer, "until": until}
    # ✨ In one pass, so a name that happens to hold "{until}" is left as typed.
    return {
        field: REMINDER_PLACES.sub(lambda place: values[place[1]], text_for(authored.get(field, draft), "observer"))
        for field, draft in DEFAULT_REMINDER.items()
    }


REMINDER_PLACES = re.compile(r"\{(name|observer|until)\}")


def relationship_question(document, name):
    """✨ How the document asks an observer how they know the participant, in the observer's wording naming them, as
    {"question", "choices": [{"id", "label"}]}; None for a document that does not ask (ticket 15b)."""
    asked = document.get("observers", {}).get("relationship")
    if asked is None:
        return None

    def worded(text):
        return text_for(text, "observer").replace("{name}", name)

    choices = [{"id": choice["id"], "label": worded(choice["label"])} for choice in asked["choices"]]
    return {"question": worded(asked["question"]), "choices": choices}


def relationship_from_form(document, posted):
    """✨ The relationship an observer chose, by its id, or None if they chose none. One the document does not offer is
    refused. It is only ever stored, never used to slice or filter results (spec, Observers)."""
    if not posted:
        return None
    offered = {choice["id"] for choice in document.get("observers", {}).get("relationship", {}).get("choices", [])}
    if posted not in offered:
        raise AnswerRefused("That isn't one of the choices offered.")
    return posted
