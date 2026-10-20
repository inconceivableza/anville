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
