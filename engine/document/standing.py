"""✨ Where a construct's share stands, in words: its band by how far it sits from an even share of its framework
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
    it, kept in whole numbers so a share exactly on a band's edge is in it.
    """
    of_even = percent * constructs
    settings = document.get("presentation", {}).get("standing", DEFAULT_STANDING)
    for band in sorted(settings["bands"], key=lambda band: band["at_least"], reverse=True):
        if of_even >= band["at_least"]:
            return band["label"]
    return settings["below"]
