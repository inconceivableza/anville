# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whatever You Do's cards and buckets, held to the two-round strengths prototype they were taken from.

The cards are read out of the prototype file itself, so a card mistyped in the migration fails here.
"""

import json
import re

from engine.document import text_for
from tests.prototype import APEST, PEP, ROOT

TWO_ROUND = (ROOT / "Prototypes for reference/two-round-strengths-prototype/index.html").read_text(encoding="utf-8")


def whatever_you_do():
    return json.loads((ROOT / "pathways/whatever-you-do.json").read_text(encoding="utf-8"))


def prototype_pairs():
    """✨ The prototype's ITEMS, in its array order: each pair's id, its two tags and its two wordings."""
    found = re.findall(
        r"id: '(\w+)',\s*apest: '(\w)',\s*pep: '(\w+)',\s*a: '((?:[^'\\]|\\.)*)',\s*b: '((?:[^'\\]|\\.)*)'", TWO_ROUND
    )
    return [(pair, [APEST[apest], PEP[pep]], first, second) for pair, apest, pep, first, second in found]


def test_whatever_you_do_has_the_two_round_prototypes_72_cards_word_for_word():
    """✨ In the participant's wording: every first-round card in the prototype's order, then every second-round card,
    each named after its twin with a "b" and naming it."""
    items = whatever_you_do()["instrument"]["items"]
    pairs = prototype_pairs()
    assert len(pairs) == 36
    assert [{**item, "text": text_for(item["text"], "participant")} for item in items] == [
        *({"id": pair, "text": first, "loads": loads} for pair, loads, first, _ in pairs),
        *({"id": f"{pair}b", "text": second, "loads": loads, "twin": pair} for pair, loads, _, second in pairs),
    ]


def test_the_seven_buckets_are_the_prototypes_spread_evenly_from_0_to_100():
    buckets = whatever_you_do()["instrument"]["buckets"]
    assert [
        (bucket["id"], text_for(bucket["label"], "participant"), text_for(bucket["label"], "observer"), bucket["seed"])
        for bucket in buckets
    ] == [
        ("definitely-not-me", "Definitely not me", "Definitely not {name}", 0),
        ("not-me", "Not me", "Not {name}", 17),
        ("not-really-me", "Not really me", "Not really {name}", 33),
        ("in-between", "In between", "In between", 50),
        ("somewhat-me", "Somewhat me", "Somewhat {name}", 67),
        ("good-at-this", "Good at this", "Good at this", 83),
        ("real-strength", "Real strength", "Real strength", 100),
    ]


def test_whatever_you_do_sorts_without_fine_tuning():
    assert whatever_you_do()["sorts_skip_fine_tuning"] is True
