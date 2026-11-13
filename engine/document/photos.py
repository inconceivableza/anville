# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A pathway's photos: files beside the document, each named by a section, with its credit (ticket 49b).

A credit is one of three kinds: required by the photo's licence, a courtesy its licence does not ask for, or marked
by the author as needing none (public domain, or the author's own).

A credit is a `Credit`, whether the document gives it or the engine's own lists of the site's photos do
(sprint-3d-r1-fix-5), so the credits page lists and draws each by the same rules.
"""

from typing import NamedTuple

REQUIRED = "required"
COURTESY = "courtesy"  # ✨ and "none", which lists nothing; the schema holds the three


class CreditPart(NamedTuple):
    """✨ A part of a credit, its title, author, source or licence: its `name` as shown, and the address it links to,
    or None."""

    name: str
    url: str | None = None


class Credit(NamedTuple):
    """✨ A photo's or video's credit, of its `kind`, `REQUIRED` or `COURTESY`. With an `author`, the credits page draws
    it from its parts, as a Creative Commons licence asks: its `description` (what it shows, in our words) or its own
    `title`, by its author, on its `source`, under its `licence`, each a `CreditPart`. Without an author, it is its
    `text`, as written."""

    kind: str
    text: str | None = None
    description: str | None = None
    title: CreditPart | None = None
    author: CreditPart | None = None
    source: CreditPart | None = None
    licence: CreditPart | None = None

    @classmethod
    def of(cls, credit):
        """✨ The `Credit` a document's photo's `credit` gives."""
        named = ("title", "author", "source", "licence")
        parts = {part: CreditPart(**credit[part]) for part in named if part in credit}
        return cls(credit["kind"], text=credit.get("text"), description=credit.get("description"), **parts)


UNSPLASH_LICENSE = CreditPart("Unsplash License", "https://unsplash.com/license")
PEXELS_LICENSE = CreditPart("Pexels License", "https://www.pexels.com/license/")


def on_unsplash(description, author, profile, page):
    """✨ The credit of a photo on Unsplash, a courtesy, as its licence asks for none: what it shows, by `author` (their
    `profile`), on Unsplash at `page`."""
    return Credit(
        COURTESY,
        description=description,
        author=CreditPart(author, profile),
        source=CreditPart("Unsplash", page),
        licence=UNSPLASH_LICENSE,
    )


def on_pexels(description, author, profile, page):
    """✨ The credit of a photo or video on Pexels, as `on_unsplash`."""
    return Credit(
        COURTESY,
        description=description,
        author=CreditPart(author, profile),
        source=CreditPart("Pexels", page),
        licence=PEXELS_LICENSE,
    )


def listed(credits, courtesy_shown):
    """✨ The credits of these the credits page lists, in their order: every required one, and the courtesy ones while
    `courtesy_shown`, the document's setting. The setting can never hide a required credit, wherever it is given."""
    return [credit for credit in credits if credit.kind == REQUIRED or (courtesy_shown and credit.kind == COURTESY)]


def credits_listed(document):
    """✨ The `Credit`s of the document's photos the credits page lists, in the document's order, by `listed`, under
    its own setting. A photo needing none lists nothing."""
    credits = [Credit.of(photo["credit"]) for photo in document.get("photos", {}).values()]
    return listed(credits, document.get("show_courtesy_credits", False))
