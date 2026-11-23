# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The frozen scoring method, held to the prototype's own output (golden fixtures).

The golden sorts were scored by the prototype's computeAll(), run by `golden/prototype_scoring.mjs`. They are
written in the prototype's terms, and translated to the new identifiers here and nowhere else.
"""

import json
from fractions import Fraction

import pytest

from engine.document.blocks import left_at_seeds
from engine.document.scoring import round_half_up, score
from tests.prototype import APEST, PEP, ROOT, whatever_you_do

GOLDEN = json.loads((ROOT / "tests/core/golden/prototype_scoring.json").read_text(encoding="utf-8"))

# ✨ The prototype's stored bucket integers run the other way from strength: 1 is "Real strength".
PROTOTYPE_BUCKETS = {
    1: "real-strength",
    2: "good-at-this",
    3: "average-not-sure",
    4: "not-really-me",
    5: "definitely-not-me",
}

# ✨ computeAll() names APEST(d) constructs by letter and PEP constructs by the new identifiers' own words.
PROTOTYPE_CONSTRUCTS = {**APEST, **{name: name for name in PEP.values()}}


def sort_answer(golden):
    """✨ A golden sort as the participant's answer: each item's bucket and fine-tuned value."""
    return {item: {"bucket": PROTOTYPE_BUCKETS[bucket], "value": value} for item, (bucket, value) in golden["sort"].items()}


def ranked_constructs(constructs):
    """✨ One framework of the prototype's output, in the shape and identifiers of a stored result."""
    return [
        {"construct": PROTOTYPE_CONSTRUCTS[construct["id"]], "raw": construct["raw"], "percent": construct["pct"]}
        for construct in constructs
    ]


@pytest.mark.parametrize("golden", GOLDEN, ids=lambda golden: golden["name"])
def test_a_sort_scores_exactly_as_the_prototype_scored_it(golden):
    result = score(whatever_you_do(), sort_answer(golden))

    assert result == {
        "method": "compositional_share",
        "frameworks": [
            {"framework": "apest", "constructs": ranked_constructs(golden["prototype"]["apest"])},
            {"framework": "pep", "constructs": ranked_constructs(golden["prototype"]["pep"])},
        ],
    }


def test_an_observers_sort_sent_without_fine_tuning_scores_exactly_as_one_with_the_sliders_left_at_their_seeds():
    """✨ The golden sort's sliders were left at their seeds; sent with no values at all, it scores the same."""
    (golden,) = (golden for golden in GOLDEN if golden["name"] == "sorted-and-left-at-seeds")
    placed_only = {item: {"bucket": placement["bucket"]} for item, placement in sort_answer(golden).items()}

    result = score(whatever_you_do(), left_at_seeds(whatever_you_do(), placed_only))

    assert result == {
        "method": "compositional_share",
        "frameworks": [
            {"framework": "apest", "constructs": ranked_constructs(golden["prototype"]["apest"])},
            {"framework": "pep", "constructs": ranked_constructs(golden["prototype"]["pep"])},
        ],
    }


def test_the_score_is_compositional_so_all_strongest_and_all_weakest_give_the_same_result():
    strongest, weakest = (
        score(whatever_you_do(), sort_answer(golden))
        for golden in GOLDEN
        if golden["name"] in ("all-strongest", "all-weakest")
    )

    def shape(result):
        return [[(c["construct"], c["percent"]) for c in f["constructs"]] for f in result["frameworks"]]

    assert shape(strongest) == shape(weakest)


def test_rounding_half_up_is_exact_for_a_fraction_and_javascripts_for_a_float():
    """✨ A hair under a half, as a fraction, is never rounded up by a float it was turned into; a float rounds as
    Math.round did, the golden sorts holding it to the prototype."""
    hair_under = Fraction(5, 2) - Fraction(1, 10**20)

    assert round_half_up(hair_under) == 2
    assert [round_half_up(number) for number in (2.5, 0.5, 49.75, 50.25)] == [3, 1, 50, 50]


