# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Where the participant and their observers differ most, and how far the observers agree (ADR 0005).

Both rules read their numbers from the pathway document: a gap of `significant_gap` points or more is significant,
and agreement is banded by the range of the observers' percents.
"""

from fractions import Fraction as F

import pytest

from engine.document.aggregation import aggregate
from engine.document.comparison import agreement, largest_gaps
from engine.document.scoring import score
from engine.results import comparison_page
from tests.documents import complete_sort, sort_pathway

# ✨ Apostle's 100 of 199: 50.25%, which rounds to 50.
YOURS = complete_sort(a5={"bucket": "strength", "value": 100}, p1={"bucket": "strength", "value": 99})


def apostle_beside(observers):
    """✨ The comparison's Apostle beside three observers who each sent `observers`: its gap card and its words for how
    others see it."""
    document = sort_pathway()
    page = comparison_page(document, score(document, YOURS), YOURS, aggregate(document, [observers] * 3))
    [card] = [gap for gap in page["gaps"] if gap["label"] == "Apostle"]
    [bar] = [bar for bar in page["frameworks"][0]["bars"] if bar["label"] == "Apostle"]
    return card, bar["seen_by_others"]


@pytest.mark.parametrize(
    "observers, gap, badge, description",
    [
        # ✨ 59 of 108 is 54.63%: 55 against 50 when rounded, a significant 5; 4.38 unrounded, a modest 4.
        ((59, 49), 4, "Others rate higher", "A modest gap."),
        # ✨ 99 of 199 is 49.75%: 50 against 50 when rounded, no gap at all; 0.5 unrounded, 1, the participant higher.
        ((99, 100), 1, "You rate higher", "A modest gap."),
    ],
    ids=["significant when rounded, modest unrounded", "none when rounded, the participant's unrounded"],
)
def test_a_gap_is_sized_and_directed_by_the_unrounded_shares_not_the_rounded_percents(observers, gap, badge, description):
    sent = complete_sort(
        a5={"bucket": "strength", "value": observers[0]}, p1={"bucket": "strength", "value": observers[1]}
    )

    card, seen = apostle_beside(sent)

    assert (card["gap"], card["badge"], card["description"]) == (gap, badge, description)
    assert seen == "Much the same"


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


def test_the_largest_gaps_are_chosen_and_ordered_by_their_unrounded_size():
    """✨ Rounded first, the gaps would be apostle 10, prophet 9, evangelist 12, shepherd 11, ponder 11 and deliver 10,
    listing deliver fifth and leaving prophet out. Unrounded, prophet's 9.99 passes apostle's 9.95, and deliver's 10.8
    passes ponder's 10.2."""
    pairs = [
        pair("apostle", F("0.45"), F("10.4")),
        pair("prophet", F("0.5"), F("10.49")),
        pair("evangelist", 0, 12),
        pair("shepherd", 0, 11),
        pair("ponder", F("0.4"), F("10.6"), framework="pep"),
        pair("deliver", F("0.6"), F("11.4"), framework="pep"),
    ]

    gaps = largest_gaps(sort_pathway(), pairs)

    assert [(gap["construct"], gap["gap"]) for gap in gaps] == [
        ("evangelist", 12),
        ("shepherd", 11),
        ("deliver", 11),
        ("ponder", 10),
        ("prophet", 10),
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
    "highest, band",
    [((56, 44), "Strong agreement"), ((57, 44), "Some variation")],
    ids=["range exactly 6", "range 6.44, 6 when rounded"],
)
def test_agreement_is_banded_by_the_range_of_the_observers_unrounded_shares(highest, band):
    """✨ Two observers put Apostle at 50; the third at 56 of 100, or 57 of 101, which is 56.44%: 56 when rounded."""
    document = sort_pathway()
    sent = [
        complete_sort(a5={"bucket": "strength", "value": a5}, p1={"bucket": "strength", "value": p1})
        for a5, p1 in [(50, 50), (50, 50), highest]
    ]

    page = comparison_page(document, score(document, YOURS), YOURS, aggregate(document, sent))

    [apostle] = [bar for bar in page["frameworks"][0]["bars"] if bar["label"] == "Apostle"]
    assert apostle["agreement"] == band


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
