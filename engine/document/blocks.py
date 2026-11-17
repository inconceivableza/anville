# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ One entry per block type: what it renders, what (if anything) it captures, and the rules the views read for
showing and saving it.

Adding a block type means an entry here, its authored shape in `pathway.schema.json`, and a template in
`engine/templates/engine/blocks/`. Unless its page needs something from the database, as a contact list's links or a
sort's results do, nothing else needs to know the type exists: the answer schema, the refusal, the text a reader is
shown, which gate clauses may name it, whether it counts towards progress, where a link to it lands and whether it saves
quietly all follow from the entry.
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
    It reads the one value sent under the answer's name, or with `reads_every_value` all of them, as a list. It is
    None for a kind whose form sends its answer under more than one name.
    Kinds are shared between block types, so a gate clause can say which kinds of answer it can read.
    """

    name: str
    schema: dict | Callable[[dict, dict, str], dict]
    refusal: str
    from_form: Callable[[str], object] | Callable[[list[str]], object] | None
    # ✨ What an observer may leave out of the answer, filled in from the document before it is held to the schema.
    observer_defaults: Callable[[dict, object], object] | None = None
    # ✨ Whether the form sends a value for each part of the answer, as a choice of many sends one for each option
    # ticked, so `from_form` is given every value sent rather than the last.
    reads_every_value: bool = False

    def schema_for(self, document, block, role="participant"):
        """✨ The answer schema for one block within its pathway document, for one role. Most kinds need none of them; a
        sort needs the document's items and buckets, and whose sort it is, and a choice its block's options."""
        return self.schema(document, block, role) if callable(self.schema) else self.schema


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


# ✨ An item an observer placed in "Haven't seen this", as it is sent and kept (ticket 108): no bucket and no value.
NOT_SEEN = {"seen": False}


def _sort_schema(document, block, role):
    """✨ Every item of the instrument, each placed in one of its buckets with a whole value from 0 to 100, or, in an
    observer's sort where the document offers "Haven't seen this" (`offers_not_seen`), not seen (ticket 108)."""
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
    if offers_not_seen(document, role):
        placement = {"oneOf": [placement, {"const": NOT_SEEN}]}
    item_ids = [item["id"] for item in instrument["items"]]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": item_ids,
        "properties": {item_id: placement for item_id in item_ids},
    }


def left_at_seeds(document, sort):
    """✨ A sort with every placement sent without a value given its bucket's seed, as if its slider were left
    untouched, so an observer can send straight after placing the cards. Anything else is passed on as sent, for the
    schema to hold to the contract."""
    if not isinstance(sort, dict):
        return sort
    seeds = {bucket["id"]: bucket["seed"] for bucket in document["instrument"]["buckets"]}

    def seeded(placement):
        if isinstance(placement, dict) and "value" not in placement and placement.get("bucket") in seeds:
            return {**placement, "value": seeds[placement["bucket"]]}
        return placement

    return {item: seeded(placement) for item, placement in sort.items()}


SORT = AnswerKind(
    "sort",
    _sort_schema,
    "Place every item in a bucket and give each one a score from 0 to 100, then submit again.",
    _sort_from_form,
    observer_defaults=left_at_seeds,
)


def _choice_schema(document, block, role):
    """✨ The identifier of one of the block's own options, never its label. The empty choice ("Select...")
    takes the answer back, as emptying a text box does: blank counts as unanswered everywhere."""
    return {"enum": ["", *(option["id"] for option in block["options"])]}


CHOICE = AnswerKind("choice", _choice_schema, "Choose one of the options.", _text_from_form)


def _choices_schema(document, block, role):
    """✨ The identifiers of any of the block's own options, each at most once, never their labels. None at all takes
    the answer back: an empty list counts as unanswered everywhere."""
    return {"type": "array", "uniqueItems": True, "items": {"enum": [option["id"] for option in block["options"]]}}


def _choices_from_form(sent):
    # ✨ A value for each option ticked, after the blank one the form always sends first, so that a form sent with
    # nothing ticked still says so, and unticking every option takes the answer back.
    return [value for value in sent if value != ""]


