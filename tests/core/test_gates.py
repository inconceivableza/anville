# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Gate clauses, at the seam the spec asks for: no browser and no database.

A gate is a list of clauses from a fixed set, never an expression (ADR 0003). Every clause must pass
before a section may be completed, and each failing clause contributes its own authored message.
"""

import pytest

from engine.document import checklist, gate_passes, unmet
from engine.document.gates import comparison_visit_key, links_issued_key


def section_gated_by(*clauses):
    return {"id": "s", "title": "A section", "blocks": [], "gate": {"clauses": list(clauses)}}


def clause(type, message="Not yet.", **parameters):
    return {"type": type, "message": message, **parameters}


# A section with no gate


def test_a_section_with_no_gate_can_be_completed():
    assert gate_passes({"id": "s", "title": "A section", "blocks": []}, {}) is True


def test_a_section_with_an_empty_list_of_clauses_can_be_completed():
    assert unmet(section_gated_by(), {}) == []


# has_answer


@pytest.mark.parametrize("answer", ["Something written", 1, 10, 0, ["an entry"], {"a": "b"}])
def test_has_answer_passes_when_the_block_has_been_answered(answer):
    section = section_gated_by(clause("has_answer", block="statement"))

    assert unmet(section, {"statement": answer}) == []


@pytest.mark.parametrize("answers", [{}, {"statement": None}, {"statement": ""}, {"statement": "   "}, {"statement": []}])
def test_has_answer_fails_when_the_block_holds_nothing(answers):
    section = section_gated_by(clause("has_answer", block="statement", message="Answer this first."))

    assert unmet(section, answers) == ["Answer this first."]


def test_an_answer_to_another_block_does_not_satisfy_the_clause():
    section = section_gated_by(clause("has_answer", block="statement", message="Answer this first."))

    assert unmet(section, {"elsewhere": "Written"}) == ["Answer this first."]


# min_text_length


@pytest.mark.parametrize("answer", ["1234567890", "a longer answer than that"])
def test_min_text_length_passes_at_or_beyond_the_minimum(answer):
    section = section_gated_by(clause("min_text_length", block="statement", min=10))

    assert unmet(section, {"statement": answer}) == []


@pytest.mark.parametrize("answer", ["", "too short", "   too short   "])
def test_min_text_length_fails_below_the_minimum_and_does_not_count_surrounding_space(answer):
    section = section_gated_by(clause("min_text_length", block="statement", min=10, message="Write at least ten."))

    assert unmet(section, {"statement": answer}) == ["Write at least ten."]


def test_min_text_length_fails_when_there_is_no_answer_at_all():
    section = section_gated_by(clause("min_text_length", block="statement", min=10, message="Write at least ten."))

    assert unmet(section, {}) == ["Write at least ten."]


# entry_count


def test_entry_count_passes_at_or_beyond_the_minimum():
    section = section_gated_by(clause("entry_count", block="markers", min=3))

    assert unmet(section, {"markers": [{"text": "a"}, {"text": "b"}, {"text": "c"}]}) == []


@pytest.mark.parametrize("answers", [{}, {"markers": []}, {"markers": [{"text": "a"}, {"text": "b"}]}])
def test_entry_count_fails_below_the_minimum(answers):
    section = section_gated_by(clause("entry_count", block="markers", min=3, message="Add at least three."))

    assert unmet(section, answers) == ["Add at least three."]


def test_entry_count_counts_every_entry_unless_the_author_asked_for_only_those_with_content():
    """✨ A widget that seeds blank rows would otherwise satisfy a count nobody has filled in."""
    seeded_blank = {"contacts": [{"name": "Someone"}, {"name": ""}, {"name": "   "}]}
    counting_all = section_gated_by(clause("entry_count", block="contacts", min=3))
    counting_filled = section_gated_by(clause("entry_count", block="contacts", min=3, only_with_content=True))

    assert unmet(counting_all, seeded_blank) == []
    assert unmet(counting_filled, seeded_blank) == ["Not yet."]


@pytest.mark.parametrize("answers", [{}, {"contacts": []}, {"contacts": [{"name": "Jo"}, {"name": "Priya"}]}])
def test_entry_count_may_allow_none_at_all_as_well_as_the_minimum(answers):
    """✨ A list a participant may skip: empty, or at least the minimum, but never a start left short."""
    section = section_gated_by(clause("entry_count", block="contacts", min=2, allow_none=True))

    assert unmet(section, answers) == []


def test_entry_count_allowing_none_still_fails_between_none_and_the_minimum():
    section = section_gated_by(clause("entry_count", block="contacts", min=2, allow_none=True, message="Two, or none."))

    assert unmet(section, {"contacts": [{"name": "Jo"}]}) == ["Two, or none."]


def test_an_entry_has_content_when_any_one_of_its_fields_does():
    section = section_gated_by(clause("entry_count", block="roles", min=2, only_with_content=True))

    assert unmet(section, {"roles": [{"title": "", "daily": "A Tuesday"}, {"title": "Teacher", "daily": ""}]}) == []


# distinct_value_count


def test_distinct_value_count_counts_the_different_values_of_a_field_not_the_entries():
    section = section_gated_by(clause("distinct_value_count", block="ideas", field="lens", min=2))
    one_lens = {"ideas": [{"lens": "who"}, {"lens": "who"}, {"lens": "who"}]}
    two_lenses = {"ideas": [{"lens": "who"}, {"lens": "who"}, {"lens": "wild"}]}

    assert unmet(section, one_lens) == ["Not yet."]
    assert unmet(section, two_lenses) == []


@pytest.mark.parametrize("answers", [{}, {"ideas": []}, {"ideas": [{"lens": ""}, {"lens": None}, {}]}])
def test_distinct_value_count_ignores_entries_with_nothing_in_that_field(answers):
    section = section_gated_by(clause("distinct_value_count", block="ideas", field="lens", min=1, message="Pick a lens."))

    assert unmet(section, answers) == ["Pick a lens."]


# every_entry_has


def test_every_entry_has_passes_when_every_entry_carries_a_value_for_the_field():
    section = section_gated_by(clause("every_entry_has", block="markers", field="chapter"))

    assert unmet(section, {"markers": [{"chapter": "childhood"}, {"chapter": "first-job"}]}) == []


@pytest.mark.parametrize("entry", [{"chapter": ""}, {"chapter": None}, {}])
def test_every_entry_has_fails_when_one_entry_is_missing_that_value(entry):
    section = section_gated_by(clause("every_entry_has", block="markers", field="chapter", message="File them all."))

    assert unmet(section, {"markers": [{"chapter": "childhood"}, entry]}) == ["File them all."]


@pytest.mark.parametrize("answers", [{}, {"markers": []}])
def test_every_entry_has_is_satisfied_by_no_entries_at_all(answers):
    """✨ "Every" over nothing is true, so an author pairs this clause with a count of entries."""
    section = section_gated_by(clause("every_entry_has", block="markers", field="chapter"))

    assert unmet(section, answers) == []


# comparison_visited


def test_comparison_visited_passes_only_once_the_comparison_has_been_visited_not_on_the_sort_alone():
    section = section_gated_by(clause("comparison_visited", block="strengths-sort", message="View the comparison."))
    sorted_only = {"strengths-sort": {"a1": {"bucket": "strength", "value": 85}}}
    visited = {**sorted_only, comparison_visit_key("strengths-sort"): "2026-10-02T10:00:00+00:00"}

    assert unmet(section, sorted_only) == ["View the comparison."]
    assert unmet(section, visited) == []


# links_issued


@pytest.mark.parametrize("issued, passes", [(None, False), (0, False), (1, False), (2, True), (3, True)])
def test_links_issued_passes_once_enough_of_the_blocks_people_hold_a_working_link(issued, passes):
    """✨ The people named are not enough: it counts the working links, which is all a participant can be seen to do."""
    section = section_gated_by(clause("links_issued", block="contacts", min=2, message="Send two links."))
    named = [{"name": f"Person {n}", "email": f"person{n}@example.com", "id": n} for n in range(3)]
    answers = {"contacts": named} if issued is None else {"contacts": named, links_issued_key("contacts"): issued}

    assert unmet(section, answers) == ([] if passes else ["Send two links."])


# Combinations, and a message for each failing clause


def test_a_gate_combines_its_clauses_and_all_of_them_must_pass():
    """✨ The prototype's timeline gate, which is the widest combination the workbook uses."""
    section = section_gated_by(
        clause("entry_count", block="chapters", min=3, message="Add at least three chapters."),
        clause("entry_count", block="markers", min=5, message="Add at least five markers."),
        clause("distinct_value_count", block="markers", field="type", min=3, message="Use at least three kinds."),
        clause("every_entry_has", block="markers", field="chapter", message="File every marker in a chapter."),
        clause("min_text_length", block="threads", min=10, message="Write about the threads you see."),
    )
    complete = {
        "chapters": [{"label": "a"}, {"label": "b"}, {"label": "c"}],
        "markers": [
            {"type": "door", "chapter": "a"},
            {"type": "door", "chapter": "a"},
            {"type": "closed", "chapter": "b"},
            {"type": "fruit", "chapter": "b"},
            {"type": "fruit", "chapter": "c"},
        ],
        "threads": "The same thread keeps returning.",
    }

    assert unmet(section, complete) == []
    assert gate_passes(section, complete) is True


