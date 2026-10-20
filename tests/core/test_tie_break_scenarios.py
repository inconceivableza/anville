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
    "scenario, on, tied, outcome",
    [
        ("tied-both", None, {"apest", "pep"}, TIE_BREAK),
        ("separated", None, {"apest"}, TIE_BREAK),
        ("separated", "pep", {"pep"}, TIE_BREAK),
        ("balanced", None, {"apest"}, TIE_BREAK),
        ("balanced", "pep", {"pep"}, TIE_BREAK),
        ("skipped", None, {"apest", "pep"}, TIE_BREAK),
        ("mixed", None, {"apest", "pep"}, TIE_BREAK),
        ("mixed", "pep", {"apest", "pep"}, TIE_BREAK),
        ("generalist-after-pairs", None, {"apest"}, TIE_BREAK),
        ("generalist", None, set(), GENERALIST),
    ],
)
def test_each_scenarios_sort_is_detected_as_it_promises(scenario, on, tied, outcome):
    document = whatever_you_do()

    detected = tie_break(document, score(document, seeding(document, scenario, on).sort))

    assert (set(detected["tied"]), detected["outcome"]) == (tied, outcome)
