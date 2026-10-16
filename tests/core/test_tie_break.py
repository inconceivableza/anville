# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whether a participant's sort leaves a framework's leaders too close to call (ticket 30a): from a stored result and
the pathway document alone, with no request or database."""

from engine.document.tie_break import tie_break

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
