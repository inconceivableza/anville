# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whether a participant's sort leaves a framework's leaders too close to call (ticket 30a): from a stored result and
the pathway document alone, with no request or database."""

from fractions import Fraction

import pytest

import tests.documents
from engine.document import validate
from engine.document.scoring import round_half_up, unrounded_shares
from engine.document.tie_break import outcomes, pair_plan, reweigh, tie_break
from engine.results import results_page
from tests.documents import sort_pathway

APEST = ["apostle", "prophet", "evangelist", "shepherd", "teacher", "deacon"]
PEP = ["ponder", "ideate", "assess", "rally", "facilitate", "deliver"]


def document(**tie_break_settings):
    """✨ A pathway with both frameworks and a tie-break, with any setting given."""
    return {
        "measurement": {
            "frameworks": [
                {"id": "apest", "label": "APEST(d)", "constructs": [{"id": c, "label": c} for c in APEST]},
                {"id": "pep", "label": "PEP", "constructs": [{"id": c, "label": c} for c in PEP]},
            ],
            "scoring": {"method": "compositional_share"},
            "tie_break": tie_break_settings,
        }
    }


def framework(framework_id, constructs, raws):
    """✨ One framework of a stored result as the compositional score makes it: each construct's raw value and its
    rounded share of the framework's total, ranked by that rounded share, ties in declaration order."""
    total = sum(raws)
    scored = [
        {"construct": c, "raw": raw, "percent": round_half_up(raw / total * 100) if total else 0}
        for c, raw in zip(constructs, raws)
    ]
    scored.sort(key=lambda construct: -construct["percent"])
    return {"framework": framework_id, "constructs": scored}


def result(apest, pep):
    return {"method": "compositional_share", "frameworks": [framework("apest", APEST, apest), framework("pep", PEP, pep)]}


CLEAR_APEST = [9, 34, 8, 14, 24, 11]  # ✨ the prototype's "Both clear"
CLEAR_PEP = [8, 33, 12, 10, 11, 26]


def test_a_leader_at_most_five_percent_more_than_another_is_too_close_to_call_and_just_over_is_not():
    """✨ Prophet's 105 is exactly 5% more than Apostle's 100, and 106 is 6% more."""
    at_five = result([100, 105, 60, 40, 30, 20], CLEAR_PEP)
    just_over = result([100, 106, 60, 40, 30, 20], CLEAR_PEP)

    assert tie_break(document(), at_five)["tied"] == {"apest": ["prophet", "apostle"]}
    assert tie_break(document(), just_over)["tied"] == {}


def test_a_share_of_nothing_is_never_too_close_to_call():
    assert tie_break(document(), result([0] * 6, CLEAR_PEP)) == {"tied": {}, "outcome": None}


def test_the_cluster_is_the_leader_on_its_unrounded_share_first_up_to_the_cluster_size():
    """✨ All six are within 5% of Deacon, who leads on 21 to the others' 20; four go on by default, two when the
    document says two. All six round to 17, and Deacon and Evangelist below to 20, so only the unrounded shares put
    Deacon first."""
    close = result([20, 20, 20, 20, 20, 21], CLEAR_PEP)
    rounded_alike = result([1585, 1816, 1960, 1787, 836, 2017], CLEAR_PEP)

    assert tie_break(document(), close)["tied"] == {"apest": ["deacon", "apostle", "prophet", "evangelist"]}
    assert tie_break(document(cluster=2), close)["tied"] == {"apest": ["deacon", "apostle"]}
    assert tie_break(document(), rounded_alike)["tied"] == {"apest": ["deacon", "evangelist"]}


def test_the_percentage_comes_from_the_document():
    """✨ Prophet's 109 is 9% more than Apostle's 100."""
    nine_more = result([100, 109, 60, 40, 30, 20], CLEAR_PEP)

    assert tie_break(document(), nine_more)["tied"] == {}
    assert tie_break(document(percent=10), nine_more)["tied"] == {"apest": ["prophet", "apostle"]}


