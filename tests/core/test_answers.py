import pytest

from engine.document import AnswerRefused, UnknownBlock, answer_from_form, answerable_block
from tests.documents import pathway_document


def test_a_long_text_answer_is_kept_exactly_as_written():
    block = answerable_block(pathway_document(), "statement")

    assert answer_from_form(pathway_document(), block, "  To serve <people>\n& build.  ") == "  To serve <people>\n& build.  "


def test_a_long_text_answer_keeps_the_line_breaks_typed_not_the_ones_forms_send():
    """✨ Browsers send each typed line break as CRLF; the text box showed, and counted, one character."""
    block = answerable_block(pathway_document(), "statement")

    assert answer_from_form(pathway_document(), block, "First line.\r\nSecond line.") == "First line.\nSecond line."


def test_a_long_text_answer_at_the_limit_is_accepted_however_its_line_breaks_were_sent():
    block = answerable_block(pathway_document(), "statement")
    at_limit = ("x" * 99 + "\n") * 200

    assert answer_from_form(pathway_document(), block, at_limit.replace("\n", "\r\n")) == at_limit


def test_a_long_text_answer_may_be_cleared():
    block = answerable_block(pathway_document(), "statement")

    assert answer_from_form(pathway_document(), block, "") == ""


def test_a_long_text_answer_beyond_the_length_limit_is_refused():
    block = answerable_block(pathway_document(), "statement")

    with pytest.raises(AnswerRefused) as refused:
        answer_from_form(pathway_document(), block, "x" * 20_001)

    assert "xxx" not in str(refused.value)  # ✨ the refusal never echoes the participant's text


@pytest.mark.parametrize("submitted, stored", [("1", 1), ("7", 7), ("10", 10)])
def test_an_agreement_scale_answer_is_a_whole_number_from_one_to_ten(submitted, stored):
    block = answerable_block(pathway_document(), "baseline-bible")

    assert answer_from_form(pathway_document(), block, submitted) == stored


@pytest.mark.parametrize("submitted", ["0", "11", "-3", "5.5", "seven", "", " 7"])
def test_an_agreement_scale_answer_outside_the_scale_is_refused(submitted):
    block = answerable_block(pathway_document(), "baseline-bible")

    with pytest.raises(AnswerRefused):
        answer_from_form(pathway_document(), block, submitted)


@pytest.mark.parametrize("block_id", ["statement", "baseline-bible"])
def test_a_missing_answer_is_refused(block_id):
    block = answerable_block(pathway_document(), block_id)

    with pytest.raises(AnswerRefused):
        answer_from_form(pathway_document(), block, None)


def test_a_block_the_pathway_does_not_have_is_unknown():
    with pytest.raises(UnknownBlock):
        answerable_block(pathway_document(), "no-such-block")


def test_a_block_that_captures_nothing_takes_no_answer():
    with pytest.raises(UnknownBlock):
        answerable_block(pathway_document(), "welcome")
