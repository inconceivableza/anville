"""✨ One entry per block type: what it renders, and what (if anything) it captures.

Before this registry a new block type had to be found in four places at once. Adding one now means an
entry here, its authored shape in `pathway.schema.json`, and a template in `engine/templates/engine/blocks/`.
Nothing else needs to know the type exists: the answer schema, the refusal, the text a reader is shown,
which gate clauses may name it and whether it counts towards progress all follow from the entry.
"""

from typing import NamedTuple

from engine.document.text import text_for

# ✨ The points of an agreement scale. The answer schema, the refusal and the rendered buttons all use these.
SCALE_POINTS = range(1, 11)

# ✨ The longest long-text answer accepted. The rendered text box carries the same limit.
LONG_TEXT_MAX_LENGTH = 20_000


class AnswerKind(NamedTuple):
    """✨ What an answer is: the shape the server accepts, and what it says to a participant when it refuses.

    The refusal is shown in place of the schema's own message, which would echo the participant's text back.
    Kinds are shared between block types, so a gate clause can say which kinds of answer it can read.
    """

    name: str
    schema: dict
    refusal: str


TEXT = AnswerKind(
    "text",
    {"type": "string", "maxLength": LONG_TEXT_MAX_LENGTH},
    "This answer is too long to save.",
)

SCALE_POINT = AnswerKind(
    "scale_point",
    {"type": "integer", "minimum": SCALE_POINTS[0], "maximum": SCALE_POINTS[-1]},
    f"Choose a number from {SCALE_POINTS[0]} to {SCALE_POINTS[-1]}.",
)


CONFIRMATION = AnswerKind(
    "confirmation",
    {"const": True},
    "Confirm that you have read the passages to open the activity.",
)


class BlockType(NamedTuple):
    """✨ One authorable kind of block.

    `text_fields` are the authored fields resolved to the reader's wording. `text_lists` are the same for
    a repeated sub-object, as `(list field, its text fields)`. `captures` is None when the block is content
    only: such a block takes no answer and counts towards nothing.
    """

    name: str
    text_fields: tuple = ()
    text_lists: tuple = ()
    captures: AnswerKind | None = None

    @property
    def is_interactive(self):
        """✨ Whether the participant does something here. Progress counts these blocks and no others."""
        return self.captures is not None


BLOCK_TYPES = {
    block_type.name: block_type
    for block_type in [
        BlockType("rich_text", text_fields=("label", "body")),
        BlockType(
            "scripture_reading",
            text_fields=("heading", "note", "confirm_label"),
            text_lists=(("passages", ("reference", "text")),),
            captures=CONFIRMATION,
        ),
        BlockType("long_text", text_fields=("prompt",), captures=TEXT),
        BlockType("agreement_scale", text_fields=("prompt", "min_label", "max_label"), captures=SCALE_POINT),
    ]
}


def authored_text(block, role):
    """✨ Every authored text field of a block, resolved to one role's wording."""
    block_type = BLOCK_TYPES[block["type"]]
    text = {field: text_for(block[field], role) for field in block_type.text_fields if field in block}
    for field, entry_fields in block_type.text_lists:
        text[field] = [
            {name: text_for(entry[name], role) for name in entry_fields if name in entry}
            for entry in block.get(field, [])
        ]
    return text


def blocks_of(document):
    """✨ Every block in the document, in the order it was authored."""
    for section in document["content"]["sections"]:
        yield from section["blocks"]


def block_types_by_id(document):
    """✨ Each block's type, keyed by its identifier. Used wherever a block is known only by name."""
    return {block["id"]: BLOCK_TYPES[block["type"]] for block in blocks_of(document)}


def section_of(document, block_id):
    """✨ The section a block belongs to, or None. A block identifier is unique across the pathway."""
    for section in document["content"]["sections"]:
        if any(block["id"] == block_id for block in section["blocks"]):
            return section
    return None
