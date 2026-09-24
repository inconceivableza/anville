"""✨ Scoring a sort answer by a named, frozen method (ADR 0003).

The pathway document chooses a method by name (`measurement.scoring.method`). A method is never edited once
a response has been scored with it: a change in behaviour is a new name. Nothing here touches the database
or a request.
"""

import math


def score(document, answer):
    """✨ The result of one sort answer, by the method the document names. The answer is already valid."""
    method = document["measurement"]["scoring"]["method"]
    return {"method": method, "frameworks": METHODS[method](document, answer)}


def _compositional_share(document, answer):
    """✨ The prototype's computeAll(), frozen.

    A construct's raw value is the sum of its items' values, and its percent is that raw value's share of
    the grand total, rounded on its own, so a framework's percents need not add up to 100. Constructs are
    ranked by rounded percent, and ties keep the order the constructs were declared in.
    """
    frameworks = []
    for framework in document["measurement"]["frameworks"]:
        raw = {construct["id"]: 0 for construct in framework["constructs"]}
        for item in document["instrument"]["items"]:
            for construct in item["loads"]:
                if construct in raw:
                    raw[construct] += answer[item["id"]]["value"]
        total = sum(raw.values())
        constructs = [
            {"construct": construct, "raw": value, "percent": _round_half_up(value / total * 100) if total else 0}
            for construct, value in raw.items()
        ]
        constructs.sort(key=lambda construct: -construct["percent"])  # ✨ stable, so ties keep declaration order
        frameworks.append({"framework": framework["id"], "constructs": constructs})
    return frameworks


def _round_half_up(number):
    # ✨ JavaScript's Math.round, which the prototype used. Python's round() takes 0.5 to 0, not 1.
    return math.floor(number + 0.5)


METHODS = {"compositional_share": _compositional_share}
