# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ `seed_tie_break`'s made-up sorts, each detected as its scenario promises on *Whatever You Do* (fix-15)."""

import json

import pytest

from engine.document.scoring import score
from engine.document.tie_break import GENERALIST, TIE_BREAK, tie_break
from engine.tie_break_scenarios import seeding
from tests.prototype import ROOT


def whatever_you_do():
    return json.loads((ROOT / "pathways/whatever-you-do.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "scenario, tied, outcome",
    [
        ("tied-both", {"apest", "pep"}, TIE_BREAK),
        ("separated", {"apest"}, TIE_BREAK),
        ("balanced", {"apest"}, TIE_BREAK),
        ("skipped", {"apest", "pep"}, TIE_BREAK),
        ("mixed", {"apest", "pep"}, TIE_BREAK),
        ("generalist-after-pairs", {"apest"}, TIE_BREAK),
        ("generalist", set(), GENERALIST),
    ],
)
def test_each_scenarios_sort_is_detected_as_it_promises(scenario, tied, outcome):
    document = whatever_you_do()

    detected = tie_break(document, score(document, seeding(document, scenario).sort))

    assert (set(detected["tied"]), detected["outcome"]) == (tied, outcome)
