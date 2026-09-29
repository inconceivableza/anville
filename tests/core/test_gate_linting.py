"""✨ A gate clause an author writes must be one the engine could actually check when the participant gets there.

Both checks were carried from ticket 02, where the linter checked only that the named block existed.
"""

import pytest

from engine.document import Problem, validate
from tests.documents import pathway_document

CLAUSE_PATH = "/content/sections/1/gate/clauses/0"


def document_whose_gate_names(clause):
    document = pathway_document()
    document["content"]["sections"][1]["gate"]["clauses"] = [clause]
    return document


def test_a_clause_about_what_an_answer_holds_may_not_name_a_block_in_another_section():
    """✨ Whether another section's text is long enough, or has enough entries, is for that section's own gate."""
    document = document_whose_gate_names(
        {"type": "min_text_length", "block": "elsewhere", "min": 10, "message": "Write more."}
    )
    document["content"]["sections"][0]["blocks"].append(
        {"id": "elsewhere", "type": "long_text", "prompt": "A question in the first section."}
    )

    assert validate(document) == [
        Problem(
            path=f"{CLAUSE_PATH}/block",
            message="Block 'elsewhere' is in another section; only a 'has_answer' clause may name a block outside its own section.",
        )
    ]


def test_has_answer_may_name_a_block_in_another_section():
    """✨ Ticket 09: Section 1 may not be completed until the sort, in a section of its own, has an answer."""
    document = document_whose_gate_names({"type": "has_answer", "block": "baseline-bible", "message": "Rate this first."})

    assert validate(document) == []


def test_has_answer_in_another_section_still_needs_a_block_that_captures_an_answer():
    document = document_whose_gate_names({"type": "has_answer", "block": "welcome", "message": "Read this first."})

    assert validate(document) == [
        Problem(
            path=f"{CLAUSE_PATH}/block",
            message="A 'has_answer' clause cannot be checked against block 'welcome', which is a rich_text.",
        )
    ]


def test_a_clause_naming_a_block_that_exists_nowhere_is_still_reported_as_missing():
    document = document_whose_gate_names(
        {"type": "min_text_length", "block": "nowhere", "min": 10, "message": "Write more."}
    )

    assert validate(document) == [
        Problem(path=f"{CLAUSE_PATH}/block", message="There is no block 'nowhere' in this pathway.")
    ]


def test_a_minimum_text_length_cannot_be_asked_of_a_block_that_captures_no_text():
    document = document_whose_gate_names(
        {"type": "min_text_length", "block": "scale-here", "min": 10, "message": "Write more."}
    )
    document["content"]["sections"][1]["blocks"].append(
        {
            "id": "scale-here",
            "type": "agreement_scale",
            "prompt": "Rate this.",
            "min_label": "Low",
            "max_label": "High",
        }
    )

    assert validate(document) == [
        Problem(
            path=f"{CLAUSE_PATH}/block",
            message="A 'min_text_length' clause cannot be checked against block 'scale-here', which is an agreement_scale.",
        )
    ]


def test_a_clause_cannot_be_asked_of_a_block_that_captures_nothing_at_all():
    document = document_whose_gate_names({"type": "has_answer", "block": "intro", "message": "Answer this."})
    document["content"]["sections"][1]["blocks"].append({"id": "intro", "type": "rich_text", "body": "Some prose."})

    assert validate(document) == [
        Problem(
            path=f"{CLAUSE_PATH}/block",
            message="A 'has_answer' clause cannot be checked against block 'intro', which is a rich_text.",
        )
    ]


@pytest.mark.parametrize(
    "clause",
    [
        {"type": "entry_count", "block": "statement", "min": 3, "message": "Add three."},
        {"type": "distinct_value_count", "block": "statement", "field": "lens", "min": 2, "message": "Vary them."},
        {"type": "every_entry_has", "block": "statement", "field": "chapter", "message": "File them all."},
    ],
)
def test_a_clause_about_entries_cannot_be_asked_of_a_block_that_captures_text(clause):
    assert validate(document_whose_gate_names(clause)) == [
        Problem(
            path=f"{CLAUSE_PATH}/block",
            message=f"A '{clause['type']}' clause cannot be checked against block 'statement', which is a long_text.",
        )
    ]


def test_a_count_of_entries_may_be_asked_of_a_contact_list():
    document = document_whose_gate_names({"type": "entry_count", "block": "people", "min": 2, "message": "Add two."})
    document["content"]["sections"][1]["blocks"].append({"id": "people", "type": "contact_list"})

    assert validate(document) == []


def test_a_minimum_text_length_cannot_be_asked_of_a_contact_list():
    document = document_whose_gate_names({"type": "min_text_length", "block": "people", "min": 2, "message": "More."})
    document["content"]["sections"][1]["blocks"].append({"id": "people", "type": "contact_list"})

    assert validate(document) == [
        Problem(
            path=f"{CLAUSE_PATH}/block",
            message="A 'min_text_length' clause cannot be checked against block 'people', which is a contact_list.",
        )
    ]


def test_a_gate_cannot_ask_anything_of_a_coach_checklist_since_none_of_it_is_kept():
    """✨ The checklist's answers are never stored (ticket 10a), and choosing a coach may be skipped, so no gate
    can wait on it."""
    document = document_whose_gate_names({"type": "has_answer", "block": "coach", "message": "Choose a coach."})
    document["content"]["sections"][1]["blocks"].append(
        {
            "id": "coach",
            "type": "coach_checklist",
            "heading": "Walking with a coach",
            "name_prompt": "Who are you thinking of asking?",
            "questions": [{"id": "faith", "question": "Shares your faith", "why": "It is rooted in scripture."}],
        }
    )

    assert validate(document) == [
        Problem(
            path=f"{CLAUSE_PATH}/block",
            message="A 'has_answer' clause cannot be checked against block 'coach', which is a coach_checklist.",
        )
    ]


def test_has_answer_may_be_asked_of_any_block_that_captures_an_answer():
    document = document_whose_gate_names({"type": "has_answer", "block": "statement", "message": "Answer this."})

    assert validate(document) == []


def test_a_gate_may_combine_clauses_of_different_types_over_different_blocks_in_its_section():
    document = document_whose_gate_names({"type": "min_text_length", "block": "statement", "min": 10, "message": "More."})
    document["content"]["sections"][1]["blocks"].append(
        {"id": "how-clear", "type": "agreement_scale", "prompt": "Clear?", "min_label": "No", "max_label": "Yes"}
    )
    document["content"]["sections"][1]["gate"]["clauses"].append(
        {"type": "has_answer", "block": "how-clear", "message": "Rate how clear it is."}
    )

    assert validate(document) == []
