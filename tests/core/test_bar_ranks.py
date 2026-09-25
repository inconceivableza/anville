"""✨ Colouring bars by rank: tied scores share a colour, as the prototype's PEP bars did."""

from engine.results import bar_ranks


def test_bars_are_ranked_by_score_and_tied_scores_share_a_rank():
    # ✨ The prototype's PEP percentages for the golden sort left at its seeds: Rally and Deliver tie at 13.
    assert bar_ranks([23, 20, 17, 14, 13, 13]) == [1, 2, 3, 4, 5, 5]


def test_after_a_tie_the_next_score_takes_the_next_rank_not_a_skipped_one():
    assert bar_ranks([20, 20, 17]) == [1, 1, 2]


def test_ranks_stop_at_six_the_number_of_rank_colours():
    assert bar_ranks([30, 25, 20, 15, 10, 5, 1]) == [1, 2, 3, 4, 5, 6, 6]
