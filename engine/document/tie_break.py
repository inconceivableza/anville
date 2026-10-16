# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whether a participant's sort leaves a framework's leaders too close to call (ticket 30a).

A framework is tied when one or more of its other constructs are within the document's threshold of its leader, on
the stored result's rounded percents; at most the document's cluster size, leader first, enter the tie-break. Run on
the participant's own result alone, never an observer's. Nothing here touches the database or a request.
"""

from fractions import Fraction

from engine.document.scoring import round_half_up

# ✨ The content owner's prototype's: within four points of the leader, and at most the top four.
DEFAULT_THRESHOLD = 4
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
    tie-break, in the result's ranked order, and what follows. Tied on exactly one framework, the participant is marked
    for the tie-break (TIE_BREAK); on both, they are a generalist (GENERALIST), with nothing asked of them; on neither,
    there is nothing to break (None). A pathway without a tie-break marks no one."""
    settings = document.get("measurement", {}).get("tie_break")
    if settings is None:
        return {"tied": {}, "outcome": None}
    threshold = settings.get("threshold", DEFAULT_THRESHOLD)
    cluster = settings.get("cluster", DEFAULT_CLUSTER)
    tied = {}
    for framework in result["frameworks"]:
        # ✨ Stable, so constructs on the same percent keep the order the result ranked them in.
        ranked = sorted(framework["constructs"], key=lambda construct: -construct["percent"])
        leader = ranked[0]["percent"]
        close = [construct["construct"] for construct in ranked if leader - construct["percent"] <= threshold]
        if len(close) > 1:
            tied[framework["framework"]] = close[:cluster]
    outcome = GENERALIST if len(tied) > 1 else TIE_BREAK if tied else None
    return {"tied": tied, "outcome": outcome}


def pair_plan(document, result):
    """✨ The "Which is more true of you?" pairs a participant marked for the tie-break answers, in order (ticket 30b), or
    [] for anyone else. Each is `{"framework", "constructs": [a, b], "statements": [a's, b's], "round"}`.

    As the content owner's prototype plans them: every pair of the tied framework's constructs, never across
    frameworks, those involving the higher-ranked first (by the sum of the two ranks, ties in the order made), then a
    second round of the same pairs with the next statement of each, all cut to the document's budget from the end.
    Construct a shows its statement at the round's place and b the one after, so no pair repeats a statement across the
    two rounds. Worked out afresh from the stored result each time; the answers are stored, the plan is not.
    """
    detected = tie_break(document, result)
    if detected["outcome"] != TIE_BREAK:
        return []
    settings = document["measurement"]["tie_break"]
    statements = settings["statements"]
    [(framework, cluster)] = detected["tied"].items()
    ranked = [
        (i + j, a, b) for i, a in enumerate(cluster) for j, b in enumerate(cluster) if i < j
    ]
    ranked.sort(key=lambda pair: pair[0])
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
        for _, a, b in ranked
    ]
    return planned[: settings.get("budget", DEFAULT_BUDGET)]


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
    [(framework_id, cluster)] = tie_break(document, result)["tied"].items()
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
