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
