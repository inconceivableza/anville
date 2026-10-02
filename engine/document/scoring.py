"""✨ Scoring a sort answer by a named, frozen method (ADR 0003).

The pathway document chooses a method by name (`measurement.scoring.method`). A method is never edited once
a response has been scored with it: a change in behaviour is a new name. Nothing here touches the database
or a request.
"""

import math


def score(document, answer):
    """✨ The result of one sort answer, by the method the document names. The answer is already valid."""
    method = document["measurement"]["scoring"]["method"]
    return {"method": method, "frameworks": METHODS[method]["score"](document, answer)}


def shares(document, answer):
    """✨ Each construct's unrounded percent, by the method the document names, as `{framework: {construct: share}}`.

    What a result's percents are before rounding, for averaging several answers without rounding twice.
    """
    method = document["measurement"]["scoring"]["method"]
    return METHODS[method]["shares"](document, answer)


def percents_by_construct(result):
    """✨ A result's rounded percents as `{framework: {construct: percent}}`, so they are found by id, not position."""
    return {
        framework["framework"]: {construct["construct"]: construct["percent"] for construct in framework["constructs"]}
        for framework in result["frameworks"]
    }


def _compositional_share(document, answer):
    """✨ The prototype's computeAll(), frozen.

    A construct's raw value is the sum of its items' values, and its percent is that raw value's share of
    the grand total, rounded on its own, so a framework's percents need not add up to 100. Constructs are
    ranked by rounded percent, and ties keep the order the constructs were declared in.
    """
    frameworks = []
    for framework, raw in _raw_values(document, answer):
        unrounded = _share_of_total(raw)
        constructs = [
            {"construct": construct, "raw": value, "percent": round_half_up(unrounded[construct])}
            for construct, value in raw.items()
        ]
        constructs.sort(key=lambda construct: -construct["percent"])  # ✨ stable, so ties keep declaration order
        frameworks.append({"framework": framework["id"], "constructs": constructs})
    return frameworks


def _compositional_shares(document, answer):
    """✨ `_compositional_share`'s percents before rounding, frozen with it."""
    return {framework["id"]: _share_of_total(raw) for framework, raw in _raw_values(document, answer)}


def _raw_values(document, answer):
    """✨ Each framework with its constructs' raw values, the sums of their items' values, in declaration order."""
    for framework in document["measurement"]["frameworks"]:
        raw = {construct["id"]: 0 for construct in framework["constructs"]}
        for item in document["instrument"]["items"]:
            for construct in item["loads"]:
                if construct in raw:
                    raw[construct] += answer[item["id"]]["value"]
        yield framework, raw


def _share_of_total(raw):
    """✨ Each raw value as a percent of the framework's grand total, unrounded; all 0 when the total is 0."""
    total = sum(raw.values())
    return {construct: value / total * 100 if total else 0 for construct, value in raw.items()}


def round_half_up(number):
    """✨ JavaScript's Math.round, which the prototype used, frozen with the methods that use it.

    Python's round() takes 0.5 to 0, not 1.
    """
    return math.floor(number + 0.5)


# ✨ A method scores an answer and gives the same percents unrounded; a new method must supply both.
METHODS = {"compositional_share": {"score": _compositional_share, "shares": _compositional_shares}}
