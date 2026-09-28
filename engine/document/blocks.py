"""✨ One entry per block type: what it renders, and what (if anything) it captures.

Before this registry a new block type had to be found in four places at once. Adding one now means an
entry here, its authored shape in `pathway.schema.json`, and a template in `engine/templates/engine/blocks/`.
Nothing else needs to know the type exists: the answer schema, the refusal, the text a reader is shown,
which gate clauses may name it and whether it counts towards progress all follow from the entry.
"""

import json
import re
from typing import Callable, NamedTuple

from engine.document.text import text_for

# ✨ The points of an agreement scale. The answer schema, the refusal and the rendered buttons all use these.
SCALE_POINTS = range(1, 11)

# ✨ The longest long-text answer accepted. The rendered text box carries the same limit.
LONG_TEXT_MAX_LENGTH = 20_000


def _text_from_form(submitted):
    # ✨ The one exception to "text is never altered on input": forms send each typed line break as CRLF,
    # while the text box showed (and its maxlength counted) a single "\n". Converting it back stores what
    # the participant typed, and keeps the server's length limit the same as the browser's.
    return submitted.replace("\r\n", "\n")


def _scale_point_from_form(submitted):
    return int(submitted) if re.fullmatch(r"[0-9]+", submitted) else submitted


def _confirmation_from_form(submitted):
    # ✨ A confirmation is made or not yet made, so the only value worth storing is that it was made.
    return submitted == "true"


def _sort_from_form(submitted):
    # ✨ The widget sends the whole sort as JSON. A decimal is kept as its text, so the schema refuses 50.0
    # rather than storing a float (JSON Schema counts 50.0 as an integer). Text that is not JSON is passed on.
    try:
        return json.loads(submitted, parse_float=str)
    except json.JSONDecodeError:
        return submitted


class AnswerKind(NamedTuple):
    """✨ What an answer is: the shape the server accepts, what a submitted form value means, and what the
    server says to a participant when it refuses one.

    The refusal is shown in place of the schema's own message, which would echo the participant's text back.
    `from_form` reads what a form sent; anything it does not recognise it passes on for the schema to refuse.
    Kinds are shared between block types, so a gate clause can say which kinds of answer it can read.
    """

    name: str
    schema: dict | Callable[[dict], dict]
    refusal: str
    from_form: Callable[[str], object]

    def schema_for(self, document):
        """✨ The answer schema within one pathway document. Most kinds need nothing from it; a sort needs
        the document's items and buckets."""
        return self.schema(document) if callable(self.schema) else self.schema


TEXT = AnswerKind(
    "text",
    {"type": "string", "maxLength": LONG_TEXT_MAX_LENGTH},
    "This answer is too long to save.",
    _text_from_form,
)

SCALE_POINT = AnswerKind(
    "scale_point",
    {"type": "integer", "minimum": SCALE_POINTS[0], "maximum": SCALE_POINTS[-1]},
    f"Choose a number from {SCALE_POINTS[0]} to {SCALE_POINTS[-1]}.",
    _scale_point_from_form,
)


CONFIRMATION = AnswerKind(
    "confirmation",
    {"const": True},
    "Confirm that you have read the passages to open the activity.",
    _confirmation_from_form,
)


def _sort_schema(document):
    """✨ Every item of the instrument, each placed in one of its buckets with a whole value from 0 to 100."""
    instrument = document["instrument"]
    placement = {
        "type": "object",
        "additionalProperties": False,
        "required": ["bucket", "value"],
        "properties": {
            "bucket": {"enum": [bucket["id"] for bucket in instrument["buckets"]]},
            "value": {"type": "integer", "minimum": 0, "maximum": 100},
        },
    }
    item_ids = [item["id"] for item in instrument["items"]]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": item_ids,
        "properties": {item_id: placement for item_id in item_ids},
    }


SORT = AnswerKind(
    "sort",
    _sort_schema,
    "Place every item in a bucket and give each one a score from 0 to 100, then submit again.",
    _sort_from_form,
)


def _sort_widget(document, role):
    """✨ What the sort widget shows: every item in the reader's wording, and the buckets weakest first."""
    instrument = document["instrument"]
    return {
        "items": [{"id": item["id"], "text": text_for(item["text"], role)} for item in instrument["items"]],
        "buckets": [
            {"id": bucket["id"], "label": text_for(bucket["label"], role), "seed": bucket["seed"]}
            for bucket in instrument["buckets"]
        ],
    }


class BlockType(NamedTuple):
    """✨ One authorable kind of block.

    `text_fields` are the authored fields resolved to the reader's wording. `text_lists` are the same for
    a repeated sub-object, as `(list field, its text fields)`. `captures` is None when the block is content
    only: such a block takes no answer and counts towards nothing. `opens_what_follows` marks a block that
    holds the rest of its section shut until it has been answered. `scored` marks a block whose answer is
    scored into a result once, when it is submitted. `widget` gives a bespoke block's JavaScript what it
    shows, from the document and in one role's wording; a block rendered by its template alone has none.
    """

    name: str
    text_fields: tuple = ()
    text_lists: tuple = ()
    captures: AnswerKind | None = None
    opens_what_follows: bool = False
    scored: bool = False
    widget: Callable[[dict, str], dict] | None = None

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
            opens_what_follows=True,
        ),
        BlockType("long_text", text_fields=("prompt", "placeholder"), captures=TEXT),
        BlockType("agreement_scale", text_fields=("prompt", "min_label", "max_label"), captures=SCALE_POINT),
        BlockType("sort_assessment", captures=SORT, scored=True, widget=_sort_widget),
        BlockType("section_link", text_fields=("body", "button_label")),
    ]
}


# ✨ Authored text any kind of block may carry: the time its activity takes, for a section with several.
COMMON_TEXT_FIELDS = ("estimate",)


def authored_text(block, role):
    """✨ Every authored text field of a block, resolved to one role's wording."""
    block_type = BLOCK_TYPES[block["type"]]
    fields = (*COMMON_TEXT_FIELDS, *block_type.text_fields)
    text = {field: text_for(block[field], role) for field in fields if field in block}
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
