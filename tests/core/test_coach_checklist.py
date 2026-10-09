# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The coach checklist's outcome rule, and what it reads from a form, at the seam the spec asks for: no browser
and no database.

The questions, which are critical and why each matters are authored in the pathway document; the rule that turns
six answers into an outcome is the engine's (ADR 0003), as the content owner's mock-up sets it out:

    any critical No            → stop
    two or more Nos            → stop
    three or more not Yes      → stop
    one soft No, or 1–2 unsure → confirm (a second thought)
    all Yes                    → proceed
"""

import pytest

from engine.document import AnswerRefused
from engine.document.coach import Outcome, candidate_name_from_form, checklist_answers_from_form, checklist_outcome

QUESTIONS = [
    {"id": "faith", "critical": True},
    {"id": "knowsYou"},
    {"id": "objectivity", "critical": True},
    {"id": "wisdom", "critical": False},
    {"id": "coaching", "critical": True},
    {"id": "time"},
]
ALL_YES = {question["id"]: "yes" for question in QUESTIONS}


def answered(**changes):
    return {**ALL_YES, **changes}


# The outcome


def test_all_yes_proceeds_and_names_nothing():
    assert checklist_outcome(QUESTIONS, ALL_YES) == Outcome("proceed", [])


@pytest.mark.parametrize(
    "changes, flagged",
    [
        ({"knowsYou": "no"}, ["knowsYou"]),
        ({"time": "no"}, ["time"]),
        ({"faith": "maybe"}, ["faith"]),
        ({"wisdom": "maybe", "coaching": "maybe"}, ["wisdom", "coaching"]),
        ({"time": "no", "objectivity": "maybe"}, ["objectivity", "time"]),
    ],
)
def test_one_soft_no_or_one_or_two_not_sures_ask_for_a_second_thought(changes, flagged):
    """✨ A critical question answered "not sure" is a pause, not a stop: only a critical No is non-negotiable."""
    assert checklist_outcome(QUESTIONS, answered(**changes)) == Outcome("confirm", flagged)


@pytest.mark.parametrize("critical", ["faith", "objectivity", "coaching"])
def test_a_no_to_any_critical_question_stops_on_its_own(critical):
    assert checklist_outcome(QUESTIONS, answered(**{critical: "no"})) == Outcome("stop", [critical])


def test_two_nos_stop_even_when_neither_is_critical():
    assert checklist_outcome(QUESTIONS, answered(knowsYou="no", time="no")) == Outcome("stop", ["knowsYou", "time"])


def test_three_answers_that_are_not_yes_stop_even_with_no_no_among_them():
    outcome = checklist_outcome(QUESTIONS, answered(faith="maybe", wisdom="maybe", time="maybe"))

    assert outcome == Outcome("stop", ["faith", "wisdom", "time"])


def test_a_stop_names_every_answer_that_was_not_yes_in_the_authored_order():
    """✨ As the mock-up does: a critical No stops, and the not-sures beside it are named too."""
    outcome = checklist_outcome(QUESTIONS, answered(time="maybe", coaching="no", knowsYou="maybe"))

    assert outcome == Outcome("stop", ["knowsYou", "coaching", "time"])


def test_whether_a_stop_came_from_a_critical_no_is_told_apart():
    """✨ The stop screen leads differently for a critical No ("something that isn't really negotiable")."""
    assert checklist_outcome(QUESTIONS, answered(faith="no")).critical_no is True
    assert checklist_outcome(QUESTIONS, answered(knowsYou="no", time="no")).critical_no is False


def test_a_question_is_soft_unless_it_is_marked_critical():
    questions = [{"id": "faith"}, {"id": "time"}]

    assert checklist_outcome(questions, {"faith": "no", "time": "yes"}) == Outcome("confirm", ["faith"])


# Reading the form


def test_the_answers_are_read_by_question_and_nothing_else_is_kept():
    posted = {f"answer-{question_id}": "yes" for question_id in ALL_YES} | {"answer-time": "maybe", "name": "Sam"}

    assert checklist_answers_from_form(QUESTIONS, posted) == answered(time="maybe")


def test_every_question_must_be_answered_to_continue():
    posted = {f"answer-{question_id}": "yes" for question_id in ALL_YES if question_id != "wisdom"}

    with pytest.raises(AnswerRefused, match="Answer all six questions to continue."):
        checklist_answers_from_form(QUESTIONS, posted)


def test_how_many_questions_there_are_is_counted_from_the_authored_list():
    questions = [{"id": "faith"}, {"id": "wisdom"}, {"id": "time"}]

    with pytest.raises(AnswerRefused, match="Answer all three questions to continue."):
        checklist_answers_from_form(questions, {"answer-faith": "yes"})


@pytest.mark.parametrize("value", ["", "Yes", "perhaps", "true"])
def test_an_answer_that_is_not_yes_not_sure_or_no_is_refused(value):
    posted = {f"answer-{question_id}": "yes" for question_id in ALL_YES} | {"answer-faith": value}

    with pytest.raises(AnswerRefused, match="Answer all six questions to continue."):
        checklist_answers_from_form(QUESTIONS, posted)


def test_the_candidates_first_name_is_trimmed():
    assert candidate_name_from_form({"name": "  Sam "}) == "Sam"


@pytest.mark.parametrize("posted", [{}, {"name": ""}, {"name": "   "}])
def test_a_first_name_is_needed_to_continue(posted):
    with pytest.raises(AnswerRefused, match="Add their first name to continue."):
        candidate_name_from_form(posted)


def test_a_first_name_longer_than_a_contacts_is_refused():
    """✨ The chosen candidate becomes the coach's contact, whose name is kept to 150 characters."""
    assert candidate_name_from_form({"name": "S" * 150}) == "S" * 150

    with pytest.raises(AnswerRefused, match="That name is too long."):
        candidate_name_from_form({"name": "S" * 151})
