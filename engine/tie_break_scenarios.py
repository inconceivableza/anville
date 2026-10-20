# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ Made-up sorts that put a participant on each of the tie-break's ways through (ADR 0018), for `seed_tie_break`.

Each scenario names what every construct of *Whatever You Do* should add up to in the sort, the answers to give its
"Which is more true of you?" pairs, and what the results should then show. The sort is built to those totals and then
worked forward through the real scoring, detection, re-weighting and results page; a scenario that no longer holds,
such as on a pathway whose bands or threshold changed, stops with an error rather than seeding something misleading.
Nothing here touches the database or a request.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from engine.document.scoring import score
from engine.document.tie_break import (
    GENERALIST,
    LEVEL,
    SAME_TOP,
    SKIPPED,
    TIE_BREAK,
    TOP_CHANGED,
    outcomes,
    pair_plan,
    reweigh,
    tie_break,
)
from engine.results import results_page

# ✨ How a tied framework's pairs are answered: always its leader, always the one just behind, the leader in the first
# round and the other in the second, or every pair skipped. Every scenario's cluster is two constructs, so one pair.
LEADER = "leader"
CHALLENGER = "challenger"
SPLIT = "split"
SKIP = "skip"

# ✨ Each sort's totals are out of 1800 on each framework, 36 items at an average of 50, so a construct's share is its
# total ÷ 18: 375 is 20.83%, the edge of "Leading", 315 is 17.5%, of "Strong", and 255 is 14.17%, of "Present".
TIED_ON_BOTH = {
    # ✨ Deacon 22.0% and Evangelist 21.2% tied; Teacher "Less used", so not flat.
    "deacon": 396, "evangelist": 382, "prophet": 324, "shepherd": 297, "apostle": 234, "teacher": 167,
    # ✨ Ideate 21.5% and Rally 20.7% tied.
    "ideate": 387, "rally": 373, "ponder": 324, "assess": 288, "facilitate": 240, "deliver": 188,
}  # fmt: skip
TIED_ON_APEST = {
    **TIED_ON_BOTH,
    # ✨ Ideate 24% clearly ahead of Rally 19%.
    "ideate": 432, "rally": 342, "ponder": 320, "assess": 288, "facilitate": 234, "deliver": 184,
}  # fmt: skip
TIED_ON_PEP = {
    **TIED_ON_BOTH,
    # ✨ Deacon 24% clearly ahead of Evangelist 19%.
    "deacon": 432, "evangelist": 342, "prophet": 320, "shepherd": 288, "apostle": 234, "teacher": 184,
}  # fmt: skip
FLAT_PEP = {
    # ✨ Every one "Present" or "Strong", and Assess 19.5% clear of Ponder 17%, so not tied.
    "assess": 351, "ponder": 306, "ideate": 297, "rally": 288, "facilitate": 282, "deliver": 276,
}  # fmt: skip
LEADING_BY_A_HAIR = {
    # ✨ Evangelist 21.1% just "Leading", Shepherd 20.3% just behind and tied with it; shared out evenly, both are 20.7%,
    # "Strong". Every other one "Present".
    "evangelist": 380, "shepherd": 366, "apostle": 268, "prophet": 264, "teacher": 262, "deacon": 260,
    **FLAT_PEP,
}  # fmt: skip
FLAT_ON_BOTH = {
    # ✨ Every one "Present" or "Strong"; Apostle and Prophet are within 5%, but flat on both comes first.
    "apostle": 333, "prophet": 320, "evangelist": 302, "shepherd": 290, "teacher": 282, "deacon": 273,
    **FLAT_PEP,
}  # fmt: skip


@dataclass(frozen=True)
class Scenario:
    """✨ A sort's totals, how each tied framework's pairs are answered, what each comes out as, and whether the
    results then say the participant is a generalist. A framework not in `answers` is not tied."""

    summary: str
    totals: dict
    answers: dict = field(default_factory=dict)
    outcomes: dict = field(default_factory=dict)
    generalist: bool = False