# ✨ "Haven't seen this" (ticket 108): an observer's card placed there is left out of their scores, by a second method.
OF_SEEN = "compositional_share_of_seen"


def scoring_seen(document):
    document["measurement"]["scoring"] = {"method": OF_SEEN}
    return document


@pytest.mark.parametrize("golden", GOLDEN, ids=lambda golden: golden["name"])
def test_a_sort_with_every_card_seen_scores_by_the_seen_cards_method_exactly_as_the_prototype_scored_it(golden):
    """✨ So a participant, who sees every card, is scored as before under either method."""
    result = score(scoring_seen(whatever_you_do()), sort_answer(golden))

    assert result == {
        "method": OF_SEEN,
        "frameworks": [
            {"framework": "apest", "constructs": ranked_constructs(golden["prototype"]["apest"])},
            {"framework": "pep", "constructs": ranked_constructs(golden["prototype"]["pep"])},
        ],
    }


NOT_SEEN = {"seen": False}


def two_rounds():
    """✨ Whatever You Do itself: twelve cards for each construct, seven buckets from 0 to 100."""
    return scoring_seen(json.loads((ROOT / "pathways/whatever-you-do.json").read_text(encoding="utf-8")))


def observers_sort(document, placing):
    """✨ An observer's sort of every card, each placed as `placing(item)` says, at its bucket's seed, or not seen."""
    seeds = {bucket["id"]: bucket["seed"] for bucket in document["instrument"]["buckets"]}
    placed = {item["id"]: placing(item) for item in document["instrument"]["items"]}
    return {
        item: NOT_SEEN if bucket is None else {"bucket": bucket, "value": seeds[bucket]}
        for item, bucket in placed.items()
    }


def apest_shares(result):
    [apest] = [framework for framework in result["frameworks"] if framework["framework"] == "apest"]
    return {construct["construct"]: construct["percent"] for construct in apest["constructs"]}


def test_cards_an_observer_has_not_seen_neither_raise_nor_lower_their_gift():
    """✨ Half of Pioneer's twelve cards unseen and the rest a real strength reads as all twelve a strength would."""
    document = two_rounds()
    pioneer = [item["id"] for item in document["instrument"]["items"] if "apostle" in item["loads"]]

    def all_strong(item):
        return "real-strength" if item["id"] in pioneer else "in-between"

    def half_unseen(item):
        return None if item["id"] in pioneer[:6] else all_strong(item)

    seen_half = score(document, observers_sort(document, half_unseen))
    seen_all = score(document, observers_sort(document, all_strong))

    assert apest_shares(seen_half) == apest_shares(seen_all) == {
        "apostle": 29, "prophet": 14, "evangelist": 14, "shepherd": 14, "teacher": 14, "deacon": 14
    }  # fmt: skip


def test_a_gift_seen_on_fewer_than_four_cards_reads_as_the_observers_cards_do_overall():
    """✨ The two-round prototype's `minSeen`. Pioneer's three cards seen, each a real strength, with every other card
    in between: alone they would make Pioneer 29%; taken at the observer's mean over all 63 cards seen, it is 17%, as
    the other gifts are."""
    document = two_rounds()
    pioneer = [item["id"] for item in document["instrument"]["items"] if "apostle" in item["loads"]]

    def three_seen(item):
        if item["id"] in pioneer:
            return "real-strength" if item["id"] in pioneer[:3] else None
        return "in-between"

    assert apest_shares(score(document, observers_sort(document, three_seen))) == {
        "apostle": 17, "prophet": 17, "evangelist": 17, "shepherd": 17, "teacher": 17, "deacon": 17
    }  # fmt: skip


def test_an_observer_who_saw_nothing_gives_every_construct_an_even_share():
    """✨ As the prototype takes the middle of its scale for a contact who saw nothing: no gift helped or hurt."""
    document = two_rounds()

    result = score(document, observers_sort(document, lambda item: None))

    assert [{construct["percent"] for construct in framework["constructs"]} for framework in result["frameworks"]] == [
        {17},
        {17},
    ]
