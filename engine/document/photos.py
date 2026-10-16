# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A pathway's photos: files beside the document, each named by a section, with its credit (ticket 49b).

A credit is one of three kinds: required by the photo's licence, a courtesy its licence does not ask for, or marked
by the author as needing none (public domain, or the author's own).
"""

REQUIRED = "required"
COURTESY = "courtesy"  # ✨ and "none", which lists nothing; the schema holds the three


def credits_listed(document):
    """✨ The credits the credits page lists, in the document's order: every required one, and the courtesy ones while
    the document's setting is on. The setting can never hide a required credit, and a photo needing none lists
    nothing."""
    listed = {REQUIRED, COURTESY} if document.get("show_courtesy_credits", False) else {REQUIRED}
    return [
        photo["credit"]["text"] for photo in document.get("photos", {}).values() if photo["credit"]["kind"] in listed
    ]