def test_tied_on_exactly_one_framework_marks_the_participant_for_the_tie_break():
    only_role_tied = result([13, 26, 9, 25, 16, 11], CLEAR_PEP)  # ✨ the prototype's "Only role tied"

    assert tie_break(document(), only_role_tied)["outcome"] == "tie_break"


# ✨ ADR 0018's worked example: Deacon 20.17, Evangelist 19.60, Prophet 18.16, Shepherd 17.87, Apostle 15.85 and
# Teacher 8.36, in declaration order here; PEP the same shape. Teacher and Facilitate read "Less used".
REVIEW_WALK = [1585, 1816, 1960, 1787, 836, 2017]


def test_too_close_to_call_on_both_frameworks_but_not_flat_is_never_a_generalist_and_has_pairs_on_both():
    both_tied = result(REVIEW_WALK, REVIEW_WALK)

    detected = tie_break(document(), both_tied)
    assert detected == {"tied": {"apest": ["deacon", "evangelist"], "pep": ["deliver", "assess"]}, "outcome": "tie_break"}
    assert {pair["framework"] for pair in pair_plan(planned(), both_tied)} == {"apest", "pep"}


def test_flat_on_both_frameworks_is_a_generalist_with_no_pairs_though_too_close_to_call():
    """✨ An even share is 16.67: 17 is 102% of it and 16 is 96%, so every construct reads "Present"."""
    flat = result([17, 17, 17, 17, 16, 16], [16, 17, 16, 17, 17, 17])

    assert tie_break(document(), flat)["outcome"] == "generalist"
    assert pair_plan(planned(), flat) == []


def test_tied_on_neither_framework_leaves_nothing_to_break():
    assert tie_break(document(), result(CLEAR_APEST, CLEAR_PEP)) == {"tied": {}, "outcome": None}


def test_a_pathway_without_a_tie_break_never_marks_anyone():
    """✨ The faithful port has none, since the original prototype had none."""
    without = document()
    del without["measurement"]["tie_break"]
    flat = result([17, 17, 16, 17, 16, 17], [17, 16, 17, 17, 16, 17])

    assert tie_break(without, flat) == {"tied": {}, "outcome": None}


def statements():
    """✨ Three statements for every construct, each naming its construct and its place."""
    return {c: [f"{c} {n}" for n in range(3)] for c in APEST + PEP}


def planned(budget=None, **settings):
    """✨ A pathway whose tie-break has statements, and the budget if one is given."""
    if budget is not None:
        settings["budget"] = budget
    return document(statements=statements(), **settings)


ONLY_ROLE_TIED = [13, 26, 9, 25, 16, 11]  # ✨ the prototype's: Prophet and Shepherd within a point
FLAT = [17, 17, 16, 17, 16, 17]  # ✨ the prototype's "Both flat" APEST: four enter, so six pairs a round


def test_pairs_stay_within_the_tied_framework():
    pairs = pair_plan(planned(), result(FLAT, CLEAR_PEP))

    assert pairs
    assert {pair["framework"] for pair in pairs} == {"apest"}
    assert all(set(pair["constructs"]) <= {"apostle", "prophet", "shepherd", "deacon"} for pair in pairs)


def test_nobody_but_a_participant_marked_for_the_tie_break_has_pairs():
    assert pair_plan(planned(), result(CLEAR_APEST, CLEAR_PEP)) == []
    assert pair_plan(planned(), result(FLAT, [17, 16, 17, 17, 16, 17])) == []


def test_pairs_among_the_top_ranked_constructs_survive_trimming_to_the_budget_from_the_document():
    """✨ Four tied make six pairs a round; ranked apostle, prophet, shepherd, deacon, the pairs with the leader come
    first and the one between third and fourth last."""
    pairs = pair_plan(planned(budget=3), result(FLAT, CLEAR_PEP))

    assert [pair["constructs"] for pair in pairs] == [
        ["apostle", "prophet"],
        ["apostle", "shepherd"],
        ["apostle", "deacon"],
    ]


