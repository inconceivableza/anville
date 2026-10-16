# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whether a participant's sort leaves a framework's leaders too close to call (ticket 30a).

A framework is tied when one or more of its other constructs are within the document's threshold of its leader, on
the stored result's rounded percents; at most the document's cluster size, leader first, enter the tie-break. Run on
the participant's own result alone, never an observer's. Nothing here touches the database or a request.
"""

# ✨ The content owner's prototype's: within four points of the leader, and at most the top four.
DEFAULT_THRESHOLD = 4
DEFAULT_CLUSTER = 4
# ✨ The prototype's: at most ten pairs, a guess it asks to be checked against drop-off (ticket 30b).
DEFAULT_BUDGET = 10
# ✨ A framework tied on its own gets a second round of the same pairs, with different statements (ticket 30b).
ROUNDS = 2


TIE_BREAK = "tie_break"
GENERALIST = "generalist"


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
