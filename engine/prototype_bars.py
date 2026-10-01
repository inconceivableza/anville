"""✨ PROTOTYPE, throwaway: ways to draw and word compositional scores, on the real results page and comparison.

Question: how should the results page and the comparison draw compositional scores, and what numbers should they
show? A–E try drawings of the percents; F–H try other numbers (bands in words, a ratio to an even share, rank only).
Switched by `?variant=A`…`H` on `/results/<block>/` and `/results/<block>/comparison/`, shown only while DEBUG is on. Lives on
the `prototype/result-bars` branch only; the winner is rewritten properly when it is folded into main.

Everything here only adds drawing positions (0–100 in each SVG's view box) to what the pages already show.
"""

import math

from engine.document.text import text_for

VARIANTS = {
    "A": "Current bars",
    "B": "Bars from an even share",
    "C": "Dots on a shared axis",
    "D": "Donuts",
    "E": "Stacked strips",
    "F": "Bands in words",
    "G": "Ratio to an even share",
    "H": "Rank only",
}

# ✨ Placeholder bands for variant F, as ratios to an even share, strongest first. Real ones would be the content
# owner's, set in the pathway document like 16b's agreement bands.
BANDS = [(1.25, "Leading"), (1.05, "Strong"), (0.85, "Present"), (0, "Less used")]

# ✨ The spec's five-point gap rule (ticket 16b), used here for F's words on the comparison.
SIGNIFICANT_GAP = 5


def variant_from(request, debug):
    variant = request.GET.get("variant", "").upper()
    return variant if debug and variant in VARIANTS else None


def switcher(variant, path):
    keys = list(VARIANTS)
    at = keys.index(variant)
    return {
        "key": variant,
        "name": VARIANTS[variant],
        "previous": f"{path}?variant={keys[at - 1]}",
        "next": f"{path}?variant={keys[(at + 1) % len(keys)]}",
        "off": path,
    }


def draw(document, frameworks):
    """✨ Adds each variant's positions to the page's frameworks, in place. A bar with `others` is on the comparison."""
    tones = _tones(document)
    for framework in frameworks:
        bars = framework["bars"]
        comparing = "others" in bars[0]
        values = [bar["percent"] for bar in bars] + ([bar["others"] for bar in bars] if comparing else [])
        even = 100 / len(bars)
        reach = max(5, math.ceil(max(abs(value - even) for value in values) / 5) * 5)
        top = max(10, math.ceil(max(values) / 10) * 10)
        framework["even"] = round(even, 1)
        framework["even_at"] = round(even / top * 100, 2)
        framework["top"] = top
        framework["reach"] = reach
        framework["ratio_low"] = f"{1 - reach / even:.1f}×"
        framework["ratio_high"] = f"{1 + reach / even:.1f}×"
        for bar in bars:
            bar["tone"] = tones.get(bar["label"], bar["colour"])
            bar["b"] = _from_even(bar["percent"], even, reach)
            bar["c"] = round(bar["percent"] / top * 100, 2)
            bar.update(_words(bar["percent"], even, [b["percent"] for b in bars]))
            if comparing:
                bar["ob"] = _from_even(bar["others"], even, reach)
                bar["oc"] = round(bar["others"] / top * 100, 2)
                bar["c_from"], bar["c_to"] = sorted((bar["c"], bar["oc"]))
                bar["c_span"] = round(bar["c_to"] - bar["c_from"], 2)
                bar["gap"] = bar["others"] - bar["percent"]
                bar["others_words"] = _words(bar["others"], even, [b["others"] for b in bars])
                bar["gap_words"] = (
                    "Much the same"
                    if abs(bar["gap"]) < SIGNIFICANT_GAP
                    else "Others place this higher" if bar["gap"] > 0 else "Others place this lower"
                )
                moved = bar["rank"] - bar["others_words"]["rank"]
                bar["move"] = "=" if moved == 0 else f"↑{moved}" if moved > 0 else f"↓{-moved}"
        framework["you_parts"] = _parts(bars, "percent")
        if comparing:
            framework["others_parts"] = _parts(bars, "others")


def _words(value, even, values):
    """✨ The other ways to say one share: its band, its ratio to an even share, points above or below even, and its
    rank among the framework's (ties share a place)."""
    ratio = value / even
    points = round(value - even)
    rank = 1 + sum(other > value for other in values)
    return {
        "band": next(name for floor, name in BANDS if ratio >= floor),
        "ratio": f"{ratio:.1f}×",
        "points": f"+{points}" if points > 0 else f"{points}" if points < 0 else "±0",
        "rank": rank,
        "ordinal": _ordinal(rank),
    }


def _ordinal(number):
    return f"{number}{'th' if 10 <= number % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')}"


def _from_even(value, even, reach):
    """✨ A bar starting at the even share (the middle, 50) and running right for more, left for less."""
    at = 50 + (value - even) / reach * 50
    return {"x": round(min(at, 50), 2), "width": round(abs(at - 50), 2), "above": value >= even}


def _parts(bars, field):
    """✨ Each construct's slice of the whole, for the donut (a circle 100 round) and the strip (100 wide). The rounded
    percents need not add to 100, so each is taken as a share of their sum."""
    total = sum(bar[field] for bar in bars) or 1
    parts, start = [], 0
    for bar in bars:
        share = bar[field] / total * 100
        parts.append(
            {
                "label": bar["label"],
                "percent": bar[field],
                "tone": bar["tone"],
                "start": round(start, 2),
                "share": round(share, 2),
                "rest": round(100 - share, 2),
                # ✨ A circle's stroke starts at three o'clock; 25 back puts the first slice at twelve.
                "offset": round(25 - start, 2),
                "middle": round(start + share / 2, 2),
            }
        )
        start += share
    return parts


def _tones(document):
    presented = {entry["construct"]: entry for entry in document.get("presentation", {}).get("constructs", [])}
    return {
        text_for(construct["label"], "participant"): f"tone-{presented[construct['id']]['tone']}"
        for framework in document["measurement"]["frameworks"]
        for construct in framework["constructs"]
        if "tone" in presented.get(construct["id"], {})
    }
