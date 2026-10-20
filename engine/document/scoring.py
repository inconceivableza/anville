# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Scoring a sort answer by a named, frozen method (ADR 0003).

The pathway document chooses a method by name (`measurement.scoring.method`). A method is never edited once
a response has been scored with it: a change in behaviour is a new name. Nothing here touches the database
or a request.
"""

import math
from fractions import Fraction


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


def unrounded_shares(result):
    """✨ A stored result's shares before rounding, as `{framework: {construct: share}}` (ADR 0018).

    A result whose method keeps what its shares were made from has them worked out again from it, exactly; any other
    result, such as one the tie-break re-weighted, gives the exact share it keeps beside each percent, or the percent
    where it keeps none, as one re-weighted before ticket 59b.
    """
    method = METHODS.get(result.get("method"), {}).get("stored_shares", _kept_shares)
    return method(result)


def _kept_shares(result):
    """✨ The exact share a result keeps beside each percent, as a fraction, or the percent where it keeps none, for a
    result whose method cannot work its shares out again."""
    return {
        framework["framework"]: {
            construct["construct"]: Fraction(construct["share"]) if "share" in construct else construct["percent"]
            for construct in framework["constructs"]
        }
        for framework in result["frameworks"]
    }


def _compositional_stored_shares(result):
    """✨ `_compositional_share`'s shares worked out again from the raw values its result keeps, as exact fractions,
    so a share exactly on a boundary is never nudged off it by floating point."""
    shares = {}
    for framework in result["frameworks"]:
        total = sum(Fraction(construct["raw"]) for construct in framework["constructs"])
        shares[framework["framework"]] = {
            construct["construct"]: Fraction(construct["raw"]) * 100 / total if total else Fraction(0)
            for construct in framework["constructs"]
        }
    return shares


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

    Python's round() takes 0.5 to 0, not 1. A fraction is rounded exactly, with a half of its own: a float's half would
    turn it into a float, which could round one a hair under a half up. A float or an int rounds as it always has.
    """
    return math.floor(number + (Fraction(1, 2) if isinstance(number, Fraction) else 0.5))


# ✨ A method scores an answer, gives the same percents unrounded, and works them out again from a result it made; a
# new method must supply all three.
METHODS = {
    "compositional_share": {
        "score": _compositional_share,
        "shares": _compositional_shares,
        "stored_shares": _compositional_stored_shares,
    }
}