def test_every_failing_clause_contributes_its_own_message_in_the_order_it_was_authored():
    section = section_gated_by(
        clause("entry_count", block="chapters", min=3, message="Add at least three chapters."),
        clause("entry_count", block="markers", min=5, message="Add at least five markers."),
        clause("distinct_value_count", block="markers", field="type", min=3, message="Use at least three kinds."),
        clause("every_entry_has", block="markers", field="chapter", message="File every marker in a chapter."),
    )

    assert unmet(section, {"chapters": [{"label": "a"}], "markers": [{"type": "door"}]}) == [
        "Add at least three chapters.",
        "Add at least five markers.",
        "Use at least three kinds.",
        "File every marker in a chapter.",
    ]


def test_only_the_failing_clauses_say_anything():
    section = section_gated_by(
        clause("has_answer", block="statement", message="Write a statement."),
        clause("min_text_length", block="statement", min=40, message="Say a little more."),
    )

    assert unmet(section, {"statement": "Short."}) == ["Say a little more."]
    assert gate_passes(section, {"statement": "Short."}) is False


def test_clauses_that_share_a_message_say_it_once():
    """✨ Four after-ratings are four clauses and one sentence; the participant should read it once."""
    section = section_gated_by(
        *[clause("has_answer", block=f"after-{n}", message="Answer all four to continue.") for n in range(1, 5)]
    )

    assert unmet(section, {}) == ["Answer all four to continue."]
    assert unmet(section, {"after-1": 5, "after-2": 5, "after-3": 5}) == ["Answer all four to continue."]
    assert unmet(section, {f"after-{n}": 5 for n in range(1, 5)}) == []