def test_the_default_budget_of_ten_keeps_the_first_round_whole_and_fills_the_rest_with_a_second():
    pairs = pair_plan(planned(), result(FLAT, CLEAR_PEP))

    assert [pair["round"] for pair in pairs] == [0] * 6 + [1] * 4


def test_a_second_round_asks_about_the_same_pair_with_different_statements():
    pairs = pair_plan(planned(), result(ONLY_ROLE_TIED, CLEAR_PEP))

    first, second = pairs
    assert first["constructs"] == second["constructs"] == ["prophet", "shepherd"]
    assert all(a != b for a, b in zip(first["statements"], second["statements"]))
    assert all(
        statement in statements()[construct]
        for pair in pairs
        for construct, statement in zip(pair["constructs"], pair["statements"])
    )


def asked(pairs):
    """✨ A pair plan as `[(framework, a, b, round), ...]`, in the order asked."""
    return [(pair["framework"], *pair["constructs"], pair["round"]) for pair in pairs]


def test_with_both_frameworks_too_close_to_call_the_pairs_alternate_between_them_each_in_two_rounds():
    pairs = pair_plan(planned(), result(REVIEW_WALK, REVIEW_WALK))

    assert asked(pairs) == [
        ("apest", "deacon", "evangelist", 0),
        ("pep", "deliver", "assess", 0),
        ("apest", "deacon", "evangelist", 1),
        ("pep", "deliver", "assess", 1),
    ]


# ✨ Four tied on each framework, so six pairs a round each: 24 questions in all, well past the budget of ten.
FOUR_TIED = [21, 21, 21, 21, 10, 6]


def test_past_the_budget_second_rounds_go_first_then_the_least_important_pairs():
    """✨ Ranked first to fourth, a pair's importance is its places' sum: 1st against 2nd most, 3rd against 4th least."""
    both = result(FOUR_TIED, FOUR_TIED)
    apest = ["apostle", "prophet", "evangelist", "shepherd"]
    pep = ["ponder", "ideate", "assess", "rally"]
    by_importance = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    first_rounds = [
        asked_pair
        for i, j in by_importance
        for asked_pair in (("apest", apest[i], apest[j], 0), ("pep", pep[i], pep[j], 0))
    ]

    assert asked(pair_plan(planned(), both)) == first_rounds[:10]
    assert asked(pair_plan(planned(budget=14), both)) == first_rounds + [
        ("apest", "apostle", "prophet", 1),
        ("pep", "ponder", "ideate", 1),
    ]


def answered(*picks, framework="apest"):
    """✨ The stored answers to a tie-break's pairs, each `(a, b, chosen)`, `chosen` None for a skip."""
    return [
        {"framework": framework, "constructs": [a, b], "round": 0, "chosen": chosen} for a, b, chosen in picks
    ]


def percents(reweighted, framework_id="apest"):
    """✨ A re-weighted result's framework as `[(construct, percent), ...]`, in its ranked order."""
    [framework] = [framework for framework in reweighted["frameworks"] if framework["framework"] == framework_id]
    return [(construct["construct"], construct["percent"]) for construct in framework["constructs"]]


def test_re_weighting_a_tied_framework_gives_a_clear_leader_where_the_choices_give_one():
    """✨ Prophet 26 and Shepherd 25 share 51 points. Shepherd chosen in both rounds wins 2 of 2, so weighs 2 to
    Prophet's 1, and leads by just over 5% of the 51: 26.12 to 24.88. Everyone else, and the other framework, keep the
    sort's."""
    sent = result(ONLY_ROLE_TIED, CLEAR_PEP)

    chose_shepherd_twice = answered(("prophet", "shepherd", "shepherd"), ("prophet", "shepherd", "shepherd"))

    reweighted = reweigh(planned(), sent, chose_shepherd_twice)

    assert percents(reweighted) == [
        ("shepherd", 26),
        ("prophet", 25),
        ("teacher", 16),
        ("apostle", 13),
        ("deacon", 11),
        ("evangelist", 9),
    ]
    assert outcomes(reweighted) == {"apest": "top_changed"}
    assert percents(reweighted, "pep") == percents(sent, "pep")
    assert reweighted["method"] != sent["method"]


