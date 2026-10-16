# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whether a participant's sort leaves a framework's leaders too close to call (ticket 30a): from a stored result and
the pathway document alone, with no request or database."""

import pytest

import tests.documents
from engine.document import validate
from engine.document.tie_break import pair_plan, tie_break
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


def framework(framework_id, constructs, percents):
    """✨ One framework of a stored result, ranked as scoring ranks it: by percent, ties in declaration order."""
    scored = [{"construct": c, "raw": p, "percent": p} for c, p in zip(constructs, percents)]
    scored.sort(key=lambda construct: -construct["percent"])
    return {"framework": framework_id, "constructs": scored}


def result(apest, pep):
    return {"method": "compositional_share", "frameworks": [framework("apest", APEST, apest), framework("pep", PEP, pep)]}


CLEAR_APEST = [9, 34, 8, 14, 24, 11]  # ✨ the prototype's "Both clear"
CLEAR_PEP = [8, 33, 12, 10, 11, 26]


def test_a_construct_four_points_behind_the_leader_ties_with_it_and_one_five_behind_does_not():
    four_behind = result([10, 30, 26, 10, 14, 10], CLEAR_PEP)
    five_behind = result([10, 30, 25, 10, 15, 10], CLEAR_PEP)

    assert tie_break(document(), four_behind)["tied"] == {"apest": ["prophet", "evangelist"]}
    assert tie_break(document(), five_behind)["tied"] == {}


def test_at_most_the_top_four_enter_the_tie_break():
    """✨ The prototype's "Both flat" APEST: all six within a point, so only the first four as ranked go on."""
    flat = result([17, 17, 16, 17, 16, 17], CLEAR_PEP)

    assert tie_break(document(), flat)["tied"] == {"apest": ["apostle", "prophet", "shepherd", "deacon"]}


def test_tied_on_exactly_one_framework_marks_the_participant_for_the_tie_break():
    only_role_tied = result([13, 26, 9, 25, 16, 11], CLEAR_PEP)  # ✨ the prototype's "Only role tied"

    assert tie_break(document(), only_role_tied)["outcome"] == "tie_break"


def test_tied_on_both_frameworks_is_a_generalist():
    both_tied = result([21, 20, 11, 22, 14, 12], [12, 22, 21, 10, 13, 22])  # ✨ the prototype's "Both tied at top"

    assert tie_break(document(), both_tied)["outcome"] == "generalist"


def test_tied_on_neither_framework_leaves_nothing_to_break():
    assert tie_break(document(), result(CLEAR_APEST, CLEAR_PEP)) == {"tied": {}, "outcome": None}


def test_the_threshold_and_cluster_size_come_from_the_document():
    four_behind = result([10, 30, 26, 27, 14, 10], CLEAR_PEP)

    assert tie_break(document(threshold=3), four_behind)["tied"] == {"apest": ["prophet", "shepherd"]}
    assert tie_break(document(threshold=4, cluster=2), four_behind)["tied"] == {"apest": ["prophet", "shepherd"]}
    assert tie_break(document(threshold=4, cluster=3), four_behind)["tied"] == {
        "apest": ["prophet", "shepherd", "evangelist"]
    }


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


def with_a_tie_break(**settings):
    """✨ The test pathway with a tie-break, its statements and its wording."""
    return tests.documents.with_a_tie_break(sort_pathway(), **settings)


def test_a_pathway_may_set_the_threshold_and_cluster_size_and_word_the_generalist():
    assert validate(with_a_tie_break(threshold=3, cluster=2)) == []


@pytest.mark.parametrize(
    "setting, value",
    [("threshold", -1), ("threshold", 2.5), ("threshold", 101), ("cluster", 1), ("cluster", "4")],
)
def test_a_threshold_or_cluster_size_that_could_not_work_is_refused_where_it_is(setting, value):
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
