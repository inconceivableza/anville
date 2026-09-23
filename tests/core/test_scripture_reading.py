"""✨ The scripture reading block: authored passages, and a confirmation that opens the activity beneath it."""

import pytest

from engine.document import AnswerRefused, answer_from_form, answerable_block, authored_text, validate
from tests.documents import pathway_document, scripture_reading


def document_with_a_reading(**fields):
    document = pathway_document()
    document["content"]["sections"][1]["blocks"].insert(0, scripture_reading(**fields))
    return document


def test_a_reading_needs_at_least_one_passage_and_each_passage_a_reference_and_its_text():
    assert validate(document_with_a_reading()) == []

    [problem] = validate(document_with_a_reading(passages=[]))
    assert problem.path == "/content/sections/1/blocks/0/passages"

    [problem] = validate(document_with_a_reading(passages=[{"reference": "1 Corinthians 12"}]))
    assert problem.path == "/content/sections/1/blocks/0/passages/0"
    assert "'text' is a required property" in problem.message


def test_a_readings_note_and_confirm_label_are_optional():
    document = document_with_a_reading()
    del document["content"]["sections"][1]["blocks"][0]["note"]
    del document["content"]["sections"][1]["blocks"][0]["confirm_label"]

    assert validate(document) == []


def test_a_passage_is_worded_per_role_like_any_other_authored_text():
    block = scripture_reading(
        passages=[
            {
                "reference": "1 Corinthians 12:4-11",
                "text": {"participant": "gifts given to you", "observer": "gifts given to them"},
            }
        ]
    )

    assert authored_text(block, "participant")["passages"] == [
        {"reference": "1 Corinthians 12:4-11", "text": "gifts given to you"}
    ]
    assert authored_text(block, "observer")["passages"] == [
        {"reference": "1 Corinthians 12:4-11", "text": "gifts given to them"}
    ]


def test_a_reading_captures_the_participants_confirmation():
    block = answerable_block(document_with_a_reading(), "reading")

    assert answer_from_form(block, "true") is True


@pytest.mark.parametrize("submitted", ["false", "", "no", "1", "maybe"])
def test_nothing_but_a_confirmation_is_accepted_as_an_answer_to_a_reading(submitted):
    """✨ A reading is confirmed or not yet confirmed; there is no third state for the server to store."""
    block = answerable_block(document_with_a_reading(), "reading")

    with pytest.raises(AnswerRefused):
        answer_from_form(block, submitted)


def test_a_reading_can_be_what_a_gate_requires():
    document = document_with_a_reading()
    document["content"]["sections"][1]["gate"]["clauses"].append(
        {"type": "has_answer", "block": "reading", "message": "Confirm you have read the passages."}
    )

    assert validate(document) == []
