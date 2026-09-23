"""✨ Accepting or refusing one submitted answer, on the server and never trusted to the widget.

What each block captures, and what a form value means for it, is decided in `blocks.py`. This module
only finds the block and holds it to its answer kind.
"""

from jsonschema import Draft202012Validator

from engine.document.blocks import BLOCK_TYPES

_validators = {
    block_type.captures.name: Draft202012Validator(block_type.captures.schema)
    for block_type in BLOCK_TYPES.values()
    if block_type.is_interactive
}


class UnknownBlock(Exception):
    """✨ The pathway version has no block by that identifier that takes an answer."""


class AnswerRefused(Exception):
    """✨ The submitted value is not a valid answer for its block."""


def answerable_block(document, block_id):
    """✨ The block with this identifier, if it takes an answer; otherwise UnknownBlock."""
    for section in document["content"]["sections"]:
        for block in section["blocks"]:
            if block["id"] == block_id and BLOCK_TYPES[block["type"]].is_interactive:
                return block
    raise UnknownBlock(block_id)


def answer_from_form(block, submitted):
    """✨ The answer a submitted form value stands for, or AnswerRefused. Text is kept exactly as written."""
    if submitted is None:
        raise AnswerRefused("No answer was sent.")
    kind = BLOCK_TYPES[block["type"]].captures
    if not _validators[kind.name].is_valid(value := kind.from_form(submitted)):
        raise AnswerRefused(kind.refusal)
    return value
