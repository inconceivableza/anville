"""✨ What the comparison makes of a self-result beside the observer average: where they differ most, and how far the
observers agree with each other (ADR 0005).

Both rules read their numbers from the pathway document's `presentation.comparison`, falling back to the prototype's.
Nothing here touches the database or a request.
"""

# ✨ The prototype's: a gap of five points or more is worth reflecting on; less is a modest gap.
DEFAULT_SIGNIFICANT_GAP = 5

# ✨ The prototype's bands, by the range of the observers' percents, and the label for a range above them all.
DEFAULT_AGREEMENT = {
    "bands": [{"up_to": 6, "label": "Strong agreement"}, {"up_to": 14, "label": "Some variation"}],
    "above": "Divided views",
}

# ✨ How many gaps the comparison lists, across both frameworks, as the prototype did.
LARGEST_GAPS = 5


def comparison_settings(document):
    """✨ The document's `presentation.comparison`: its thresholds and wording, or nothing when it has none."""
    return document.get("presentation", {}).get("comparison", {})


def largest_gaps(document, pairs):
    """✨ The largest gaps between the participant's percent and the observers' mean, largest first.

    `pairs` holds each construct as `{framework, construct, you, others}` in the order declared, so ties keep that
    order. A gap's `direction` is `others_higher`, `you_higher`, or None when there is no gap at all.
    """
    significant_gap = comparison_settings(document).get("significant_gap", DEFAULT_SIGNIFICANT_GAP)
    gaps = []
    for pair in pairs:
        difference = pair["others"] - pair["you"]
        gaps.append(
            {
                **pair,
                "gap": abs(difference),
                "direction": "others_higher" if difference > 0 else "you_higher" if difference < 0 else None,
                "significant": abs(difference) >= significant_gap,
            }
        )
    gaps.sort(key=lambda gap: -gap["gap"])  # ✨ stable, so ties keep declaration order
    return gaps[:LARGEST_GAPS]


def agreement(document, per_observer):
    """✨ The label of the band the observers' range falls in: the narrowest band whose `up_to` the range doesn't pass,
    whatever order the bands are written in, or the label for above them all."""
    spread = max(per_observer) - min(per_observer)
    agreement_bands = comparison_settings(document).get("agreement", DEFAULT_AGREEMENT)
    for band in sorted(agreement_bands["bands"], key=lambda band: band["up_to"]):
        if spread <= band["up_to"]:
            return band["label"]
    return agreement_bands["above"]
