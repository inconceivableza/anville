# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ What the pathway document says about observers: inviting them, and how many must answer (ADR 0005).

Nothing here touches the database or a request.
"""

from datetime import timedelta

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
    "to {name} with them. You can withdraw while this link works, and your answers will be deleted."
)


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