# ✨ Each scenario's variants by the framework `--on` names, keyed by the pathway's own framework ids; one that takes
# no `--on` has a single variant under None. For separated and balanced, `--on` is the one framework tied (the other
# has a clear leader); for mixed, it is the one that comes out Separated while the other is skipped.
DEFAULT_ON = "apest"
SCENARIOS = {
    "tied-both": {
        None: Scenario(
            "Tied on both frameworks, not flat: pairs on both, alternating.",
            TIED_ON_BOTH,
            answers={"apest": LEADER, "pep": LEADER},
            outcomes={"apest": SAME_TOP, "pep": SAME_TOP},
        ),
    },
    "separated": {
        "apest": Scenario(
            "Tied on APEST(d) alone; answering for the one behind makes its top change.",
            TIED_ON_APEST,
            answers={"apest": CHALLENGER},
            outcomes={"apest": TOP_CHANGED},
        ),
        "pep": Scenario(
            "Tied on PEP alone; answering for the one behind makes its top change.",
            TIED_ON_PEP,
            answers={"pep": CHALLENGER},
            outcomes={"pep": TOP_CHANGED},
        ),
    },
    "balanced": {
        "apest": Scenario(
            "Tied on APEST(d) alone; one answer each way leaves the best weight shared.",
            TIED_ON_APEST,
            answers={"apest": SPLIT},
            outcomes={"apest": LEVEL},
        ),
        "pep": Scenario(
            "Tied on PEP alone; one answer each way leaves the best weight shared.",
            TIED_ON_PEP,
            answers={"pep": SPLIT},
            outcomes={"pep": LEVEL},
        ),
    },
    "skipped": {
        None: Scenario(
            "Tied on both frameworks; every pair skipped.",
            TIED_ON_BOTH,
            answers={"apest": SKIP, "pep": SKIP},
            outcomes={"apest": SKIPPED, "pep": SKIPPED},
        ),
    },
    "mixed": {
        "apest": Scenario(
            "Tied on both frameworks; APEST(d) separated, PEP skipped.",
            TIED_ON_BOTH,
            answers={"apest": CHALLENGER, "pep": SKIP},
            outcomes={"apest": TOP_CHANGED, "pep": SKIPPED},
        ),
        "pep": Scenario(
            "Tied on both frameworks; PEP separated, APEST(d) skipped.",
            TIED_ON_BOTH,
            answers={"apest": SKIP, "pep": CHALLENGER},
            outcomes={"apest": SKIPPED, "pep": TOP_CHANGED},
        ),
    },
    "generalist-after-pairs": {
        None: Scenario(
            "One role just Leading, another just behind; balanced answers leave both profiles flat.",
            LEADING_BY_A_HAIR,
            answers={"apest": SPLIT},
            outcomes={"apest": LEVEL},
            generalist=True,
        ),
    },
    "generalist": {
        None: Scenario(
            "Flat on both frameworks from the sort: no pairs, the generalist's box straight away.",
            FLAT_ON_BOTH,
            generalist=True,
        ),
    },
}
TAKES_ON = [name for name, variants in SCENARIOS.items() if None not in variants]


class ScenarioDoesNotHold(ValueError):
    """✨ The pathway's sort, scoring or tie-break no longer lets a scenario come out as it says."""


class NoSuchVariant(ValueError):
    """✨ `--on` given to a scenario that takes none, or naming a framework the scenario has no variant for."""


def scenario_for(name, on=None):
    """✨ The scenario `name`'s variant for `on` (DEFAULT_ON when it takes one and none is given), or NoSuchVariant."""
    variants = SCENARIOS[name]
    if None in variants:
        if on is not None:
            raise NoSuchVariant(f"{name} does not take --on; only {', '.join(TAKES_ON)} do.")
        return variants[None]
    on = on or DEFAULT_ON
    if on not in variants:
        raise NoSuchVariant(f"{name} takes --on {' or '.join(variants)}, not {on}.")
    return variants[on]


@dataclass(frozen=True)
class Seeding:
    """✨ What a scenario seeds and promises: the sort and its result, each pair with the construct to choose (None to
    skip), and the results page the participant should then see."""

    sort: dict
    scores: dict
    questions: list
    shown: dict