def choices_of(answer):
    """✨ The identifiers a choice of many holds, as a list, for its template to tick. A single option's identifier, as
    a single select stores it, reads as a choice of that one, so a reason given before it took many still shows; no
    answer, or a blank one, as none."""
    if isinstance(answer, list):
        return answer
    return [answer] if isinstance(answer, str) and answer else []


CHOICES = AnswerKind(
    "choices", _choices_schema, "Choose only from the options.", _choices_from_form, reads_every_value=True
)

# ✨ People other than the participant. A list is never sent as one form value: each person is added or changed on
# their own (`contact_from_form` holds them to their rules), and they are kept as contacts rather than answers. The
# schema is what the gate then reads. Each person also carries their contact id.
CONTACTS = AnswerKind(
    "contacts",
    {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "id": {"type": "integer"},
            },
        },
    },
    "Check the names and email addresses.",
    None,
)


# ✨ The sort widget's own wording where a document has none: the prototype's, and for an observer the same about the
# participant, in the third person. `{count}` is left for the widget to fill in.
SORT_WORDING = {
    "sort_heading": {"participant": "Sort your strengths", "observer": "Sort {name}'s strengths"},
    "sort_instruction": {
        "participant": "Choose the bucket that fits best",
        "observer": "Choose the bucket that fits {name} best",
    },
    "all_sorted": "All {count} sorted!",
    # ✨ Shown to observers only, who may send once every card is placed (see `left_at_seeds`).
    "send_or_fine_tune": "You can send your evaluation now, or fine-tune how strong each one is in {name} first.",
    "fine_tune_label": "Continue to fine-tuning →",
    # ✨ Observers only too: sending without fine-tuning, apart from `submit_label`, which sends after it.
    "send_now_label": "Skip fine-tuning and send →",
    "fine_tune_heading": {"participant": "How strong is each one?", "observer": "How strong is each one in {name}?"},
    "fine_tune_intro": "Grouped by how you sorted them. Adjust the sliders to fine-tune.",
    "slider_min": {"participant": "Not me", "observer": "Not {name}"},
    "slider_max": "Real strength",
    "submit_label": {"participant": "See my results →", "observer": "Send my evaluation →"},
    # ✨ Observers only, where "Haven't seen this" is offered: once every card is placed there, what sending means, and
    # the press that sends it, in place of the others (ticket 120). Such a send is kept as a decline.
    "nothing_seen": "You haven’t seen any of these in {name}, so there’s nothing to add to how others see them. If "
    "that’s right, send it, and we’ll keep only that you couldn’t answer. To change a card, undo back to it.",
    "decline_label": "Send that I couldn’t answer →",
    # ✨ The two-round prototype's, used only where some items are reworded (see `twin`): round 1 the originals, round 2
    # the rewordings, with a look at how the buckets were used between them.
    "round_1_title": {"participant": "What you’re good at", "observer": "What {name} is good at"},
    "round_2_title": {"participant": "What you find yourself doing", "observer": "What you’d see {name} doing"},
    "scale_less": {"participant": "← Less like me", "observer": "← Less like {name}"},
    "scale_more": {"participant": "More like me →", "observer": "More like {name} →"},
    "halfway_heading": "Round 1 done",
    "halfway_intro": {
        "participant": "Round 2 covers the same ground from a different angle: things you’d find yourself doing. Don’t "
        "try to match your earlier answers. Answer for the words in front of you.",
        "observer": "Round 2 covers the same ground from a different angle: things you’d see {name} doing. Don’t try "
        "to match your earlier answers. Answer for the words in front of you.",
    },
    "buckets_used_heading": "How you used the buckets",
    # ✨ Well spread is 5 or more of 7 buckets used, none holding more than a third of the cards. The widget fills in
    # `{used}`, `{buckets}` and, where one bucket holds too many, `{crowded}` with `buckets_crowded`, as it does
    # `{count}`.
    "buckets_spread_well": "You used {used} of the {buckets} buckets. That’s a good spread, and it makes your results "
    "clearer. Keep doing the same in round 2.",
    "buckets_spread_more": "You used {used} of the {buckets} buckets{crowded}. Spreading your answers out makes the "
    "results clearer, so in round 2 try using the whole range where it fits.",
    "buckets_crowded": ", and {count} of your {cards} cards are in “{bucket}”",
    "start_round_2_label": "Start round 2",
    "undo_last_card_label": "Undo last card",
    # ✨ The quick check, participants' only (see `quick_check`). `{pairs}` is "One pair" or "3 pairs".
    "check_heading": "{pairs} pulled in opposite directions",
    "check_intro": "Each pair describes the same strength in different words, but you put them on opposite sides. "
    "Change either answer if it doesn’t look right. If both are true, leave them as they are.",
}

