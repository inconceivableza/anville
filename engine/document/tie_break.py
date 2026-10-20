# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whether a participant's sort leaves a framework's leaders too close to call (ticket 30a, ADR 0018).

A framework is tied when its leader's unrounded share is at most the document's percentage more than one or more of
its other constructs'; at most the document's cluster size, leader first, enter the tie-break. A participant flat on
every framework is a generalist instead, and is asked nothing. Run on the participant's own result alone, never an
observer's. Nothing here touches the database or a request.
"""

import re
from fractions import Fraction
from itertools import zip_longest

from engine.document.scoring import round_half_up, unrounded_shares
from engine.document.standing import flat

# ✨ ADR 0018's: a leader at most 5% more than another, and the content owner's prototype's at most the top four.
DEFAULT_PERCENT = 5
DEFAULT_CLUSTER = 4
# ✨ The prototype's: at most ten pairs, a guess it asks to be checked against drop-off (ticket 30b).
DEFAULT_BUDGET = 10
# ✨ A framework tied on its own gets a second round of the same pairs, with different statements (ticket 30b).
ROUNDS = 2


TIE_BREAK = "tie_break"
GENERALIST = "generalist"

# ✨ The re-weighting's name, stored on the result it makes (ticket 30c). A second named scoring method beside the
# compositional score (ADR 0003): once a result is made with it, its behaviour is frozen, and a change is a new name.
# The outcome it names was amended to follow the weights alone, and its shares to open only a gap just past the
# threshold (fix-22), both before any real participant's result, so it keeps its name (ADR 0018, amended). Each
# result stores its outcome and shares, so one stored before keeps what it was given. Since fix-26 it also stores the
# constructs each framework tied, which changes no outcome or share, only what the results page can name.
REWEIGHTING = "pairwise_reweighting"
# ✨ How far past the threshold the re-weighting sets one weight's constructs ahead of the next's: a hundredth of a
# percent, so 5.01% for a document's 5%. The test for too close to call counts exactly 5% as tied, so the gap must be
# more than that; a hundredth is past it while adding next to nothing.
JUST_PAST = Fraction(1, 100)

# ✨ What the tie-break's answers did to a tied framework: a new construct leads, the same one leads, or none does,
# because the best weight is shared, the choices having gone in a circle or not, or every pair was skipped (ADR 0018).
TOP_CHANGED = "top_changed"
SAME_TOP = "same_top"
SEPARATED = (TOP_CHANGED, SAME_TOP)
CIRCLE = "circle"
LEVEL = "level"
BALANCED = (CIRCLE, LEVEL)
SKIPPED = "skipped"

# ✨ What the results page's tie-break sentences may name (fix-26), each by a construct's label: the leader after the
# answers (top), the sort's leader among the tied (previous), the closest behind the top after the answers (next), and
# the constructs that entered the tie-break, in the order shown (names). The linter refuses any other.
PLACEHOLDERS = ("top", "previous", "next", "names")


def tie_break(document, result):
    """✨ `{"tied": {framework: [construct, ...]}, "outcome": ...}`: each tied framework's constructs that enter the
    tie-break, leader first by unrounded share, and what follows. Flat on every framework, the participant is a
    generalist (GENERALIST), with nothing tied and nothing asked of them; otherwise, tied on one framework or more,
    they are marked for the tie-break (TIE_BREAK); on neither, there is nothing to break (None). A pathway without a
    tie-break marks no one."""
    settings = document.get("measurement", {}).get("tie_break")
    if settings is None:
        return {"tied": {}, "outcome": None}
    shares = unrounded_shares(result)
    if all(flat(document, list(shares[framework["framework"]].values())) for framework in result["frameworks"]):
        return {"tied": {}, "outcome": GENERALIST}
    within = _within(settings)
    cluster = settings.get("cluster", DEFAULT_CLUSTER)
    tied = {}
    for framework in result["frameworks"]:
        share = shares[framework["framework"]]
        # ✨ Stable, so constructs on the same unrounded share keep the order the result ranked them in.
        ranked = [c["construct"] for c in sorted(framework["constructs"], key=lambda c: -share[c["construct"]])]
        leader = share[ranked[0]]
        close = [construct for construct in ranked if leader <= share[construct] * within] if leader else []
        if len(close) > 1:
            tied[framework["framework"]] = close[:cluster]
    return {"tied": tied, "outcome": TIE_BREAK if tied else None}


def _within(settings):
    """✨ How many times another's share a leader's may be and still be too close to call: 1.05 for 5%."""
    # ✨ As a string first, so a percentage such as 2.5 is taken as written, not as its nearest binary fraction.
    return 1 + Fraction(str(settings.get("percent", DEFAULT_PERCENT))) / 100


def pair_plan(document, result):
    """✨ The "Which is more true of you?" pairs a participant marked for the tie-break answers, in order (ticket 30b), or
    [] for anyone else. Each is `{"framework", "constructs": [a, b], "statements": [a's, b's], "round"}`.

    As the content owner's prototype plans them, and as its notes share the budget (ADR 0018): every pair of each tied
    framework's constructs, never across frameworks, those involving the higher-ranked first (by the sum of the two
    ranks, ties in the order made), then a second round of the same pairs with the next statement of each. With two
    frameworks tied, each round alternates between them, pair by pair. All of it is cut to the document's budget from
    the end, so second rounds go first, then the least important pairs. Construct a shows its statement at the round's
    place and b the one after, so no pair repeats a statement across the two rounds. Worked out afresh from the stored
    result each time; the answers are stored, the plan is not.
    """
    detected = tie_break(document, result)
    if detected["outcome"] != TIE_BREAK:
        return []
    settings = document["measurement"]["tie_break"]
    statements = settings["statements"]
    by_framework = [_by_importance(framework, cluster) for framework, cluster in detected["tied"].items()]
    planned = [
        {
            "framework": framework,
            "constructs": [a, b],
            "statements": [
                statements[a][round_ % len(statements[a])],
                statements[b][(round_ + 1) % len(statements[b])],
            ],
            "round": round_,
        }
        for round_ in range(ROUNDS)
        # ✨ A framework with fewer pairs runs out first, and the other's go on alone.
        for alongside in zip_longest(*by_framework)
        for framework, a, b in filter(None, alongside)
    ]
    return planned[: settings.get("budget", DEFAULT_BUDGET)]


def _by_importance(framework, cluster):
    """✨ Every pair of a tied framework's cluster as `(framework, a, b)`, most important first: by the sum of the two
    constructs' places, ties in the order made."""
    pairs = [(i + j, a, b) for i, a in enumerate(cluster) for j, b in enumerate(cluster) if i < j]
    pairs.sort(key=lambda pair: pair[0])
    return [(framework, a, b) for _, a, b in pairs]