def test_a_leader_the_choices_keep_is_kept_and_said_to_be_the_same():
    """✨ A skip counts as an appearance for both and a win for neither: Prophet wins 1 of 2 and weighs 1.5 to
    Shepherd's 1, so leads by just over 5% of the 51 points, 26.12 to 24.88."""
    reweighted = reweigh(
        planned(),
        result(ONLY_ROLE_TIED, CLEAR_PEP),
        answered(("prophet", "shepherd", "prophet"), ("prophet", "shepherd", None)),
    )

    assert percents(reweighted)[:2] == [("prophet", 26), ("shepherd", 25)]
    assert outcomes(reweighted) == {"apest": "same_top"}


# ✨ The re-weighting opens a gap of 5.01% between one weight and the next (fix-22): a hundredth of a percent past the
# document's 5%, so the two are no longer too close to call.
JUST_OVER = Fraction(10501, 10000)


def test_the_answers_put_the_tied_constructs_in_order_just_over_the_threshold_apart_keeping_their_total():
    """✨ The seeded `separated` sort: Deacon 22.0% and Evangelist 21.2% are tied, and Evangelist chosen in both rounds
    now leads by just over 5%, about 22.1% to 21.1%, where sharing out by weight made it 28.8% to 14.4%."""
    sent = result([234, 324, 382, 297, 167, 396], CLEAR_PEP)
    chose_evangelist_twice = answered(("deacon", "evangelist", "evangelist"), ("deacon", "evangelist", "evangelist"))

    reweighted = reweigh(planned(), sent, chose_evangelist_twice)

    before, after = unrounded_shares(sent)["apest"], unrounded_shares(reweighted)["apest"]
    assert after["evangelist"] / after["deacon"] == JUST_OVER
    assert after["evangelist"] + after["deacon"] == before["evangelist"] + before["deacon"]
    assert {c: s for c, s in after.items() if c not in ("evangelist", "deacon")} == {
        c: s for c, s in before.items() if c not in ("evangelist", "deacon")
    }
    assert tie_break(planned(), reweighted)["tied"] == {}


def test_three_tied_constructs_end_in_the_order_of_their_weights_each_just_over_the_threshold_ahead_of_the_next():
    """✨ Teacher beats both in both rounds and Prophet beats Apostle in both: weights of 2, 1.5 and 1."""
    teacher_then_prophet = answered(
        *[("apostle", "prophet", "prophet"), ("apostle", "teacher", "teacher"), ("prophet", "teacher", "teacher")] * 2
    )

    reweighted = reweigh(planned(), result(THREE_LEVEL, CLEAR_PEP), teacher_then_prophet)

    after = unrounded_shares(reweighted)["apest"]
    assert [construct for construct, _ in percents(reweighted)[:3]] == ["teacher", "prophet", "apostle"]
    assert after["teacher"] / after["prophet"] == after["prophet"] / after["apostle"] == JUST_OVER
    assert after["teacher"] + after["prophet"] + after["apostle"] == Fraction(6000, 90)


def test_constructs_sharing_the_top_weight_stay_level_with_each_other():
    """✨ Apostle and Prophet share the best weight, Shepherd and Deacon the one below."""
    reweighted = reweigh(planned(), result(FLAT, CLEAR_PEP), LEVEL_AT_THE_TOP)

    after = unrounded_shares(reweighted)["apest"]
    assert after["apostle"] == after["prophet"]
    assert after["shepherd"] == after["deacon"]
    assert after["apostle"] / after["shepherd"] == JUST_OVER