# ✨ What an observer is told on sending an assessment a second time through the same claim: the first one stands.
SENT_ALREADY = "Your evaluation has already been sent."


def _sort_widget(document, role, name=""):
    """✨ What the sort widget shows: every item in the reader's wording, the buckets weakest first, and the widget's
    own wording, each field the document's or else the engine's. `{name}` becomes the participant's name, as plain
    text, never through `format()`. An observer is offered sending as soon as every card is placed; a participant
    always fine-tunes, unless the document skips fine-tuning for everyone. Each item names its twin, either way round,
    and, where any is reworded, its round: the second for a rewording, the first for the rest. Where fine-tuning is
    skipped, a participant gets a quick check of twins answered far apart instead; an observer never does, as several
    observers' contradictions average out. An observer is offered "Haven't seen this" beside the buckets where the
    document has it (`offers_not_seen`, ticket 108). How the cards were spread over the buckets is shown between the
    rounds and once every card is placed, unless the document hides it, for everyone (ticket 108)."""
    instrument = document["instrument"]
    authored = document.get("presentation", {}).get("sort_wording", {})
    twins = {}
    for item in instrument["items"]:
        if "twin" in item:
            twins[item["id"]], twins[item["twin"]] = item["twin"], item["id"]

    def shown(text):
        return text_for(text, role).replace("{name}", name)

    return {
        "items": [
            {
                "id": item["id"],
                "text": shown(item["text"]),
                **({"twin": twins[item["id"]]} if item["id"] in twins else {}),
                **({"round": 2 if "twin" in item else 1} if twins else {}),
            }
            for item in instrument["items"]
        ],
        "buckets": [
            {"id": bucket["id"], "label": shown(bucket["label"]), "seed": bucket["seed"]}
            for bucket in instrument["buckets"]
        ],
        "wording": {field: shown(authored.get(field, default)) for field, default in SORT_WORDING.items()},
        "not_seen": {"label": shown(instrument["not_seen"]["label"])} if offers_not_seen(document, role) else None,
        "bucket_summary": not document.get("sorts_hide_bucket_summary", False),
        "fine_tunes": not skips_fine_tuning(document),
        "sends_before_fine_tuning": role == "observer",
        "quick_check": role == "participant" and skips_fine_tuning(document),
    }


def offers_not_seen(document, role):
    """✨ Whether `role`'s sort offers "Haven't seen this" beside the buckets (ticket 108): an observer's, where the
    document's instrument has it (`not_seen`); never the participant's, who answers for themselves."""
    return role == "observer" and "not_seen" in document["instrument"]


def skips_fine_tuning(document):
    """✨ Whether the document's sorts are sent once every card is placed, by everyone, each card at its bucket's
    seed."""
    return document.get("sorts_skip_fine_tuning", False)


