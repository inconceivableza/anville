# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ Made-up demos that put a participant on each of the tie-break's ways through (ADR 0018), for `seed_tie_break` and
the demo-only choice of a demo profile.

A demo is two choices made apart (fix-25): a starting profile, what every construct of *Whatever You Do* should add up
to in the sort, and how to answer its "Which is more true of you?" pairs. What the pairs and the results should then
show is worked out from the two, never written for each combination: each way of answering comes out the same on every
tied framework it is given to, and a profile says which frameworks it ties and whether the participant is flat once
they come out level. The sort is built to the profile's totals and worked forward through the real scoring, detection,
pair plan, re-weighting and results page. A combination that does not fit (answers for a profile with no pairs, none
for one with pairs, or answers for frameworks the profile does not tie) is refused with its reason, and one that no
longer holds, such as on a pathway whose bands or threshold changed, stops with an error rather than seeding something
misleading. Nothing here touches the database or a request.
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

# ✨ How a tied framework's pairs are answered, and what its re-weighting then comes out as: always its leader (the same
# one on top), always the one just behind (a new one on top), the leader in the first round and the other in the second
# (the best weight shared), or every pair skipped. Every profile's cluster is two constructs, so one pair a round.
LEADER = "leader"
BEHIND = "behind"
EACH_WAY = "each-way"
SKIP = "skip"
COMES_OUT = {LEADER: SAME_TOP, BEHIND: TOP_CHANGED, EACH_WAY: LEVEL, SKIP: SKIPPED}

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
class Profile:
    """✨ A starting profile: the sort's totals, the frameworks it ties by the pathway's ids (none where it is flat on
    both, a generalist with no pairs), and whether the participant is a generalist once every tied framework comes out
    level."""

    summary: str
    totals: dict
    tied: frozenset = frozenset()
    flat_once_level: bool = False


PROFILES = {
    "tied-apest": Profile(
        "Tied on APEST(d) only: two roles level, PEP clear.", TIED_ON_APEST, frozenset({"apest"})
    ),
    "tied-pep": Profile("Tied on PEP only: two energies level, APEST(d) clear.", TIED_ON_PEP, frozenset({"pep"})),
    "tied-both": Profile(
        "Tied on both frameworks, not flat: pairs on both, alternating.", TIED_ON_BOTH, frozenset({"apest", "pep"})
    ),
    "just-leading": Profile(
        "One role just Leading, another just behind it, the rest Present or Strong.",
        LEADING_BY_A_HAIR,
        frozenset({"apest"}),
        flat_once_level=True,
    ),
    "flat": Profile("Flat on both frameworks: no pairs, the generalist's box straight away.", FLAT_ON_BOTH),
}


@dataclass(frozen=True)
class Answers:
    """✨ How to answer a profile's pairs: one way on every framework it ties (`each`), or a way for each framework by its
    id (`by_framework`), which fits only a profile that ties exactly those."""

    summary: str
    each: str | None = None
    by_framework: dict = field(default_factory=dict)

    def way_for(self, framework):
        return self.each or self.by_framework[framework]


ANSWERS = {
    "leader": Answers("Choose the leader each time: separated, the same one on top.", each=LEADER),
    "behind": Answers("Choose the one behind each time: separated, a new one on top.", each=BEHIND),
    "one-each-way": Answers("One answer each way: genuinely balanced.", each=EACH_WAY),
    "skip": Answers("Skip every pair.", each=SKIP),
    "separate-apest-skip-pep": Answers(
        "APEST(d) separated, choosing the one behind each time; PEP skipped.", by_framework={"apest": BEHIND, "pep": SKIP}
    ),
    "separate-pep-skip-apest": Answers(
        "PEP separated, choosing the one behind each time; APEST(d) skipped.", by_framework={"apest": SKIP, "pep": BEHIND}
    ),
}


class ScenarioDoesNotHold(ValueError):
    """✨ The pathway's sort, scoring or tie-break no longer lets a combination come out as it says."""


class DoesNotFit(ValueError):
    """✨ A profile or answers not known, or answers that do not suit the profile; its message says why."""


def fit(profile, answers=None):
    """✨ Raise DoesNotFit, saying why, unless `profile` names a profile and `answers` (None for none) a way of
    answering that suits it."""
    if profile not in PROFILES:
        raise DoesNotFit(f"There is no starting profile called {profile}.")
    if answers is not None and answers not in ANSWERS:
        raise DoesNotFit(f"There is no way of answering the pairs called {answers}.")
    tied = PROFILES[profile].tied
    if not tied and answers is not None:
        raise DoesNotFit(f"{profile} has no pairs, so it takes no answers.")
    if tied and answers is None:
        raise DoesNotFit(f"{profile} has pairs, so it needs a way of answering them.")
    own = ANSWERS[answers].by_framework if answers else {}
    if own and set(own) != tied:
        fitting = [name for name, other in PROFILES.items() if other.tied == set(own)]
        raise DoesNotFit(f"{answers} fits only {' or '.join(fitting)}.")


def summary(profile, answers=None):
    """✨ What a combination is, in a line: the profile's summary and the answers'."""
    return " ".join([PROFILES[profile].summary, *([ANSWERS[answers].summary] if answers else [])])


@dataclass(frozen=True)
class Seeding:
    """✨ What a combination seeds and promises: the sort and its result, each pair with the construct to choose (None to
    skip), and the results page the participant should then see."""

    sort: dict
    scores: dict
    questions: list
    shown: dict