def reweigh(document, result, answers):
    """✨ The result re-weighted by the tie-break's answers (ticket 30c, ADR 0018), as the content owner's prototype's
    `rescore` weighs it, for a participant marked for the tie-break who has answered or skipped every pair. The sort's
    result is left as it is: this is a second result, kept beside it, with `tie_break` listing each framework that had
    pairs, how its answers came out and the constructs that entered its tie-break, leader first as the sort ranked them
    (fix-26), so the results page can name them.

    Each tied framework that had pairs is re-weighted from its own answers alone, so neither framework's answers
    change the other. Each construct that entered its tie-break weighs 1 plus the share of its appearances it won, a
    skip being an appearance for both and a win for neither. The weights decide the order of those constructs, and the
    gap opens only enough to settle it (the developer's call, fix-22, ADR 0018 amended), where the prototype shared
    their total out by weight, so that a lead of under a point could become one of fourteen. Constructs on the same
    weight end level; each weight's constructs end just past the document's percentage ahead of the next weight's
    (JUST_PAST), so they are no longer too close to call; and the unrounded share they had between them is kept. A
    tied construct the gap pushes below one outside the cluster is listed below it, by its unrounded share like any
    other: the answers put it last of the cluster, and keeping the cluster's total means its last falls as its first
    rises.

    Every construct keeps its unrounded share, as an exact fraction written out, beside its whole number: each
    re-weighted share is rounded half up on its own, as the compositional score rounds, where the prototype added what
    rounding lost to the leader, which could make a leader of one. A re-weighted framework is ranked by the unrounded
    shares, which replace its fallback to declaration order; constructs level on them keep the sort's order. Every
    other construct and framework is as the sort scored it.

    The weights decide the outcome: one construct alone on the best weight is separated (TOP_CHANGED or SAME_TOP), even
    where the choices went in a circle. Where the best weight is shared there is no winner to name, so the constructs
    are genuinely balanced: CIRCLE where the choices also went in a circle, some construct beating one that beat one
    that beat it across both rounds, as the prototype checks for, and LEVEL otherwise. Every pair skipped says nothing
    about the participant (SKIPPED), so that framework is left as sorted.
    """
    tied = tie_break(document, result)["tied"]
    apart = _within(document["measurement"]["tie_break"]) + JUST_PAST / 100
    sorted_shares = unrounded_shares(result)
    frameworks, broken = [], []
    for framework in result["frameworks"]:
        framework_id = framework["framework"]
        share = sorted_shares[framework_id]
        constructs = [{**construct, "share": str(share[construct["construct"]])} for construct in framework["constructs"]]
        own_answers = [answer for answer in answers if answer["framework"] == framework_id]
        if framework_id in tied and own_answers:
            outcome, share = _reweighed(tied[framework_id], share, own_answers, apart)
            broken.append({"framework": framework_id, "outcome": outcome, "tied": tied[framework_id]})
            if outcome != SKIPPED:
                constructs = [
                    {**construct, "percent": round_half_up(share[c]), "share": str(share[c])}
                    if (c := construct["construct"]) in tied[framework_id]
                    else construct
                    for construct in constructs
                ]
                # ✨ Stable, so constructs level on their unrounded share keep the order the sort ranked them in.
                constructs.sort(key=lambda construct: -share[construct["construct"]])
        frameworks.append({"framework": framework_id, "constructs": constructs})
    return {"method": REWEIGHTING, "frameworks": frameworks, "tie_break": broken}