class BlockType(NamedTuple):
    """✨ One authorable kind of block.

    `text_fields` are the authored fields resolved to the reader's wording. `text_lists` are the same for
    a repeated sub-object, as `(list field, its text fields)`. `captures` is None when the block is content
    only: such a block takes no answer and counts towards nothing. `opens_what_follows` marks a block that
    holds the rest of its section shut until it has been answered. `scored` marks a block whose answer is
    scored into a result once, when it is submitted. `widget` gives a bespoke block's JavaScript what it
    shows, from the document, in one role's wording and naming the participant; a block rendered by its template alone
    has none.

    `onward_label` is the wording of a button leading on to a block of this type, as the comparison's last button does
    to the block waiting on it. `quiet_setting` names the document setting under which its answer saves without saying
    "Saved" (`saves_quietly`). `reached_at_top` marks a block reached at its page's top, with no anchor, when it opens
    that page (`anchor_of`). `lists_links` marks a block whose people are listed with their links, so its page shows a
    link just issued, this once.

    `sent_with_its_page` marks an ordinary answer, whose fields belong to its page's one form under the block's own
    name (`page_field`), so that every press on the page sends it, and the press stores it before anything else: the
    page's Save without JavaScript, its way on with JavaScript or without, and the way back from a page that seals a
    letter (sprint-3d-r1-fix-6). With JavaScript it also saves on its own as it changes. `names_its_way_on` marks a
    block, the letter, that the press leading on from its page is for: worded by the block's `continue_label` where it
    has one, and landed on going back to that page (`way_on_named_by`, ticket 107).
    """

    name: str
    text_fields: tuple = ()
    text_lists: tuple = ()
    captures: AnswerKind | None = None
    opens_what_follows: bool = False
    scored: bool = False
    widget: Callable[[dict, str, str], dict] | None = None
    onward_label: str = "On to your reflection →"
    quiet_setting: str | None = None
    reached_at_top: bool = False
    lists_links: bool = False
    sent_with_its_page: bool = False
    names_its_way_on: bool = False

    @property
    def is_interactive(self):
        """✨ Whether the participant does something here. Progress counts these blocks and no others."""
        return self.captures is not None


# ✨ Never remove an entry while any stored pathway version uses it: versions are never edited, so every response
# pinned to one would break (spec, The pathway document and versions). A renamed one goes in `RENAMED_BLOCK_TYPES`.
BLOCK_TYPES = {
    block_type.name: block_type
    for block_type in [
        BlockType(
            "rich_text",
            text_fields=("heading", "label", "body", "list_label"),
            text_lists=(("items", ("lead", "text")),),
        ),
        BlockType(
            "scripture_reading",
            text_fields=("heading", "note", "confirm_label"),
            text_lists=(("passages", ("reference", "text")),),
            captures=CONFIRMATION,
            opens_what_follows=True,
        ),
        # ✨ Passages to read with nothing to confirm, so nothing beneath them waits on them (sprint 3c, ticket 87).
        BlockType(
            "scripture_passages", text_fields=("heading", "note"), text_lists=(("passages", ("reference", "text")),)
        ),
        BlockType("long_text", text_fields=("prompt", "placeholder"), captures=TEXT, sent_with_its_page=True),
        # ✨ A long text sealed as its section is finished, until a date the participant picks (ticket 104). Where a page
        # follows its own, the press leading there is worded for it, "Save my letter and continue →" (ticket 107).
        BlockType(
            "letter",
            text_fields=(
                "prompt",
                "placeholder",
                "copy_note",
                "continue_label",
                "seal_label",
                "seal_note",
                "date_label",
            ),
            captures=TEXT,
            sent_with_its_page=True,
            names_its_way_on=True,
        ),
        BlockType(
            "agreement_scale",
            text_fields=("prompt", "min_label", "max_label"),
            captures=SCALE_POINT,
            quiet_setting="ratings_save_quietly",
            sent_with_its_page=True,
        ),
        BlockType(
            "single_select",
            text_fields=("prompt", "placeholder"),
            text_lists=(("options", ("label",)),),
            captures=CHOICE,
            sent_with_its_page=True,
        ),
        # ✨ One or more choices from a list, as cards, each a checkbox (ticket 112).
        BlockType(
            "multi_select",
            text_fields=("prompt", "note"),
            text_lists=(("options", ("label",)),),
            captures=CHOICES,
            sent_with_its_page=True,
        ),
        BlockType("contact_list", text_fields=("more_note", "note"), captures=CONTACTS, lists_links=True),
        # ✨ Captures nothing: its answers are opinions about another person, never kept (see `coach.py`).
        BlockType(
            "coach_checklist",
            text_fields=(
                "heading",
                "lead",
                "body",
                "not_needed",
                "needed",
                "footnote",
                "name_prompt",
                "name_placeholder",
                "name_hint",
                "coach_invitation",
                "coach_accepted",
                "coach_declined",
            ),
            text_lists=(("questions", ("question", "note", "why", "coach_note", "coach_why", "commitment")),),
            # ✨ An anchor on the checklist that opens its page would scroll past the page's title (ticket 82).
            reached_at_top=True,
            lists_links=True,
        ),
        BlockType("sort_assessment", captures=SORT, scored=True, widget=_sort_widget),
        # ✨ Its `sort`'s results in full, drawn as the results page draws them, once there are any (ticket 57).
        BlockType("sort_results"),
        # ✨ The way to its `sort`'s comparison, saying where it stands (`comparison_status`), once there is a result
        # (ticket 67a).
        BlockType("comparison_signpost", text_fields=("title",)),
        BlockType("section_signpost", text_fields=("body", "button_label")),
        BlockType("download", text_fields=("body", "button_label"), onward_label="On to your workbook →"),
        # ✨ Never shown: it splits its section into pages (`pages_of`).
        BlockType("page_break"),
    ]
}

