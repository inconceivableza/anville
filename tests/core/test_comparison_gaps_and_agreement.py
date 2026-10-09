# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Where the participant and their observers differ most, and how far the observers agree (ADR 0005).

Both rules read their numbers from the pathway document: a gap of `significant_gap` points or more is significant,
and agreement is banded by the range of the observers' percents.
"""

import pytest

from engine.document.comparison import agreement, largest_gaps
from tests.documents import sort_pathway


def pair(construct, you, others, framework="apest"):
    """✨ One construct's self-result percent beside the observers' mean."""
    return {"framework": framework, "construct": construct, "you": you, "others": others}


def test_the_five_largest_gaps_across_both_frameworks_come_largest_first_ties_in_declared_order():
    pairs = [
        pair("apostle", 20, 30),
        pair("prophet", 25, 10),
        pair("evangelist", 15, 16),
        pair("shepherd", 10, 22),
        pair("ponder", 30, 18, framework="pep"),
        pair("deliver", 10, 20, framework="pep"),
    ]

    gaps = largest_gaps(sort_pathway(), pairs)

    assert [(gap["construct"], gap["gap"], gap["direction"]) for gap in gaps] == [
        ("prophet", 15, "you_higher"),
        ("shepherd", 12, "others_higher"),
        ("ponder", 12, "you_higher"),
        ("apostle", 10, "others_higher"),
        ("deliver", 10, "others_higher"),
    ]


@pytest.mark.parametrize(
    "threshold, gap, significant",
    [(8, 8, True), (8, 7, False), (None, 5, True), (None, 4, False)],
    ids=["at the document's", "one below the document's", "at the default five", "one below the default five"],
)
def test_a_gap_is_significant_from_the_documents_threshold_or_five(threshold, gap, significant):
    document = sort_pathway()
    del document["presentation"]["comparison"]
    if threshold is not None:
        document["presentation"]["comparison"] = {"significant_gap": threshold}

    [shown] = largest_gaps(document, [pair("apostle", 20, 20 + gap)])

    assert shown["significant"] is significant


@pytest.mark.parametrize(
    "per_observer, band",
    [
        ([10, 13, 16], "Strong agreement"),
        ([10, 17], "Some variation"),
        ([10, 12, 24], "Some variation"),
        ([10, 25], "Divided views"),
    ],
    ids=["range 6", "range 7", "range 14", "range 15"],
)
def test_agreement_is_banded_by_the_range_of_the_observers_percents(per_observer, band):
    assert agreement(sort_pathway(), per_observer) == band


@pytest.mark.parametrize(
    "per_observer, band",
    [([10, 14], "Strong agreement"), ([10, 40], "Divided views")],
    ids=["range 4", "range 30"],
)
def test_bands_are_read_narrowest_first_whatever_order_they_are_written_in(per_observer, band):
    """✨ The widest band is written first, so reading in the order written would put range 4 in "Some variation".
    Range 30 is above every band, and takes the label for above."""
    document = sort_pathway()
    document["presentation"]["comparison"]["agreement"] = {
        "bands": [{"up_to": 14, "label": "Some variation"}, {"up_to": 6, "label": "Strong agreement"}],
        "above": "Divided views",
    }

    assert agreement(document, per_observer) == band
