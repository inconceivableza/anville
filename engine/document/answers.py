"""✨ What each capturing block accepts as its answer, checked on the server and never trusted to the widget.

Which blocks capture what is decided in `blocks.py`; this module only accepts or refuses a submitted value.
"""

import re

from jsonschema import Draft202012Validator

from engine.document.blocks import BLOCK_TYPES, LONG_TEXT_MAX_LENGTH, SCALE_POINTS, AnswerKind

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
    value = _parse(kind, submitted)
    if not _validators[kind.name].is_valid(value):
        raise AnswerRefused(kind.refusal)
    return value


def _parse(kind: AnswerKind, submitted):
    if kind.name == "scale_point" and re.fullmatch(r"[0-9]+", submitted):
        return int(submitted)
    if kind.name == "confirmation":
        # ✨ A confirmation is made or not yet made: the only value worth storing is that it was made.
        return submitted == "true"
    if kind.name == "text":
        # ✨ The one exception to "text is never altered on input": forms send each typed line break as
        # CRLF, while the text box showed (and its maxlength counted) a single "\n". Converting it back
        # stores what the participant typed, and keeps the server's length limit the same as the browser's.
        return submitted.replace("\r\n", "\n")
    return submitted  # ✨ anything else is left for the schema to accept or refuse


__all__ = [
    "LONG_TEXT_MAX_LENGTH",
    "SCALE_POINTS",
    "AnswerRefused",
    "UnknownBlock",
    "answer_from_form",
    "answerable_block",
]