# ✨ Of the four tied in FLAT (68 points between them), Apostle beats Prophet, Prophet beats Shepherd and Shepherd
# beats Apostle, and every pair with Deacon is skipped: each of the three wins 1 of 3 and Deacon none of 3.
IN_A_CIRCLE = answered(
    ("apostle", "prophet", "apostle"),
    ("apostle", "shepherd", "shepherd"),
    ("apostle", "deacon", None),
    ("prophet", "shepherd", "prophet"),
    ("prophet", "deacon", None),
    ("shepherd", "deacon", None),
)
ALL_SKIPPED = answered(*[(*answer["constructs"], None) for answer in IN_A_CIRCLE])
# ✨ Apostle beats Prophet and Prophet beats Apostle, the rest skipped: no circle, but Apostle and Prophet share the
# best weight.
LEVEL_AT_THE_TOP = answered(
    ("apostle", "prophet", "apostle"),
    ("apostle", "shepherd", None),
    ("apostle", "deacon", None),
    ("prophet", "shepherd", None),
    ("prophet", "deacon", None),
    ("apostle", "prophet", "prophet"),
)


@pytest.mark.parametrize(
    "answers, outcome, shares",
    [
        # ✨ Each of the three weighs 4/3 and Deacon 1, so each is just over 5% ahead of Deacon: 17.21 each and 16.38
        # for Deacon, of the 68.
        (IN_A_CIRCLE, "circle", {"apostle": 17, "prophet": 17, "shepherd": 17, "deacon": 16}),
        # ✨ Apostle and Prophet each win 1 of 4 and weigh 1.25 to Shepherd's and Deacon's 1, so are just over 5% ahead
        # of them: 17.42 and 16.58, all 17 when rounded.
        (LEVEL_AT_THE_TOP, "level", {"apostle": 17, "prophet": 17, "shepherd": 17, "deacon": 17}),
    ],
    ids=["in a circle", "level at the top"],
)
def test_choices_that_go_in_a_circle_or_leave_the_best_level_are_balanced_with_no_winner_forced(
    answers, outcome, shares
):
    reweighted = reweigh(planned(), result(FLAT, CLEAR_PEP), answers)

    assert outcomes(reweighted) == {"apest": outcome}
    assert {construct: percent for construct, percent in percents(reweighted) if construct in shares} == shares


# ✨ Apostle, Prophet and Teacher level at the top, Evangelist, Shepherd and Deacon well below.
THREE_LEVEL = [20, 20, 10, 10, 20, 10]


def test_choices_that_go_in_a_circle_but_leave_one_weight_on_top_are_separated_by_the_weights():
    """✨ The first round goes in a circle (Apostle beats Prophet, Prophet Teacher, Teacher Apostle); in the second
    Apostle beats both and Prophet Teacher. Apostle wins 3 of 4, Prophet 2 and Teacher 1: weights of 1.75, 1.5 and
    1.25, so Apostle leads on its own."""
    circle_then_clear = answered(
        ("apostle", "prophet", "apostle"),
        ("prophet", "teacher", "prophet"),
        ("apostle", "teacher", "teacher"),
        ("apostle", "prophet", "apostle"),
        ("apostle", "teacher", "apostle"),
        ("prophet", "teacher", "prophet"),
    )

    reweighted = reweigh(planned(), result(THREE_LEVEL, CLEAR_PEP), circle_then_clear)

    assert outcomes(reweighted) == {"apest": "same_top"}
    assert [construct for construct, _ in percents(reweighted)[:3]] == ["apostle", "prophet", "teacher"]


