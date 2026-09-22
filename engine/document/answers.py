"""✨ What each capturing block accepts as its answer, checked on the server and never trusted to the widget."""

import re

from jsonschema import Draft202012Validator

# ✨ The points of an agreement scale. The answer schema, the refusal and the rendered buttons all use these.
SCALE_POINTS = range(1, 11)

# ✨ The answer schema of every block type that captures an answer. A type missing here captures nothing.
ANSWER_SCHEMAS = {
    "long_text": {"type": "string", "maxLength": 20_000},
    "agreement_scale": {"type": "integer", "minimum": SCALE_POINTS[0], "maximum": SCALE_POINTS[-1]},
}

_validators = {block_type: Draft202012Validator(schema) for block_type, schema in ANSWER_SCHEMAS.items()}

# ✨ Shown to the participant in place of the schema's own message, which would echo their text back.
_REFUSALS = {
    "long_text": "This answer is too long to save.",
    "agreement_scale": f"Choose a number from {SCALE_POINTS[0]} to {SCALE_POINTS[-1]}.",
}


class UnknownBlock(Exception):
    """✨ The pathway version has no block by that identifier that takes an answer."""


class AnswerRefused(Exception):
    """✨ The submitted value is not a valid answer for its block."""


def answerable_block(document, block_id):
    """✨ The block with this identifier, if it takes an answer; otherwise UnknownBlock."""
    for section in document["content"]["sections"]:
        for block in section["blocks"]:
            if block["id"] == block_id and block["type"] in ANSWER_SCHEMAS:
                return block
    raise UnknownBlock(block_id)


def answer_from_form(block, submitted):
    """✨ The answer a submitted form value stands for, or AnswerRefused. Text is kept exactly as written."""
    if submitted is None:
        raise AnswerRefused("No answer was sent.")
    value = _parse(block["type"], submitted)
    if not _validators[block["type"]].is_valid(value):
        raise AnswerRefused(_REFUSALS[block["type"]])
    return value


def _parse(block_type, submitted):
    if block_type == "agreement_scale" and re.fullmatch(r"[0-9]+", submitted):
        return int(submitted)
    return submitted  # ✨ anything else is left for the schema to accept or refuse
