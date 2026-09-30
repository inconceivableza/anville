"""✨ What others see in a participant: observers' sorts, each scored on its own, then averaged (ADR 0005).

Over `sort_pathway()`'s two items, a5 (apostle, deliver) and p1 (prophet, ponder), an observer's apostle and
deliver share is a5's value over both values, and their prophet and ponder share is p1's.
"""

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

    # ✨ (90 + 50 + 20) / 3 = 53.3. Pooling the raw values first would give 120 / 220 = 54.5, so 55.
    assert apostle["percent"] == 53


def test_the_mean_is_rounded_once_not_from_each_observers_rounded_percent():
    [apest, _] = aggregate(sort_pathway(), [observer(10, 70), observer(10, 70), observer(12, 88)])["frameworks"]
    apostle = apest["constructs"][0]

    # ✨ Shares of 12.5%, 12.5% and 12% average 12.3, so 12. Their rounded percents (13, 13, 12) would give 13.
    assert apostle["percent"] == 12
    assert apostle["per_observer"] == [12, 13, 13]


def test_each_observers_value_is_kept_but_never_in_the_order_they_answered():
    [apest, _] = aggregate(sort_pathway(), THREE_OBSERVERS)["frameworks"]
    apostle = apest["constructs"][0]

    assert apostle["per_observer"] == [20, 50, 90]


def test_both_frameworks_are_given_with_their_constructs_in_declaration_order():
    assert aggregate(sort_pathway(), THREE_OBSERVERS) == {
        "observers": 3,
        "frameworks": [
            {
                "framework": "apest",
                "constructs": [
                    {"construct": "apostle", "percent": 53, "per_observer": [20, 50, 90]},
                    {"construct": "prophet", "percent": 47, "per_observer": [10, 50, 80]},
                ],
            },
            {
                # ✨ Ranked, deliver (53) would come before ponder (47).
                "framework": "pep",
                "constructs": [
                    {"construct": "ponder", "percent": 47, "per_observer": [10, 50, 80]},
                    {"construct": "deliver", "percent": 53, "per_observer": [20, 50, 90]},
                ],
            },
        ],
    }
