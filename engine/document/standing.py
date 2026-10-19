# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Where a construct's share stands, in words: its standing, by how far it sits from an even share of its framework
(ticket 38).

The bands are the pathway document's `presentation.standing`, falling back to variant F's placeholders until the content
owner gives real ones. Nothing here touches the database or a request.
"""

# ✨ Variant F's placeholders, each from a percent of an even share, and the label for a share below them all.
DEFAULT_STANDING = {
    "bands": [
        {"at_least": 125, "label": "Leading"},
        {"at_least": 105, "label": "Strong"},
        {"at_least": 85, "label": "Present"},
    ],
    "below": "Less used",
}


def standing(document, percent, constructs):
    """✨ The label of the highest band a share reaches, whatever order the bands are written in, or the label for below.

    An even share is 100 divided among the framework's `constructs`, so a share is `percent × constructs` percent of
    it. A participant's own share is given unrounded (ADR 0018), as an exact fraction where its result allows, and a
    share exactly on a band's edge is in it; an observers' mean is compared just as it is.
    """
    band = _band(document, percent, constructs)
    return band["label"] if band else _settings(document)["below"]


def flat(document, shares):
    """✨ Whether a framework's `shares` are flat (ADR 0018): every one reaches the lowest band and none the highest, as
    "Present" and "Strong" are the in-between bands of *Whatever You Do*."""
    bands = sorted(_settings(document)["bands"], key=lambda band: band["at_least"])
    return all(_band(document, share, len(shares)) not in (None, bands[-1]) for share in shares)


def _band(document, percent, constructs):
    """✨ The highest band a share reaches, or None below them all."""
    of_even = percent * constructs
    for band in sorted(_settings(document)["bands"], key=lambda band: band["at_least"], reverse=True):
        if of_even >= band["at_least"]:
            return band
    return None


def _settings(document):
    return document.get("presentation", {}).get("standing", DEFAULT_STANDING)