def test_every_pair_skipped_is_an_outcome_of_its_own_and_leaves_the_framework_as_sorted():
    sent = result(FLAT, CLEAR_PEP)

    reweighted = reweigh(planned(), sent, ALL_SKIPPED)

    assert outcomes(reweighted) == {"apest": "skipped"}
    assert percents(reweighted) == percents(sent)
    assert unrounded_shares(reweighted) == unrounded_shares(sent)


# ✨ ADR 0018's worked example on both frameworks: Deacon 2017 and Evangelist 1960 of 10001 on APEST(d), Deliver and
# Assess on PEP.
BOTH_TIED = result(REVIEW_WALK, REVIEW_WALK)
CHOSE_EVANGELIST_TWICE = answered(("deacon", "evangelist", "evangelist"), ("deacon", "evangelist", "evangelist"))
SKIPPED_ON_PEP = answered(("deliver", "assess", None), ("deliver", "assess", None), framework="pep")
ASSESS_THEN_DELIVER = answered(("deliver", "assess", "assess"), ("deliver", "assess", "deliver"), framework="pep")


def test_with_pairs_on_both_frameworks_each_is_re_weighted_from_its_own_answers_with_its_own_outcome():
    """✨ Evangelist chosen twice weighs 2 to Deacon's 1, so leads by just over 5% of their 3977 / 10001: 20.37 to
    19.40. PEP, every pair skipped, is as the sort left it."""
    reweighted = reweigh(planned(), BOTH_TIED, CHOSE_EVANGELIST_TWICE + SKIPPED_ON_PEP)

    assert outcomes(reweighted) == {"apest": "top_changed", "pep": "skipped"}
    assert percents(reweighted)[0] == ("evangelist", 20)
    assert dict(percents(reweighted))["deacon"] == 19
    assert percents(reweighted, "pep") == percents(BOTH_TIED, "pep")


def test_one_frameworks_answers_never_change_the_other():
    apest_alone = reweigh(planned(), BOTH_TIED, CHOSE_EVANGELIST_TWICE)
    beside_pep = reweigh(planned(), BOTH_TIED, CHOSE_EVANGELIST_TWICE + ASSESS_THEN_DELIVER)

    assert percents(beside_pep) == percents(apest_alone)
    assert unrounded_shares(beside_pep)["apest"] == unrounded_shares(apest_alone)["apest"]
    assert outcomes(beside_pep) == {"apest": "top_changed", "pep": "level"}


def test_a_tied_framework_with_no_pairs_asked_is_left_as_sorted_with_no_outcome():
    """✨ A budget of one asks only APEST(d)'s first pair."""
    reweighted = reweigh(planned(budget=1), BOTH_TIED, CHOSE_EVANGELIST_TWICE[:1])

    assert outcomes(reweighted) == {"apest": "top_changed"}
    assert percents(reweighted, "pep") == percents(BOTH_TIED, "pep")


# ✨ With the placeholder bands, an even share of 16.67 makes Leading 20.83, Strong 17.5 and Present 14.17. APEST(d):
# Apostle 21 (Leading) and Prophet 20.5 (Strong) are too close to call, the rest Present; PEP is flat and not too
# close to call (18 is just over 5% more than 17). Not a generalist, for Apostle leads.
LEADING_ALONE = result([2100, 2050, 1475, 1475, 1450, 1450], [1800, 1700, 1650, 1650, 1600, 1600])


def results_pathway():
    """✨ A pathway with a tie-break and the wording its results page needs, generalist's and tie-break's."""
    pathway = planned()
    pathway.update(title="Results", instrument={"items": []})
    pathway["presentation"] = {
        key: value for key, value in with_a_tie_break()["presentation"].items() if key in ("generalist", "tie_break")
    }
    return pathway


def drawn(reweighted):
    """✨ The results page's APEST(d) for a re-weighted result, as `[(construct, standing), ...]` in its order, its
    tie-break wording and its generalist's."""
    page = results_page(results_pathway(), reweighted, {}, "Sam")
    apest = page["frameworks"][0]
    return [(bar["label"], bar["standing"]) for bar in apest["bars"]], apest["tie_break"], page["generalist"]


