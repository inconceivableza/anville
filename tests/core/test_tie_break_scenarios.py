# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ `seed_tie_break`'s starting profiles and ways of answering their pairs, chosen apart (fix-25): every combination
offered holds on *Whatever You Do*, its sort detected as the profile promises, and every other is refused (fix-15)."""

import json
from itertools import product

import pytest

from engine.document.scoring import score
from engine.document.tie_break import GENERALIST, TIE_BREAK, tie_break
from engine.tie_break_scenarios import ANSWERS, PROFILES, DoesNotFit, holding, seeding
from tests.prototype import ROOT


def whatever_you_do():
    return json.loads((ROOT / "pathways/whatever-you-do.json").read_text(encoding="utf-8"))


# ✨ What each profile's sort ties.
TIED = {
    "tied-apest": {"apest"},
    "tied-pep": {"pep"},
    "tied-both": {"apest", "pep"},
    "just-leading": {"apest"},
    "flat": set(),
}
EVERY_WAY = ["leader", "behind", "one-each-way", "skip"]
OFFERED = [
    *[(profile, answers) for profile in ("tied-apest", "tied-pep", "tied-both") for answers in EVERY_WAY],
    ("tied-both", "separate-apest-skip-pep"),
    ("tied-both", "separate-pep-skip-apest"),
    *[("just-leading", answers) for answers in EVERY_WAY],
    ("flat", None),
]
REFUSED = [pair for pair in product(PROFILES, [None, *ANSWERS]) if pair not in OFFERED]


@pytest.mark.parametrize("profile, answers", OFFERED)
def test_each_offered_combination_holds_its_sort_detected_as_the_profile_promises(profile, answers):
    document = whatever_you_do()

    detected = tie_break(document, score(document, seeding(document, profile, answers).sort))

    outcome = TIE_BREAK if TIED[profile] else GENERALIST
    assert (set(detected["tied"]), detected["outcome"]) == (TIED[profile], outcome)


@pytest.mark.parametrize("profile, answers", OFFERED)
def test_each_offered_sort_is_one_a_participant_could_make_by_choosing_buckets_alone(profile, answers):
    """✨ With no fine-tuning, every card is at its bucket's seed."""
    document = whatever_you_do()
    seeds = {bucket["id"]: bucket["seed"] for bucket in document["instrument"]["buckets"]}

    sort = seeding(document, profile, answers).sort

    assert [item for item, placed in sort.items() if placed["value"] != seeds[placed["bucket"]]] == []


@pytest.mark.parametrize("profile, answers", REFUSED)
def test_each_other_combination_is_refused(profile, answers):
    with pytest.raises(DoesNotFit):
        seeding(whatever_you_do(), profile, answers)


def test_exactly_the_combinations_that_hold_are_offered():
    assert holding(whatever_you_do()) == OFFERED
