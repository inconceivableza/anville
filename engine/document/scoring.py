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


def stored_share(share):
    """✨ An exact share as a result keeps it beside its percent: written out as text, since a stored result is JSON,
    which holds no fractions. `_kept_share` alone turns it back into a number."""
    return str(share)


def _kept_share(construct):
    """✨ The exact share a result keeps beside a construct's percent, as a fraction, or the percent where it keeps
    none, as one re-weighted before ticket 59b."""
    return Fraction(construct["share"]) if "share" in construct else construct["percent"]


def _kept_shares(result):
    """✨ The exact share a result keeps beside each percent (`_kept_share`), for a result whose method cannot work its
    shares out again."""
    return {
        framework["framework"]: {
            construct["construct"]: _kept_share(construct) for construct in framework["constructs"]
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
    return _ranked(_raw_values(document, answer))


def _ranked(raw_values):
    """✨ Each framework's constructs with their raw values and percents, as `_compositional_share` ranks them. A raw
    value that is not a whole number is kept as an exact fraction written out (`stored_share`), as a result is JSON."""
    frameworks = []
    for framework, raw in raw_values:
        unrounded = _share_of_total(raw)
        constructs = [
            {
                "construct": construct,
                "raw": value if isinstance(value, int) else stored_share(value),
                "percent": round_half_up(unrounded[construct]),
            }
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


def _compositional_share_of_seen(document, answer):
    """✨ `_compositional_share`, leaving out every item an observer placed in "Haven't seen this" (ticket 108).

    Each construct's raw value is its seen items' mean, taken over all its items, so an item not seen neither raises
    nor lowers its construct, as the two-round prototype scores its contacts. With every item seen, as in any
    participant's sort, that is the sum of their values, and the result is `_compositional_share`'s exactly. As in the
    prototype, a construct seen on too few of its items (FEWEST_SEEN) takes the mean over every item seen instead, and
    an observer who saw nothing at all gives each construct the middle value (MIDDLE), so an even share.
    """
    return _ranked(_raw_values_of_seen(document, answer))


def _compositional_shares_of_seen(document, answer):
    """✨ `_compositional_share_of_seen`'s percents before rounding, frozen with it."""
    return {framework["id"]: _share_of_total(raw) for framework, raw in _raw_values_of_seen(document, answer)}


# ✨ The two-round prototype's `minSeen`: a construct seen on fewer of its items than this, or than all of them where it
# has fewer, takes the mean over every item seen, so a card or two cannot carry it either way.
FEWEST_SEEN = 4
# ✨ The middle of an item's values, 0 to 100, for a sort with nothing seen, as the prototype takes its scale's middle.
MIDDLE = 50


def _raw_values_of_seen(document, answer):
    """✨ Each framework with its constructs' raw values, as `_compositional_share_of_seen` takes them, in declaration
    order: a whole number wherever it is one, as with every item seen, and otherwise an exact fraction."""
    items = document["instrument"]["items"]
    seen = {item["id"]: answer[item["id"]]["value"] for item in items if answer[item["id"]].get("seen", True)}
    overall = Fraction(sum(seen.values()), len(seen)) if seen else Fraction(MIDDLE)
    for framework in document["measurement"]["frameworks"]:
        raw = {}
        for construct in framework["constructs"]:
            own = [item["id"] for item in items if construct["id"] in item["loads"]]
            values = [seen[item] for item in own if item in seen]
            enough = values and len(values) >= min(FEWEST_SEEN, len(own))
            value = (Fraction(sum(values), len(values)) if enough else overall) * len(own)
            raw[construct["id"]] = int(value) if value.denominator == 1 else value
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
    },
    "compositional_share_of_seen": {
        "score": _compositional_share_of_seen,
        "shares": _compositional_shares_of_seen,
        "stored_shares": _compositional_stored_shares,
    },
}