def drawn_after(answers):
    """✨ `drawn`, after the tie-break's `answers` on LEADING_ALONE."""
    return drawn(reweigh(results_pathway(), LEADING_ALONE, answers))


# ✨ One choice each shares 41.5 equally: 20.75 each, Strong, so every APEST(d) construct now stands between.
ONE_CHOICE_EACH = answered(("apostle", "prophet", "apostle"), ("apostle", "prophet", "prophet"))


def test_a_re_weighted_result_that_comes_out_flat_on_both_and_balanced_says_generalist_after_the_pairs():
    bars, said, generalist = drawn_after(ONE_CHOICE_EACH)

    assert said["heading"] == "Genuinely balanced"
    assert generalist == {"heading": "A generalist", "text": "Two flat profiles, even after your pairs."}
    assert bars[:2] == [("apostle", "Strong"), ("prophet", "Strong")]


def test_a_flat_result_beside_a_separated_outcome_never_says_generalist():
    """✨ Under the placeholder bands, choices that separate this framework leave it a Leading construct, so the
    outcome is set by hand on the flat result."""
    reweighted = reweigh(results_pathway(), LEADING_ALONE, ONE_CHOICE_EACH)
    reweighted["tie_break"] = [{"framework": "apest", "outcome": "same_top"}]

    _, said, generalist = drawn(reweighted)

    assert said["heading"] == "Separated"
    assert generalist is None


def test_a_separated_frameworks_standings_put_the_construct_it_names_first():
    """✨ Prophet chosen twice leads by just over 5% of 41.5: 21.26, Leading, to Apostle's 20.24, Strong."""
    bars, said, generalist = drawn_after(answered(("apostle", "prophet", "prophet"), ("apostle", "prophet", "prophet")))

    assert said["text"] == "The top changed."
    assert generalist is None
    assert bars[:2] == [("prophet", "Leading"), ("apostle", "Strong")]


def with_a_tie_break(**settings):
    """✨ The test pathway with a tie-break, its statements and its wording."""
    return tests.documents.with_a_tie_break(sort_pathway(), **settings)


def test_a_pathway_may_set_the_percentage_and_cluster_size_and_word_the_generalist():
    assert validate(with_a_tie_break(percent=2.5, cluster=2)) == []


@pytest.mark.parametrize(
    "setting, value",
    [
        ("percent", -1),
        ("percent", 101),
        ("percent", "5"),
        ("cluster", 1),
        ("cluster", "4"),
        # ✨ Every tied framework gets a pair, two when both are tied (ADR 0018).
        ("budget", 0),
        ("budget", 1),
    ],
)
def test_a_percentage_or_cluster_size_that_could_not_work_is_refused_where_it_is(setting, value):
    problems = validate(with_a_tie_break(**{setting: value}))

    assert [problem.path for problem in problems] == [f"/measurement/tie_break/{setting}"]


def test_a_tie_break_without_the_generalists_wording_is_refused():
    pathway = with_a_tie_break()
    del pathway["presentation"]["generalist"]

    assert [problem.path for problem in validate(pathway)] == ["/measurement/tie_break"]


def test_a_tie_break_needs_three_statements_for_every_construct():
    missing = with_a_tie_break()
    del missing["measurement"]["tie_break"]["statements"]["ponder"]
    too_few = with_a_tie_break()
    too_few["measurement"]["tie_break"]["statements"]["apostle"].pop()

    assert [problem.path for problem in validate(missing)] == ["/measurement/tie_break/statements"]
    assert [problem.path for problem in validate(too_few)] == ["/measurement/tie_break/statements/apostle"]


def test_a_tie_break_without_the_pairs_wording_is_refused():
    pathway = with_a_tie_break()
    del pathway["presentation"]["tie_break"]

    assert [problem.path for problem in validate(pathway)] == ["/measurement/tie_break"]
