"""✨ The Whatever You Do instrument, held to the prototype it was migrated from.

The item bank is read out of the prototype file itself, so an item mistyped in the migration fails here.
"""

import re
from collections import Counter

from engine.document import text_for
from tests.prototype import APEST, PEP, PROTOTYPE, js_string, whatever_you_do


def prototype_items():
    """✨ The prototype's giftItems, in its array order, as items of a pathway document."""
    found = re.findall(r"\{id:'(\w+)',label:'((?:[^'\\]|\\.)*)',apest:'(\w)',pep:'(\w+)'\}", PROTOTYPE)
    return [
        {"id": item_id, "text": js_string(label), "loads": [APEST[apest], PEP[pep]]}
        for item_id, label, apest, pep in found
    ]


def test_the_36_items_are_the_prototypes_word_for_word_with_the_same_loadings():
    """✨ In the participant's wording: four items also carry the observer's (ticket 15a)."""
    items = whatever_you_do()["instrument"]["items"]
    assert len(prototype_items()) == 36
    assert [{**item, "text": text_for(item["text"], "participant")} for item in items] == prototype_items()


def test_the_buckets_run_from_weakest_to_strongest_with_the_prototypes_labels_and_seeds():
    buckets = whatever_you_do()["instrument"]["buckets"]
    assert [{**bucket, "label": text_for(bucket["label"], "participant")} for bucket in buckets] == [
        {"id": "definitely-not-me", "label": "Definitely not me", "seed": 10},
        {"id": "not-really-me", "label": "Not really me", "seed": 25},
        {"id": "average-not-sure", "label": "Average / not sure", "seed": 45},
        {"id": "good-at-this", "label": "Good at this", "seed": 65},
        {"id": "real-strength", "label": "Real strength", "seed": 85},
    ]


def test_the_unbalanced_item_matrix_is_ported_unchanged():
    """✨ Content debt, kept on purpose: Shepherd and deacon items never earn Ponder, Teacher items never earn
    Rally. Fixing it changes every participant's results, so it is the content owner's call and a new method."""
    items = whatever_you_do()["instrument"]["items"]
    matrix = Counter(tuple(item["loads"]) for item in items)
    rows = {
        "apostle": [1, 1, 1, 1, 1, 1],
        "prophet": [2, 1, 1, 1, 1, 0],
        "evangelist": [1, 1, 1, 2, 1, 0],
        "shepherd": [0, 1, 1, 1, 1, 2],
        "teacher": [2, 1, 1, 0, 1, 1],
        "deacon": [0, 1, 1, 1, 1, 2],
    }
    assert {
        apest: [matrix[apest, pep] for pep in PEP.values()] for apest in APEST.values()
    } == rows