# ✨ The block types that quote passages of scripture, each passage from a translation the pathway declares.
PASSAGE_BLOCK_TYPES = ("scripture_reading", "scripture_passages")

# ✨ Block types renamed since a stored pathway version used them, old name to new (ticket 75). A stored version keeps
# its old names, since it is never edited, and is read under the new ones (`with_current_names`); a document being
# loaded may use only the new.
RENAMED_BLOCK_TYPES = {"section_link": "section_signpost", "comparison_link": "comparison_signpost"}


def with_current_names(document):
    """✨ A stored document with each block under a renamed type given its new name (`RENAMED_BLOCK_TYPES`), as the
    engine reads every stored pathway version. The document is changed in place and returned."""
    for section in document.get("content", {}).get("sections", []):
        for block in section.get("blocks", []):
            block["type"] = RENAMED_BLOCK_TYPES.get(block.get("type"), block.get("type"))
    return document


# ✨ Authored text any kind of block may carry: the time its activity takes, for a section with several.
COMMON_TEXT_FIELDS = ("estimate",)


def authored_text(block, role):
    """✨ Every authored text field of a block, resolved to one role's wording."""
    block_type = BLOCK_TYPES[block["type"]]
    fields = (*COMMON_TEXT_FIELDS, *block_type.text_fields)
    text = {field: text_for(block[field], role) for field in fields if field in block}
    for field, entry_fields in block_type.text_lists:
        # ✨ An entry's identifier, where it has one, comes along untranslated: a choice's option is answered by it.
        text[field] = [
            {
                **({"id": entry["id"]} if "id" in entry else {}),
                **{name: text_for(entry[name], role) for name in entry_fields if name in entry},
            }
            for entry in block.get(field, [])
        ]
    return text


def signpost_shown(block, text, linked_section, is_complete, role):
    """✨ A section signpost's wording and where its button leads, as `(text, sort)`. Once the linked section is
    complete, a signpost with `finished` wording shows it in place of its own body and button label, and `sort` is the
    identifier of the sort in that section, whose results the button then leads to, or None to lead to the section as
    before (ticket 61). Otherwise `text` is the signpost's own and `sort` is None."""
    finished = block.get("finished")
    if not (finished and is_complete):
        return text, None
    text = {
        **text,
        "body": text_for(finished["body"], role) if "body" in finished else "",
        "button_label": text_for(finished["button_label"], role),
    }
    sort = next((other["id"] for other in linked_section["blocks"] if BLOCK_TYPES[other["type"]].scored), None)
    return text, sort


