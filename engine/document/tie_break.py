# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whether a participant's sort leaves a framework's leaders too close to call (ticket 30a, ADR 0018).

A framework is tied when its leader's unrounded share is at most the document's percentage more than one or more of
its other constructs'; at most the document's cluster size, leader first, enter the tie-break. A participant flat on
every framework is a generalist instead, and is asked nothing. Run on the participant's own result alone, never an
observer's. Nothing here touches the database or a request.
"""

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
REWEIGHTING = "pairwise_reweighting"

# ✨ What the tie-break's answers did to the tied framework: a new construct leads, the same one leads, or none does,
# because the choices went in a circle or left the best of them level.
TOP_CHANGED = "top_changed"
SAME_TOP = "same_top"
CIRCLE = "circle"
LEVEL = "level"
BALANCED = (CIRCLE, LEVEL)


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
    # ✨ As a string first, so a percentage such as 2.5 is taken as written, not as its nearest binary fraction.
    within = 1 + Fraction(str(settings.get("percent", DEFAULT_PERCENT))) / 100
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
    """✨ The result re-weighted by the tie-break's answers (ticket 30c), as the content owner's prototype's `rescore`
    does it, for a participant marked for the tie-break who has answered or skipped every pair. The sort's result is
    left as it is: this is a second result, kept beside it, with `tie_break` saying which framework was broken and how.

    Only the tied framework's answers count. Each construct that entered the tie-break weighs 1 plus the share of its
    appearances it won, a skip being an appearance for both and a win for neither, and the points those constructs
    had between them are shared out again by weight. Each share is rounded half up on its own, as the compositional
    score rounds, where the prototype added what rounding lost to the leader, which could make a leader of one. The
    framework is ranked by the unrounded shares, which replace its fallback to declaration order; constructs level on
    them keep the sort's order. Every other construct and framework is as the sort scored it.

    The choices went in a circle when some construct beat one that beat one that beat it, as the prototype checks for,
    across both rounds; the prototype then says the constructs are genuinely balanced rather than forcing a winner.
    Where no circle is found but the best weight is shared, as when every pair is skipped, there is no winner to name
    either, so that is balanced too (LEVEL).
    """
    # ✨ With both frameworks tied, only the first is re-weighted for now (ticket 59b re-weights each).
    framework_id, cluster = next(iter(tie_break(document, result)["tied"].items()))
    answers = [answer for answer in answers if answer["framework"] == framework_id]
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

    frameworks = []
    for framework in result["frameworks"]:
        if framework["framework"] != framework_id:
            frameworks.append(framework)
            continue
        total = sum(construct["percent"] for construct in framework["constructs"] if construct["construct"] in cluster)
        share = {c: total * weights[c] / sum(weights.values()) for c in cluster}
        constructs = [
            {**construct, "percent": round_half_up(share[construct["construct"]])}
            if construct["construct"] in cluster
            else construct
            for construct in framework["constructs"]
        ]
        # ✨ Stable, so constructs level on their unrounded share keep the order the sort ranked them in.
        constructs.sort(key=lambda construct: -share.get(construct["construct"], construct["percent"]))
        frameworks.append({"framework": framework_id, "constructs": constructs})

    best = max(weights.values())
    if _in_a_circle(beaten):
        outcome = CIRCLE
    elif sum(1 for weight in weights.values() if weight == best) > 1:
        outcome = LEVEL
    elif max(cluster, key=lambda c: weights[c]) != cluster[0]:
        outcome = TOP_CHANGED
    else:
        outcome = SAME_TOP
    return {
        "method": REWEIGHTING,
        "frameworks": frameworks,
        "tie_break": {"framework": framework_id, "outcome": outcome},
    }


def _in_a_circle(beaten):
    """✨ Whether some construct beat one that beat one that beat it, as the prototype's `hasCycle` asks."""
    return any(a in beaten[c] for a in beaten for b in beaten[a] for c in beaten[b])
