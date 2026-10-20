# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Colouring bars by rank: tied scores share a colour, as the prototype's PEP bars did, and only exactly tied ones,
since the drawings all use unrounded shares (ADR 0018)."""

from engine.document.scoring import score
from engine.results import bar_ranks, results_page
from tests.documents import complete_sort, sort_pathway


def pep_colours(sort):
    """✨ `sort_pathway()`'s PEP bars, coloured by rank, as `{label: colour}`."""
    document = sort_pathway()
    pep = results_page(document, score(document, sort), sort, "Sam")["frameworks"][1]
    return {bar["label"]: bar["colour"] for bar in pep["bars"]}


def test_bars_are_ranked_by_score_and_tied_scores_share_a_rank():
    # ✨ The prototype's PEP percentages for the golden sort left at its seeds: Rally and Deliver tie at 13.
    assert bar_ranks([23, 20, 17, 14, 13, 13]) == [1, 2, 3, 4, 5, 5]


def test_after_a_tie_the_next_score_takes_the_next_rank_not_a_skipped_one():
    assert bar_ranks([20, 20, 17]) == [1, 1, 2]


def test_ranks_stop_at_six_the_number_of_rank_colours():
    assert bar_ranks([30, 25, 20, 15, 10, 5, 1]) == [1, 2, 3, 4, 5, 6, 6]


def test_two_pep_scores_a_fraction_apart_take_different_colours():
    """✨ Deliver's 100 of 199 is 50.25% and Ponder's 99 is 49.75%: both 50 when rounded, but drawn apart."""
    near = complete_sort(a5={"bucket": "strength", "value": 100}, p1={"bucket": "strength", "value": 99})

    assert pep_colours(near) == {"Deliver": "rank-1", "Ponder": "rank-2"}


def test_two_pep_scores_exactly_tied_share_a_colour():
    tied = complete_sort(a5={"bucket": "strength", "value": 100}, p1={"bucket": "strength", "value": 100})

    assert set(pep_colours(tied).values()) == {"rank-1"}