# ✨ Where the way to the comparison stands, as a comparison signpost says it: engine wording, as the section statuses
# are, since its section's card and the hub's row are to say the same (spec, Blocks). While waiting, it says how many
# of the minimum have answered, which, unlike "Waiting for answers", never reads as done (ticket 81).
COMPARISON_STATUSES = {
    "waiting": "{answered} of {minimum} answered",
    "ready": "Ready to view",
    "viewed": "Viewed",
}


# ✨ What a comparison signpost says in place of its status between a retake and the new sort, as `(link, rest)`: the
# words leading back to the sort, then the rest of the sentence. Its card makes the first part the link; the hub's row
# and the sidebar show the two as one line.
COMPARISON_UNSORTED = ("Finish your strengths evaluation", "to compare.")


def comparison_status(answered, minimum, viewed):
    """✨ Where the way to a sort's comparison stands, as `(state, wording)`: viewed once the participant has pressed
    "Compare with how others see you →" with at least the minimum in, whatever has been answered since; otherwise ready
    from the minimum, and waiting below it, saying how many of the minimum have answered (tickets 67a, 81)."""
    if viewed:
        state = "viewed"
    elif answered >= minimum:
        state = "ready"
    else:
        state = "waiting"
    return state, COMPARISON_STATUSES[state].format(answered=answered, minimum=minimum)


# ✨ The warning before the press that freezes answer collection (ADR 0017), engine wording as the statuses are: when
# everyone invited has replied, and otherwise, with how many have, out of how many invited. Replied, not answered, since
# ticket 120: someone who declined has replied, and is waited on no longer.
FREEZE_WARNINGS = {
    "everyone": "Everyone you invited has replied. Once you look, you can't add anyone else.",
    "some": "{replied} of the {invited} people you invited have replied. Once you look, no more answers are added, "
    "so anyone who hasn't replied yet won't be able to.",
}


def freeze_warning(replied, invited):
    """✨ What the participant is told before the press on to the comparison freezes answer collection (ADR 0017): on
    "Before you look", or beside the press where the document puts it there (`warns_beside_the_press`). `replied` counts
    the assessments that count and the declines (ticket 120)."""
    if replied >= invited:
        return FREEZE_WARNINGS["everyone"]
    return FREEZE_WARNINGS["some"].format(replied=replied, invited=invited)


def warns_beside_the_press(document):
    """✨ Whether the document puts the freeze warning beside the press on to the comparison wherever it is offered, the
    press then showing the comparison with no page between (ticket 106); off, as in the faithful port, the press first
    asks on "Before you look"."""
    return document.get("freeze_warning_beside_the_press", False)


def translation_shown(document, passage):
    """✨ The translation named beside a passage's reference: its own, unless that is the document's, which the
    credits page says is the one used unless otherwise indicated. None when nothing is to be named."""
    own = passage.get("translation")
    return own if own != document.get("translation") else None


def text_shown(document, block, role):
    """✨ A block's authored text in one role's wording (`authored_text`), with each passage of a block quoting
    scripture naming its translation beside its reference, where `translation_shown` names one."""
    text = authored_text(block, role)
    if block["type"] in PASSAGE_BLOCK_TYPES:
        for passage, shown in zip(block["passages"], text["passages"]):
            shown["translation"] = translation_shown(document, passage)
    return text


def saves_quietly(document, section, block):
    """✨ Whether a block's answer saves without saying "Saved": every answer on a wizard's pages (ticket 83), and one
    whose type names a document setting for it (`quiet_setting`) where the document turns that setting on, as
    *Whatever You Do*'s 1–10 ratings do (sprint-3c-r3-fix-15). A refusal still says why."""
    setting = BLOCK_TYPES[block["type"]].quiet_setting
    return bool(section.get("wizard")) or bool(setting and document.get(setting, False))


def blocks_of(document):
    """✨ Every block in the document, in the order it was authored."""
    for section in document["content"]["sections"]:
        yield from section["blocks"]


