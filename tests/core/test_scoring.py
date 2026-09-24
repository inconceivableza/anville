"""✨ The frozen scoring method, held to the prototype's own output (golden fixtures).

The golden sorts were scored by the prototype's computeAll(), run by `golden/prototype_scoring.mjs`. They are
written in the prototype's terms, and translated to the new identifiers here and nowhere else.
"""

import json
from pathlib import Path

import pytest

from engine.document.scoring import score

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "tests/core/golden/prototype_scoring.json").read_text(encoding="utf-8"))

# ✨ The prototype's stored bucket integers run the other way from strength: 1 is "Real strength".
PROTOTYPE_BUCKETS = {
    1: "real-strength",
    2: "good-at-this",
    3: "average-not-sure",
    4: "not-really-me",
    5: "definitely-not-me",
}

PROTOTYPE_CONSTRUCTS = {
    "A": "apostle",
    "P": "prophet",
    "E": "evangelist",
    "S": "shepherd",
    "T": "teacher",
    "d": "deacon",
    **{name: name for name in ("ponder", "ideate", "assess", "rally", "facilitate", "deliver")},
}


def whatever_you_do():
    return json.loads((ROOT / "pathways/whatever-you-do.json").read_text(encoding="utf-8"))


def sort_answer(golden):
    """✨ A golden sort as the participant's answer: each item's bucket and fine-tuned value."""
    return {item: {"bucket": PROTOTYPE_BUCKETS[bucket], "value": value} for item, (bucket, value) in golden["sort"].items()}


def profile(constructs):
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
            {"framework": "apest", "constructs": profile(golden["prototype"]["apest"])},
            {"framework": "pep", "constructs": profile(golden["prototype"]["pep"])},
        ],
    }


def test_the_score_is_compositional_so_all_strongest_and_all_weakest_give_the_same_profile():
    strongest, weakest = (
        score(whatever_you_do(), sort_answer(golden))
        for golden in GOLDEN
        if golden["name"] in ("all-strongest", "all-weakest")
    )

    def shape(result):
        return [[(c["construct"], c["percent"]) for c in f["constructs"]] for f in result["frameworks"]]

    assert shape(strongest) == shape(weakest)
