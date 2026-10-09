# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Accepting or refusing one submitted answer, on the server and never trusted to the widget.

What each block captures, and what a form value means for it, is decided in `blocks.py`. This module
only finds the block and holds it to its answer kind.
"""

from jsonschema import Draft202012Validator

from engine.document.blocks import BLOCK_TYPES

class UnknownBlock(Exception):
    """✨ The pathway version has no block by that identifier that takes an answer."""


class AnswerRefused(Exception):
    """✨ The submitted value is not a valid answer for its block.

    `field` says which entry is at fault, and where the answer has rows, such as a contact list, `row` (counted
    from 1) says which row, so the page can mark it as well as saying so. The coach's details use `field` alone.
    """

    def __init__(self, message, row=None, field=None):
        super().__init__(message)
        self.row = row
        self.field = field


def answerable_block(document, block_id):
    """✨ The block with this identifier, if it takes an answer; otherwise UnknownBlock."""
    for section in document["content"]["sections"]:
        for block in section["blocks"]:
            if block["id"] == block_id and BLOCK_TYPES[block["type"]].is_interactive:
                return block
    raise UnknownBlock(block_id)


def answer_from_form(document, block, submitted):
    """✨ The answer a submitted form value stands for, or AnswerRefused. Text is kept exactly as written.

    The document is the block's own pathway version, since what a valid answer is can depend on it.
    """
    if submitted is None:
        raise AnswerRefused("No answer was sent.")
    kind = BLOCK_TYPES[block["type"]].captures
    if not Draft202012Validator(kind.schema_for(document, block)).is_valid(value := kind.from_form(submitted)):
        raise AnswerRefused(kind.refusal)
    return value
