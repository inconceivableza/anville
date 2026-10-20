# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ What others see in a participant: observers' sorts, each scored on its own, then averaged (ADR 0005).

Over `sort_pathway()`'s two items, a5 (apostle, deliver) and p1 (prophet, ponder), an observer's apostle and
deliver share is a5's value over both values, and their prophet and ponder share is p1's.
"""

from fractions import Fraction

import pytest

from engine.document.aggregation import aggregate
from tests.documents import complete_sort, sort_pathway


def observer(a5, p1):
    """✨ One observer's sort, with the two items' fine-tuned values."""
    return complete_sort(a5={"bucket": "strength", "value": a5}, p1={"bucket": "not-me", "value": p1})


# ✨ Apostle shares of 90%, 50% and 20%, from totals of 100, 20 and 100.
THREE_OBSERVERS = [observer(90, 10), observer(10, 10), observer(20, 80)]


@pytest.mark.parametrize("count", [0, 2])
def test_below_the_minimum_the_aggregate_holds_the_count_and_no_numbers(count):
    assert aggregate(sort_pathway(), THREE_OBSERVERS[:count]) == {"observers": count, "frameworks": None}


def test_the_minimum_is_read_from_the_document():
    document = sort_pathway()
    document["observers"] = {"minimum_observers": 4}

    assert aggregate(document, THREE_OBSERVERS) == {"observers": 3, "frameworks": None}


def test_each_observer_is_scored_on_their_own_before_averaging():
    [apest, _] = aggregate(sort_pathway(), THREE_OBSERVERS)["frameworks"]
    apostle = apest["constructs"][0]

    # ✨ (90 + 50 + 20) / 3 = 53.3. Pooling the raw values first would give 120 / 220 = 54.5.
    assert apostle["share"] == Fraction(160, 3)


def test_each_observers_share_is_kept_unrounded_but_never_in_the_order_they_answered():
    [apest, _] = aggregate(sort_pathway(), [observer(10, 70), observer(12, 88), observer(10, 70)])["frameworks"]
    apostle = apest["constructs"][0]

    # ✨ 12%, 12.5% and 12.5%, never the 12, 13 and 13 they round to (ADR 0018), which nothing shows.
    assert apostle["per_observer_shares"] == [12, Fraction(25, 2), Fraction(25, 2)]
    assert set(apostle) == {"construct", "share", "per_observer_shares"}


def test_both_frameworks_are_given_with_their_constructs_in_declaration_order():
    aggregated = aggregate(sort_pathway(), THREE_OBSERVERS)

    assert aggregated == {
        "observers": 3,
        "frameworks": [
            {
                "framework": "apest",
                "constructs": [
                    {"construct": "apostle", "share": Fraction(160, 3), "per_observer_shares": [20, 50, 90]},
                    {"construct": "prophet", "share": Fraction(140, 3), "per_observer_shares": [10, 50, 80]},
                ],
            },
            {
                # ✨ Ranked, deliver (53.3) would come before ponder (46.7).
                "framework": "pep",
                "constructs": [
                    {"construct": "ponder", "share": Fraction(140, 3), "per_observer_shares": [10, 50, 80]},
                    {"construct": "deliver", "share": Fraction(160, 3), "per_observer_shares": [20, 50, 90]},
                ],
            },
        ],
    }
