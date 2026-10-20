# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Every drawing sits at a construct's unrounded share (ADR 0018), so two constructs a fraction apart are never
drawn as one. The results page, Section 1's results and the coach's view all draw `results_page`; the comparison
draws `comparison_page`."""

from engine.document.aggregation import aggregate
from engine.document.scoring import score
from engine.document.tie_break import reweigh
from engine.results import comparison_page, results_page
from tests.documents import complete_sort, sort_pathway, with_a_tie_break

# ✨ Apostle and Deliver 100 of 199, Prophet and Ponder 99: 50.25% and 49.75%, both 50 when rounded. On an axis
# ending at twice an even share, 100, they sit at 50.25 and 49.75.
NEAR = complete_sort(a5={"bucket": "strength", "value": 100}, p1={"bucket": "strength", "value": 99})


def drawn(page, framework=0):
    """✨ A page's framework as `{label: bar}`."""
    return {bar["label"]: bar for bar in page["frameworks"][framework]["bars"]}


def test_two_constructs_a_fraction_apart_are_drawn_apart_on_the_results():
    document = sort_pathway()

    bars = drawn(results_page(document, score(document, NEAR), NEAR, "Sam"))

    assert (bars["Apostle"]["percent"], bars["Prophet"]["percent"]) == (50, 50)
    assert (bars["Apostle"]["at"], bars["Prophet"]["at"]) == (50.25, 49.75)


def test_constructs_on_the_same_rounded_percent_are_listed_by_unrounded_share_highest_first():
    """✨ Prophet's 100 of 199 is 50.25% and Apostle's 99 is 49.75%: both 50, so the stored result keeps Apostle, declared
    first, ahead. The page lists Prophet first, as it is drawn."""
    document = sort_pathway()
    sort = complete_sort(a5={"bucket": "strength", "value": 99}, p1={"bucket": "strength", "value": 100})
    stored = score(document, sort)
    assert [c["construct"] for c in stored["frameworks"][0]["constructs"]] == ["apostle", "prophet"]

    bars = results_page(document, stored, sort, "Sam")["frameworks"][0]["bars"]

    assert [(bar["label"], bar["at"]) for bar in bars] == [("Prophet", 50.25), ("Apostle", 49.75)]


def test_a_re_weighted_result_is_drawn_at_its_unrounded_shares():
    """✨ A third item, on Prophet and Deliver, ties Apostle and Prophet at 50 each and leaves PEP clear. Prophet chosen
    twice leads by just over 5%, 51.22 to Apostle's 48.78, so they sit there, not at 51 and 49."""
    document = with_a_tie_break(sort_pathway())
    document["instrument"]["items"].append({"id": "x1", "text": "Seeing it through", "loads": ["prophet", "deliver"]})
    sort = complete_sort(
        a5={"bucket": "strength", "value": 50},
        p1={"bucket": "not-me", "value": 10},
        x1={"bucket": "strength", "value": 40},
    )
    sent = score(document, sort)
    answers = [{"framework": "apest", "constructs": ["apostle", "prophet"], "round": r, "chosen": "prophet"} for r in (0, 1)]

    bars = drawn(results_page(document, reweigh(document, sent, answers), sort, "Sam"))

    assert (bars["Prophet"]["at"], bars["Apostle"]["at"]) == (51.22, 48.78)


def test_the_comparison_draws_the_participant_the_observers_mean_and_each_observer_at_unrounded_shares():
    """✨ Every observer sent NEAR too, so their mean and each of them sit at 50.25 and 49.75 as well."""
    document = sort_pathway()

    page = comparison_page(document, score(document, NEAR), NEAR, aggregate(document, [NEAR] * 3))

    bars = drawn(page)
    assert (bars["Apostle"]["you_at"], bars["Prophet"]["you_at"]) == (50.25, 49.75)
    assert (bars["Apostle"]["others_at"], bars["Prophet"]["others_at"]) == (50.25, 49.75)
    assert [dot["x"] for dot in bars["Apostle"]["strip"]["dots"]] == [50.25] * 3
    assert [dot["x"] for dot in bars["Prophet"]["strip"]["dots"]] == [49.75] * 3


def test_the_observers_mean_and_each_observer_are_worded_from_unrounded_shares():
    """✨ Apostle's 37 of 87 is 42.53%, which rounds to 43, 86% of an even share of 50, but is 85.06% unrounded: below
    a band that starts at 86."""
    document = sort_pathway()
    document["presentation"]["standing"] = {
        "bands": [{"at_least": 110, "label": "Strong"}, {"at_least": 86, "label": "Present"}],
        "below": "Less used",
    }
    sent = complete_sort(a5={"bucket": "strength", "value": 37}, p1={"bucket": "strength", "value": 50})

    page = comparison_page(document, score(document, NEAR), NEAR, aggregate(document, [sent] * 3))

    apostle = drawn(page)["Apostle"]
    assert apostle["others_standing"] == "Less used"
    assert apostle["strip"]["standings"] == ["Less used"] * 3
