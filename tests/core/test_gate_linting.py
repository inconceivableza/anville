# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A gate clause an author writes must be one the engine could actually check when the participant gets there.

Both checks were carried from ticket 02, where the linter checked only that the named block existed.
"""

import pytest

from engine.document import Problem, validate
from tests.documents import pathway_document, sort_pathway

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
            message=(
                "Block 'elsewhere' is in another section; "
                "only a 'has_answer', 'comparison_visited' or 'links_issued' clause may name a block outside its "
                "own section."
            ),
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


# Opening conditions (ADR 0019)

A_COACH_CHECKLIST = {
    "id": "coach",
    "type": "coach_checklist",
    "heading": "Walking with a coach",
    "name_prompt": "Who are you thinking of asking?",
    "questions": [{"id": "faith", "question": "Shares your faith", "why": "It is rooted in scripture."}],
}


def document_whose_section_opens_when(clause):
    """✨ The test pathway with a coach checklist in onboarding, and the calling section opening on `clause`."""
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].append(A_COACH_CHECKLIST)
    document["content"]["sections"][1]["opens_when"] = {"clauses": [clause]}
    return document


def test_an_opening_condition_must_be_a_clause_from_the_fixed_set():
    document = document_whose_section_opens_when({"type": "coach_is_free", "block": "coach", "message": "Wait."})

    assert [problem.path for problem in validate(document)] == ["/content/sections/1/opens_when/clauses/0/type"]


def test_coach_accepted_must_name_a_coach_checklist_and_may_name_one_in_another_section():
    accepted = {"type": "coach_accepted", "block": "coach", "message": "Opens once your coach has accepted."}
    assert validate(document_whose_section_opens_when(accepted)) == []

    document = document_whose_section_opens_when({**accepted, "block": "statement"})

    assert validate(document) == [
        Problem(
            path="/content/sections/1/opens_when/clauses/0/block",
            message="A 'coach_accepted' clause cannot be checked against block 'statement', which is a long_text.",
        )
    ]


def test_has_answer_may_be_asked_of_any_block_that_captures_an_answer():
    document = document_whose_gate_names({"type": "has_answer", "block": "statement", "message": "Answer this."})

    assert validate(document) == []


def test_a_comparison_visited_clause_may_name_the_sort_in_another_section_but_no_block_that_is_not_scored():
    """✨ Ticket 16c: Section 1 waits on a visit to the comparison of a sort in a section of its own."""
    document = sort_pathway()
    document["content"]["sections"][1]["gate"]["clauses"] = [
        {"type": "comparison_visited", "block": "strengths-sort", "message": "View the comparison."},
        {"type": "comparison_visited", "block": "statement", "message": "View the comparison."},
    ]

    assert validate(document) == [
        Problem(
            path="/content/sections/1/gate/clauses/1/block",
            message="A 'comparison_visited' clause cannot be checked against block 'statement', which is a long_text.",
        )
    ]


# The number of people a links_issued clause needs, written once (ticket 81)


def with_voices(message="Add at least {min} people.", to_finish="added at least {min} people in {title}", gate=True):
    """✨ The test pathway with a section after onboarding holding a contact list, as Five trusted voices does, its
    `links_issued` clause asking for three people (left out without a `gate`), and with `to_finish`."""
    document = pathway_document()
    clause = {"type": "links_issued", "block": "contacts", "min": 3, "message": message}
    document["content"]["sections"].append(
        {
            "id": "voices",
            "title": "Five trusted voices",
            "requires": ["onboarding"],
            "to_finish": to_finish,
            "blocks": [{"id": "contacts", "type": "contact_list"}],
            **({"gate": {"clauses": [clause]}} if gate else {}),
        }
    )
    return document


@pytest.mark.parametrize(
    "fields, path",
    [
        ({"message": "Add at least 4 people."}, "/content/sections/2/gate/clauses/0/message"),
        ({"to_finish": "added at least 4 people in {title}"}, "/content/sections/2/to_finish"),
        (
            {"to_finish": {"participant": "added at least {min} people in {title}", "observer": "added 4"}},
            "/content/sections/2/to_finish/observer",
        ),
    ],
    ids=["in the message", "in the phrase", "in one role's phrase"],
)
def test_a_number_other_than_the_links_issued_minimum_is_refused_where_it_is_written(fields, path):
    assert validate(with_voices(**fields)) == [
        Problem(path, "This says 4 where the section's 'links_issued' clause asks for 3; write {min} for its minimum.")
    ]


def test_a_phrase_may_write_min_only_in_a_section_with_one_links_issued_clause():
    assert validate(with_voices(gate=False)) == [
        Problem(
            "/content/sections/2/to_finish",
            "{min} is the minimum of the section's own 'links_issued' clause, and this section has none, or more "
            "than one.",
        )
    ]


def test_a_gate_may_combine_clauses_of_different_types_over_different_blocks_in_its_section():
    document = document_whose_gate_names({"type": "min_text_length", "block": "statement", "min": 10, "message": "More."})
    document["content"]["sections"][1]["blocks"].append(
        {"id": "how-clear", "type": "agreement_scale", "prompt": "Clear?", "min_label": "No", "max_label": "Yes"}
    )
    document["content"]["sections"][1]["gate"]["clauses"].append(
        {"type": "has_answer", "block": "how-clear", "message": "Rate how clear it is."}
    )

    assert validate(document) == []
