# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A construct's drawing and its standing take its standing's colour, on both frameworks, so a colour never disagrees
with the word beside it (developer's call, 20 Oct). The colour follows the standing's place among the document's bands,
highest first, never its label. The results page, Section 1's results and the coach's view all draw `results_page`."""

from engine.document.scoring import score
from engine.results import results_page
from tests.documents import complete_sort, sort_pathway


def coloured(sort, document=None):
    """✨ Every bar of `sort_pathway()`'s two frameworks, as `{label: (standing, colour)}`. Each has two constructs, so an
    even share is 50 and the default bands start at shares of 62.5 (Leading), 52.5 (Strong) and 42.5 (Present)."""
    document = document or sort_pathway()
    page = results_page(document, score(document, sort), sort, "Sam")
    return {bar["label"]: (bar["standing"], bar["colour"]) for framework in page["frameworks"] for bar in framework["bars"]}


def test_constructs_with_the_same_standing_share_a_colour_whatever_their_rank():
    """✨ 52% and 48%: one ranked above the other on each framework, but all four Present."""
    bars = coloured(complete_sort(a5={"bucket": "strength", "value": 52}, p1={"bucket": "strength", "value": 48}))

    assert {standing for standing, _ in bars.values()} == {"Present"}
    assert len({colour for _, colour in bars.values()}) == 1


def test_constructs_with_different_standings_take_different_colours():
    leading = coloured(complete_sort(a5={"bucket": "strength", "value": 90}, p1={"bucket": "strength", "value": 10}))
    strong = coloured(complete_sort(a5={"bucket": "strength", "value": 55}, p1={"bucket": "strength", "value": 45}))

    assert (leading["Apostle"][0], strong["Apostle"][0], strong["Prophet"][0], leading["Prophet"][0]) == (
        "Leading",
        "Strong",
        "Present",
        "Less used",
    )
    assert len({leading["Apostle"][1], strong["Apostle"][1], strong["Prophet"][1], leading["Prophet"][1]}) == 4


def test_less_used_takes_the_less_used_colour_on_both_frameworks():
    bars = coloured(complete_sort(a5={"bucket": "strength", "value": 90}, p1={"bucket": "strength", "value": 10}))

    assert (bars["Prophet"], bars["Ponder"]) == (("Less used", "standing-below"), ("Less used", "standing-below"))
    assert (bars["Apostle"][1], bars["Deliver"][1]) == ("standing-1", "standing-1")


def test_the_colour_follows_the_bands_place_not_its_label():
    """✨ Two bands of another pathway's, written lowest first: the higher takes the top standing's colour, the lower
    the next, and the label below them the less-used colour."""
    document = sort_pathway()
    document["presentation"]["standing"] = {
        "bands": [{"at_least": 90, "label": "Often"}, {"at_least": 110, "label": "Mostly"}],
        "below": "Seldom",
    }
    high = coloured(complete_sort(a5={"bucket": "strength", "value": 60}, p1={"bucket": "strength", "value": 40}), document)
    near = coloured(complete_sort(a5={"bucket": "strength", "value": 50}, p1={"bucket": "strength", "value": 50}), document)

    assert (high["Apostle"], near["Apostle"], high["Prophet"]) == (
        ("Mostly", "standing-1"),
        ("Often", "standing-2"),
        ("Seldom", "standing-below"),
    )