def coach_brief(block):
    """✨ The coach brief a sort carries, in the participant's wording, as both the consent beside their comparison
    and the coach's link show it; None for a sort without one (ticket 25a)."""
    brief = block.get("coach_brief")
    if brief is None:
        return None
    return {
        **{field: text_for(brief[field], "participant") for field in ("title", "purpose", "length", "avoid")},
        **{
            field: [{"text": text_for(entry["text"], "participant")} for entry in brief[field]]
            for field in ("questions", "watch_for")
        },
    }


def block_types_by_id(document):
    """✨ Each block's type, keyed by its identifier. Used wherever a block is known only by name."""
    return {block["id"]: BLOCK_TYPES[block["type"]] for block in blocks_of(document)}


def pages_of(section):
    """✨ A section's blocks, page by page. Each `page_break` starts a new page and is on none; a section without one
    is a single page."""
    pages = [[]]
    for block in section["blocks"]:
        if block["type"] == "page_break":
            pages.append([])
        else:
            pages[-1].append(block)
    return pages


def way_on_named_by(page, sealed_ids):
    """✨ The block on a page, a list of its blocks, that the press leading on from that page is for
    (`names_its_way_on`), or None: a letter while it is written, not once it is sealed, when there is nothing of it to
    save (ticket 107). `sealed_ids` are the blocks of the participant's sealed letters."""
    named = (block for block in page if BLOCK_TYPES[block["type"]].names_its_way_on)
    return next((block for block in named if block["id"] not in sealed_ids), None)


def page_field(block):
    """✨ The name an answer sent with its page is sent under (`sent_with_its_page`, sprint-3d-r1-fix-6): the block's
    own, since one form sends every answer on the page and no two may share a name."""
    return f"answer-{block['id']}"


def page_count(section):
    """✨ How many pages a section has, and so the number of its last."""
    return len(pages_of(section))


def page_of(section, block_id):
    """✨ The page of its section a block is on, counting from 1, or None for a block not on any of them."""
    for number, page in enumerate(pages_of(section), start=1):
        if any(block["id"] == block_id for block in page):
            return number
    return None


def landing_of(block):
    """✨ The id on its page that saving a block without JavaScript comes back to: the block's own, or for a block that
    opens what follows (a reading), its confirmation, with what it opened just beneath (ticket 41e)."""
    if BLOCK_TYPES[block["type"]].opens_what_follows:
        return f"block-{block['id']}-confirmed"
    return f"block-{block['id']}"


def anchor_of(section, block_id):
    """✨ The anchor a link to a block takes on its page: the block's own, or None for a block whose type is reached at
    its page's top (`reached_at_top`) when it opens that page, so the page opens at its title (ticket 82)."""
    opening = pages_of(section)[page_of(section, block_id) - 1][0]
    if opening["id"] == block_id and BLOCK_TYPES[opening["type"]].reached_at_top:
        return None
    return f"block-{block_id}"


def section_of(document, block_id):
    """✨ The section a block belongs to, or None. A block identifier is unique across the pathway."""
    for section in document["content"]["sections"]:
        if any(block["id"] == block_id for block in section["blocks"]):
            return section
    return None


def section_ended_by(document, part):
    """✨ The section a part is the last thing in, or None: the section it is a part of, when that section's last block
    is its signpost to the part, as Section 1 ends in the strengths evaluation (ticket 88). The part's end then offers
    that section's finish. A part its section does not link to, or one with anything after its link, ends nothing."""
    if "part_of" not in part:
        return None
    parent = next((section for section in document["content"]["sections"] if section["id"] == part["part_of"]), None)
    return parent if parent is not None and ends_in_signpost_to(parent, part) else None


def ends_in_signpost_to(parent, part):
    """✨ Whether a section's last block is its signpost to `part`, so the part's end is the section's (ticket 88)."""
    last = parent["blocks"][-1] if parent["blocks"] else None
    return last is not None and last["type"] == "section_signpost" and last["section"] == part["id"]