def seeding(document, name, on=None):
    """✨ The scenario `name`'s variant for `on` worked forward on `document`; NoSuchVariant where it has none, or
    ScenarioDoesNotHold where any step comes out otherwise than it promises."""
    scenario = scenario_for(name, on)
    sort = sort_with_totals(document, scenario.totals)
    scores = score(document, sort)
    detected = tie_break(document, scores)
    expected = GENERALIST if not scenario.answers else TIE_BREAK
    if detected["outcome"] != expected or set(detected["tied"]) != set(scenario.answers):
        raise ScenarioDoesNotHold(f"{name}: the sort is detected as {detected}, not as the scenario needs.")
    if any(len(cluster) != 2 for cluster in detected["tied"].values()):
        raise ScenarioDoesNotHold(f"{name}: each tied framework should have two constructs tied, not {detected}.")

    questions = [
        (pair, _chosen(scenario.answers[pair["framework"]], pair, detected["tied"][pair["framework"]]))
        for pair in pair_plan(document, scores)
    ]
    shown = scores
    if questions:
        answers = [{**pair, "chosen": chosen} for pair, chosen in questions]
        shown = reweigh(document, scores, answers)
        if outcomes(shown) != scenario.outcomes:
            raise ScenarioDoesNotHold(f"{name}: the answers come out as {outcomes(shown)}, not {scenario.outcomes}.")
    page = results_page(document, shown, sort, "")
    if (page["generalist"] is not None) != scenario.generalist:
        raise ScenarioDoesNotHold(f"{name}: the generalist's box would {'not ' * scenario.generalist}show.")
    return Seeding(sort=sort, scores=scores, questions=questions, shown=page)


def _chosen(answer, pair, cluster):
    """✨ The construct a scenario's answer chooses in `pair`, or None to skip it."""
    if answer == SKIP:
        return None
    if answer == SPLIT:
        return cluster[pair["round"] % 2]
    return cluster[0] if answer == LEADER else cluster[1]


def sort_with_totals(document, totals):
    """✨ A sort whose constructs add up to exactly `totals`, every item at a whole value from 0 to 100 in the bucket
    whose seed is nearest it, as if the slider were moved there.

    Each item loads one construct of each of two frameworks, so the items are the edges between two sets of
    constructs. Every item starts at the value that best fits both its constructs' totals (alternating least squares),
    rounded; what rounding left over is then moved along a spanning tree of the items, leaves first, so every total
    comes out exact."""
    frameworks = [[c["id"] for c in framework["constructs"]] for framework in document["measurement"]["frameworks"]]
    if len(frameworks) != 2 or set(totals) != {c for constructs in frameworks for c in constructs}:
        raise ScenarioDoesNotHold("The scenarios are made for two frameworks with Whatever You Do's constructs.")
    if sum(totals[c] for c in frameworks[0]) != sum(totals[c] for c in frameworks[1]):
        raise ScenarioDoesNotHold("A sort's two frameworks always add up to the same total.")
    edges = {}
    for item in document["instrument"]["items"]:
        ends = [next((c for c in item["loads"] if c in constructs), None) for constructs in frameworks]
        if None in ends:
            raise ScenarioDoesNotHold(f"Item {item['id']} does not load onto both frameworks.")
        edges[item["id"]] = tuple(ends)

    fit = {construct: 0.0 for construct in totals}
    for _ in range(200):
        for side in (0, 1):
            for construct in frameworks[side]:
                own = [ends for ends in edges.values() if ends[side] == construct]
                fit[construct] = (totals[construct] - sum(fit[ends[1 - side]] for ends in own)) / len(own)
    values = {item: round(fit[a] + fit[p]) for item, (a, p) in edges.items()}

    left = dict(totals)
    for item, (a, p) in edges.items():
        left[a] -= values[item]
        left[p] -= values[item]
    for item, construct, towards in _spanning_tree_leaves_first(edges):
        values[item] += left[construct]
        left[towards] -= left[construct]
        left[construct] = 0
    if any(left.values()) or not all(0 <= value <= 100 for value in values.values()):
        raise ScenarioDoesNotHold("No sort of whole values from 0 to 100 adds up to the scenario's totals.")

    buckets = document["instrument"]["buckets"]
    return {
        item: {"bucket": min(buckets, key=lambda bucket: abs(bucket["seed"] - value))["id"], "value": value}
        for item, value in values.items()
    }


def _spanning_tree_leaves_first(edges):
    """✨ `(item, construct, towards)` for each item of a spanning tree over the constructs, from the leaves in: the
    item joins `construct` to `towards`, the next construct on the way to the tree's root."""
    neighbours = defaultdict(list)
    for item, (a, p) in edges.items():
        neighbours[a].append((item, p))
        neighbours[p].append((item, a))
    root = next(iter(neighbours))
    reached, joined = {root}, []
    queue = [root]
    for construct in queue:
        for item, other in neighbours[construct]:
            if other not in reached:
                reached.add(other)
                joined.append((item, other, construct))
                queue.append(other)
    if reached != set(neighbours):
        raise ScenarioDoesNotHold("The items do not join every construct, so the totals cannot all be met.")
    return reversed(joined)