def _reweighed(cluster, share, answers, apart):
    """✨ One tied framework's outcome and its shares after its own answers: `(outcome, {construct: share})`, each
    weight's constructs `apart` times the share of the next weight's."""
    if all(answer["chosen"] is None for answer in answers):
        return SKIPPED, share
    wins = {construct: 0 for construct in cluster}
    appearances = {construct: 0 for construct in cluster}
    beaten = {construct: set() for construct in cluster}
    for answer in answers:
        for construct in answer["constructs"]:
            appearances[construct] += 1
        if answer["chosen"] is not None:
            wins[answer["chosen"]] += 1
            [loser] = [construct for construct in answer["constructs"] if construct != answer["chosen"]]
            beaten[answer["chosen"]].add(loser)
    # ✨ Fractions, so weights that are equal compare equal.
    weights = {c: 1 + (Fraction(wins[c], appearances[c]) if appearances[c] else 0) for c in cluster}
    # ✨ The cluster's total in parts: each of the lowest weight's constructs takes one, each of the next weight's
    # `apart` parts, and so on up, one more factor of `apart` for every weight below its own.
    below = {weight: sum(1 for other in set(weights.values()) if other < weight) for weight in weights.values()}
    parts = {c: apart ** below[weights[c]] for c in cluster}
    part = sum(share[c] for c in cluster) / sum(parts.values())
    reweighed = {**share, **{c: part * parts[c] for c in cluster}}

    # ✨ The weights decide (ADR 0018, amended): one construct on the best weight is separated even where the answers
    # went in a circle; only a best weight shared is balanced, worded as a circle where the answers also went in one.
    best = max(weights.values())
    if sum(1 for weight in weights.values() if weight == best) > 1:
        outcome = CIRCLE if _in_a_circle(beaten) else LEVEL
    elif max(cluster, key=lambda c: weights[c]) != cluster[0]:
        outcome = TOP_CHANGED
    else:
        outcome = SAME_TOP
    return outcome, reweighed


def outcomes(result):
    """✨ `{framework: outcome}` for each framework a re-weighted result broke, or {} for any other result. A result
    re-weighted before ticket 59b names its one framework on its own, and is read the same way."""
    broken = result.get("tie_break") or []
    if isinstance(broken, dict):
        broken = [broken]
    return {entry["framework"]: entry["outcome"] for entry in broken}


def named(text, names):
    """✨ `text` with each of the results page's tie-break placeholders (PLACEHOLDERS) replaced by `names[placeholder]`,
    as plain text in one pass, never through `format()`, so a label holding braces is never itself filled in. The
    template escapes whatever comes out."""
    return re.sub(r"\{(\w+)\}", lambda found: names.get(found[1], found[0]), text)


def joined(labels):
    """✨ Labels as a sentence lists them: "A and B", "A, B and C"."""
    return " and ".join(filter(None, [", ".join(labels[:-1]), *labels[-1:]]))


def tied_in(result):
    """✨ `{framework: [construct, ...]}`: the constructs that entered each broken framework's tie-break, leader first as
    the sort ranked them (fix-26). A result re-weighted before fix-26 did not keep them, so names none; its pathway
    version's wording, from before then too, names none either."""
    broken = result.get("tie_break") or []
    if isinstance(broken, dict):
        broken = [broken]
    return {entry["framework"]: entry.get("tied", []) for entry in broken}


def _in_a_circle(beaten):
    """✨ Whether some construct beat one that beat one that beat it, as the prototype's `hasCycle` asks."""
    return any(a in beaten[c] for a in beaten for b in beaten[a] for c in beaten[b])
