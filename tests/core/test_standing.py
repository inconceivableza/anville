# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Where a construct's share stands, in words: its band by how far it sits from an even share of its framework.

The bands are the pathway document's `presentation.standing`, each from a percent of an even share, read highest first
whatever order they are written in; below them all a share takes the label for below (ticket 38).
"""

import pytest

from engine.document.standing import standing
from tests.documents import sort_pathway

# ✨ With five constructs an even share is 20, so a share of 25 is exactly 125% of it and 17 exactly 85%.
FIVE = 5


@pytest.mark.parametrize(
    "percent, label",
    [(25, "Out front"), (24, "Well used"), (21, "Well used"), (20, "In the mix"), (17, "In the mix"), (16, "Quiet")],
    ids=["125% of even", "120%", "105%", "100%", "85%", "80%"],
)
def test_a_share_takes_the_highest_band_it_reaches_whatever_order_the_bands_are_written_in(percent, label):
    """✨ The lowest band is written first, so reading in the order written would put every share above 85% in it."""
    document = sort_pathway()
    document["presentation"]["standing"] = {
        "bands": [
            {"at_least": 85, "label": "In the mix"},
            {"at_least": 125, "label": "Out front"},
            {"at_least": 105, "label": "Well used"},
        ],
        "below": "Quiet",
    }

    assert standing(document, percent, FIVE) == label


@pytest.mark.parametrize(
    "percent, label",
    [(25, "Leading"), (24, "Strong"), (20, "Present"), (16, "Less used")],
    ids=["125% of even", "120%", "100%", "80%"],
)
def test_a_document_without_bands_takes_the_placeholder_bands(percent, label):
    """✨ Variant F's placeholders, until the content owner gives real ones."""
    document = sort_pathway()
    document["presentation"].pop("standing", None)

    assert standing(document, percent, FIVE) == label