def test_clauses_that_are_worded_differently_each_still_speak():
    section = section_gated_by(
        clause("has_answer", block="letter", message="Write your letter."),
        clause("has_answer", block="after-1", message="Answer all four to continue."),
        clause("has_answer", block="after-2", message="Answer all four to continue."),
    )

    assert unmet(section, {}) == ["Write your letter.", "Answer all four to continue."]


def test_a_clause_message_may_be_worded_per_role():
    section = section_gated_by({"type": "has_answer", "block": "statement", "message": {"participant": "Write yours."}})

    assert unmet(section, {}) == ["Write yours."]


# The checklist beneath "Mark complete": every message, met or not, so nothing comes and goes as answers change


def test_the_checklist_lists_every_message_in_the_order_authored_with_whether_it_is_met():
    section = section_gated_by(
        clause("has_answer", block="letter", message="Write your letter."),
        clause("has_answer", block="rating", message="Answer the rating."),
    )

    assert checklist(section, {"rating": 5}) == [("Write your letter.", False), ("Answer the rating.", True)]


def test_a_message_several_clauses_share_is_listed_once_and_met_only_when_all_of_them_pass():
    section = section_gated_by(
        *[clause("has_answer", block=f"after-{n}", message="Answer all four to continue.") for n in range(1, 5)]
    )

    assert checklist(section, {"after-1": 5, "after-2": 5, "after-3": 5}) == [("Answer all four to continue.", False)]
    assert checklist(section, {f"after-{n}": 5 for n in range(1, 5)}) == [("Answer all four to continue.", True)]


def test_a_section_with_no_gate_has_nothing_to_list():
    assert checklist({"id": "s", "title": "A section", "blocks": []}, {}) == []