def seeding(document, profile, answers=None):
    """✨ The profile `profile` answered as `answers` says, worked forward on `document`; DoesNotFit where the two do
    not suit each other, or ScenarioDoesNotHold where any step comes out otherwise than they promise."""
    fit(profile, answers)
    return _answered(document, profile, _sorted(document, profile), answers)


def holding(document):
    """✨ Every combination that fits and holds on `document`, as `(profile, answers)` in the order PROFILES and ANSWERS
    list them, answers None for a profile with no pairs; none on a pathway the profiles were not made for, such as one
    with no tie-break. Each profile's sort is built once."""
    found = []
    for profile in PROFILES:
        try:
            sorted_ = _sorted(document, profile)
        except ScenarioDoesNotHold:
            continue
        for answers in [None, *ANSWERS]:
            try:
                fit(profile, answers)
                _answered(document, profile, sorted_, answers)
            except (DoesNotFit, ScenarioDoesNotHold):
                continue
            found.append((profile, answers))
    return found


def _sorted(document, name):
    """✨ The profile's sort, its result and what the tie-break detects in it, `(sort, scores, detected)`, provided it
    ties exactly the frameworks the profile says, two constructs each; otherwise ScenarioDoesNotHold."""
    profile = PROFILES[name]
    sort = sort_with_totals(document, profile.totals)
    scores = score(document, sort)
    detected = tie_break(document, scores)
    expected = TIE_BREAK if profile.tied else GENERALIST
    if detected["outcome"] != expected or set(detected["tied"]) != profile.tied:
        raise ScenarioDoesNotHold(f"{name}: the sort is detected as {detected}, not as the profile needs.")
    if any(len(cluster) != 2 for cluster in detected["tied"].values()):
        raise ScenarioDoesNotHold(f"{name}: each tied framework should have two constructs tied, not {detected}.")
    return sort, scores, detected


def _answered(document, name, sorted_, answers_name):
    """✨ The profile's sort answered as `answers_name` says, checked against what the two promise: each tied framework
    comes out as its way of answering does, and the generalist's box shows for a profile flat on both, or for one flat
    once level whose every tied framework comes out level."""
    profile = PROFILES[name]
    sort, scores, detected = sorted_
    answers = ANSWERS.get(answers_name)
    called = f"{name} with {answers_name}" if answers_name else name
    expected = {framework: COMES_OUT[answers.way_for(framework)] for framework in profile.tied}
    generalist = not profile.tied or (profile.flat_once_level and set(expected.values()) == {LEVEL})

    questions = [
        (pair, _chosen(answers.way_for(pair["framework"]), pair, detected["tied"][pair["framework"]]))
        for pair in pair_plan(document, scores)
    ]
    shown = reweigh(document, scores, [{**pair, "chosen": chosen} for pair, chosen in questions]) if questions else scores
    if outcomes(shown) != expected:
        raise ScenarioDoesNotHold(f"{called}: the answers come out as {outcomes(shown)}, not {expected}.")
    page = results_page(document, shown, sort, "")
    if (page["generalist"] is not None) != generalist:
        raise ScenarioDoesNotHold(f"{called}: the generalist's box would {'not ' * generalist}show.")
    return Seeding(sort=sort, scores=scores, questions=questions, shown=page)


def _chosen(way, pair, cluster):
    """✨ The construct a way of answering chooses in `pair`, or None to skip it."""
    if way == SKIP:
        return None
    if way == EACH_WAY:
        return cluster[pair["round"] % 2]
    return cluster[0] if way == LEADER else cluster[1]


def sort_with_totals(document, totals):
    """✨ A sort whose constructs add up to exactly `totals`, every item at a whole value from 0 to 100 in the bucket
    whose seed is nearest it, as if the slider were moved there.

    Each item loads one construct of each of two frameworks, so the items are the edges between two sets of
    constructs. Every item starts at the value that best fits both its constructs' totals (alternating least squares),
    rounded; what rounding left over is then moved along a spanning tree of the items, leaves first, so every total
    comes out exact."""
    frameworks = [[c["id"] for c in framework["constructs"]] for framework in document["measurement"]["frameworks"]]
    if len(frameworks) != 2 or set(totals) != {c for constructs in frameworks for c in constructs}:
        raise ScenarioDoesNotHold("The profiles are made for two frameworks with Whatever You Do's constructs.")
    if sum(totals[c] for c in frameworks[0]) != sum(totals[c] for c in frameworks[1]):
        raise ScenarioDoesNotHold("A sort's two frameworks always add up to the same total.")
    edges = {}
    for item in document["instrument"]["items"]:
        ends = [next((c for c in item["loads"] if c in constructs), None) for constructs in frameworks]
        if None in ends:
            raise ScenarioDoesNotHold(f"Item {item['id']} does not load onto both frameworks.")
        edges[item["id"]] = tuple(ends)

    best = {construct: 0.0 for construct in totals}
    for _ in range(200):
        for side in (0, 1):
            for construct in frameworks[side]:
                own = [ends for ends in edges.values() if ends[side] == construct]
                best[construct] = (totals[construct] - sum(best[ends[1 - side]] for ends in own)) / len(own)
    values = {item: round(best[a] + best[p]) for item, (a, p) in edges.items()}

    left = dict(totals)
    for item, (a, p) in edges.items():
        left[a] -= values[item]
        left[p] -= values[item]
    for item, construct, towards in _spanning_tree_leaves_first(edges):
        values[item] += left[construct]
        left[towards] -= left[construct]
        left[construct] = 0
    if any(left.values()) or not all(0 <= value <= 100 for value in values.values()):
        raise ScenarioDoesNotHold("No sort of whole values from 0 to 100 adds up to the profile's totals.")

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
