# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ The hub: the engine's view of where a participant has got to.

A hub is derived from the pathway's sections and what the participant has answered and completed. None of
it is an authored block (CONTEXT.md), so an author cannot write a status, a lock or a next-step banner, and
cannot accidentally leave one out. Nothing here touches the database or a request: the same derivation
serves the hub page, the guard on a section page and the re-check when a section is completed.
"""

from typing import NamedTuple

from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from engine.document.blocks import BLOCK_TYPES, page_count, page_of, pages_of
from engine.document.gates import (
    clause_passes,
    clauses_of,
    gate_passes,
    has_content,
    opened_key,
    unmet,
    unmet_clauses,
    waits_on_comparison,
    with_people_minimum,
)
from engine.document.text import text_for

LOCKED = "locked"
NOT_STARTED = "not-started"
IN_PROGRESS = "in-progress"
COMPLETE = "complete"

# ✨ Engine wording, not authored content: an author writes gate messages, never a status.
LABELS = {
    LOCKED: "Locked",
    NOT_STARTED: "Not started",
    IN_PROGRESS: "In progress",
    COMPLETE: "Complete",
}


# ✨ The coach's answer as the coach's side card tags it (ticket 51b): "waiting" while a working link is unanswered.
COACH_ANSWER_LABELS = {
    "waiting": "Link issued",
    "accepted": "Accepted",
    "declined": "Declined",
}


class CoachWaitWording(NamedTuple):
    """✨ What the engine says of a section waiting on the coach's acceptance, for one answer of the coach's: the
    next-step panel's `heading` and `sentence`, while nothing else is open, and the coach card's `line` under its tag,
    while the section waits on the coach at all (ticket 65)."""

    heading: str
    sentence: str
    line: str


# ✨ The coach card's line while no coach has said no, whether a link awaits their answer or there is none.
_OPENS_ONCE_YOUR_COACH_ACCEPTS = "{section} opens once your coach accepts"

# ✨ Engine wording for a section waiting on the coach's acceptance (ADR 0019), by the coach's answer as the coach page
# tells it: "waiting" while a working link is unanswered, "declined", or None with no working link (none made, expired
# unanswered, or revoked).
COACH_WAIT_WORDING = {
    "waiting": CoachWaitWording(
        "Waiting on your coach to respond",
        "{section} opens once {coach} has accepted.",
        _OPENS_ONCE_YOUR_COACH_ACCEPTS,
    ),
    "declined": CoachWaitWording(
        "{coach} has said no",
        "Choose someone else to walk with you. {section} opens once they accept.",
        "Choose another coach to open {section}",
    ),
    None: CoachWaitWording(
        "Choose a coach",
        "{section} opens once your coach has accepted.",
        _OPENS_ONCE_YOUR_COACH_ACCEPTS,
    ),
}


def with_coach_answer(state, answer):
    """✨ The coach's section as its side card shows it: "Locked" while locked, the coach's answer while there is one or
    a working link awaits it (ticket 51b), and otherwise, with no coach, or their link revoked or expired unanswered,
    what it showed before any link was made, though the section stays complete (fix-2)."""
    if state.is_locked:
        return state
    return state._replace(label=COACH_ANSWER_LABELS.get(answer, LABELS[NOT_STARTED]))


class NextStepWording(NamedTuple):
    """✨ What the hub's next step says for a section that carries its own wording for it (ticket 49b), and `waiting`, what
    it says while the section's only open work waits on others' answers (ticket 68), with its placeholders, or None. A
    section may carry `waiting` alone, its heading and sentence then None (ticket 87)."""

    heading: str | None
    sentence: str | None
    waiting: str | None = None


class SectionState(NamedTuple):
    """✨ One section as the hub sees it. `is_next` marks the one section the hub points the participant at.
    `estimate` is the authored time it takes, or None once the section has been begun. `page` is the page of it
    the participant has reached, or the first once it is complete, which is where the hub leads. `part_of` is the
    section it is a part of, if any. `lock_note` says, while it is locked, what opens it. `number` is the authored number
    the hub shows beside it, if any, and `side_card` the authored sentence of a section the hub draws as a side card, or
    None for one it lists (ticket 49a). `next_step` is the authored heading and sentence the hub's next step shows while
    this section is the next step, or None for a section without them (ticket 49b)."""

    id: str
    title: str
    status: str
    label: str
    is_next: bool = False
    estimate: str | None = None
    page: int = 1
    part_of: str | None = None
    lock_note: str | None = None
    number: str | None = None
    side_card: str | None = None
    next_step: NextStepWording | None = None

    @property
    def is_locked(self):
        return self.status == LOCKED

    @property
    def called(self):
        """✨ What the engine's wording calls the section: "Section 3" for one numbered "03", as the pathway's own
        sentences call it, or its title for one without a number (tickets 65 and 68)."""
        return _called([(self.number, self.title)])

    def waiting_sentence(self, minimum):
        """✨ The sentence the hub's next step says while this section's only open work waits on others' answers (ticket
        68), as the section carries it, with what the engine's wording calls the section at {section} and the pathway's
        `minimum` number of observer answers at {minimum}; None for a section without one. Replaced as plain text, never
        through `format()`, as the lock note's {sections} is."""
        wording = self.next_step.waiting if self.next_step else None
        if wording is None:
            return None
        return wording.replace("{section}", self.called).replace("{minimum}", str(minimum))


def _called(numbered):
    """✨ What the engine's wording calls the sections given as (number, title): "Section 1" for one numbered "01",
    "Sections 1 and 2" for several all numbered, or else each by that or by its title for one without a number, joined
    ("Section 1 and Walk with a coach"). The one rule for both the hub's {section} and a lock note's (ticket 86)."""
    numbers = [number for number, _ in numbered if number and number.isdigit()]
    if len(numbered) > 1 and len(numbers) == len(numbered):
        return "Sections " + _joined_text([str(int(number)) for number in numbers])
    return _joined_text(
        [f"Section {int(number)}" if number and number.isdigit() else title for number, title in numbered]
    )


class OutlineEntry(NamedTuple):
    """✨ One section as the hub and the sidebar list it, with the parts of it listed under it (ticket 41b)."""

    section: SectionState
    parts: tuple


class CoachWait(NamedTuple):
    """✨ A section not yet opened whose opening conditions wait on the coach's acceptance (ADR 0019), and whether that
    is `only` what holds it shut, with the sections it requires done (ticket 65)."""

    section: SectionState
    only: bool

    def panel(self, answer, coach):
        """✨ The next-step panel's heading and sentence, as a `NextStepWording`, by the coach's `answer` as the coach
        page tells it, naming the `coach`."""
        wording = _coach_wait_wording(answer)
        return NextStepWording(
            wording.heading.format(coach=coach), wording.sentence.format(section=self.section.called, coach=coach)
        )

    def line(self, answer):
        """✨ The coach card's line under its tag, by the coach's `answer` as the coach page tells it."""
        return _coach_wait_wording(answer).line.format(section=self.section.called)


def _coach_wait_wording(answer):
    """✨ The engine's wording for the coach's `answer`, as `COACH_WAIT_WORDING` has it; an answer it lacks is said as
    no working link is."""
    return COACH_WAIT_WORDING.get(answer, COACH_WAIT_WORDING[None])


class Hub(NamedTuple):
    """✨ A participant's whole hub: their track's sections, the one to do next, how many of the sections it
    counts (`counted_sections`) are complete, out of `total`, and the first section waiting on the coach, as a
    `CoachWait`, if any. With no next step, `waiting_on_answers` is the first section passed over because its only open
    work waits on the comparison, and so on other people's answers (ticket 68), or None."""

    sections: tuple
    next_step: SectionState | None
    complete: int
    total: int
    coach_wait: CoachWait | None = None
    waiting_on_answers: SectionState | None = None

    def outline(self):
        """✨ The sections as the hub and the sidebar list them, as `OutlineEntry`s, each with the parts listed under it.
        A part of a section outside the track is listed on its own. A side card is not listed: it is drawn beside the
        list (ticket 49a)."""
        listed = {state.id for state in self.sections if state.part_of is None}
        return [
            OutlineEntry(state, tuple(part for part in self.sections if part.part_of == state.id))
            for state in self.sections
            if state.part_of not in listed and state.side_card is None
        ]

    def side_cards(self):
        """✨ The sections the hub draws as side cards, in the document's order."""
        return [state for state in self.sections if state.side_card is not None]


def track_sections(document):
    """✨ The sections of the participant's track.

    Until a participant can choose a track (ticket 23), a track is the whole pathway. Everything that
    counts sections or blocks goes through here, so choosing a track later changes this function alone.
    """
    return document["content"]["sections"]


def section_by_id(document, section_id):
    """✨ The section with this identifier within the participant's track, or None."""
    return next((section for section in track_sections(document) if section["id"] == section_id), None)


def open_blocks(section, answers, sections, up_to_page=1):
    """✨ The blocks of a section a participant has reached, and whether nothing in them holds the rest shut.

    A block that opens what follows it (a scripture reading) holds the rest of the section shut until it
    has been answered. A signpost marked `holds_what_follows` holds it shut until the linked section's gate
    passes, which is why the track's `sections` are needed. Pages after `up_to_page`, the page reached, are
    shut too. The server decides this on every request, so an activity a participant has not opened is
    neither in the page nor answerable: it is not reachable at all, rather than merely unseen.
    """
    sections_by_id = {other["id"]: other for other in sections}
    reached = []
    for block in (block for page in pages_of(section)[:up_to_page] for block in page):
        reached.append(block)
        if _holds_what_follows(block, answers, sections_by_id):
            return reached, False
    return reached, True


def page_reached(section, moved_past, answers, sections):
    """✨ The page of a section a participant has reached, from the pages they have moved past (`moved_past`, by
    section).

    Each page is reached only through every page ahead of it, and the last is as far as there is to go. A block
    holding the rest shut holds the pages after its own too, even once gone past: a participant who went on past a
    holding signpost, then made its section's gate fail again, is back on the signpost's page rather than on one with
    nothing.
    """
    last = page_count(section)
    moved_past = moved_past.get(section["id"], ())
    page = 1
    while page in moved_past and page < last:
        page += 1
    blocks, all_open = open_blocks(section, answers, sections, up_to_page=page)
    return page if all_open else page_of(section, blocks[-1]["id"])


def _holds_what_follows(block, answers, sections_by_id):
    if BLOCK_TYPES[block["type"]].opens_what_follows:
        return not has_content(answers.get(block["id"]))
    if block.get("holds_what_follows"):
        linked = sections_by_id.get(block["section"])
        return linked is None or not gate_passes(linked, answers)  # ✨ a signpost outside the track opens nothing
    return False


def block_ids_fixed_on_completion(section, answers):
    """✨ The blocks whose answers completing this section fixes: those the author marked `fixed_once_complete`
    that hold something. A marked block left unanswered is not fixed as a blank; it can still be answered, and is
    fixed the next time the section is completed.
    """
    return [
        block["id"]
        for block in section["blocks"]
        if block.get("fixed_once_complete") and has_content(answers.get(block["id"]))
    ]


def is_locked(section, completed, answers=None, sections=(), moved_past=None):
    """✨ Whether a section is still shut, because a section it requires has not been completed, because one of its
    opening conditions fails, or, for a part of a section in the track's `sections`, because the participant has not
    yet reached that section's signpost to it.

    A section the participant has already completed is never shut again, whatever happens to the sections
    it required. Otherwise the hub would show it as complete, link to it, and bounce them back here.
    """
    if section["id"] in completed:
        return False
    answers = answers or {}
    if not _requires_met(section, completed) or unmet_opening_notes(section, answers):
        return True
    return _waiting_on(section, completed, answers, sections, moved_past or {}) is not None


def _requires_met(section, completed):
    """✨ Whether every section this one requires is among those `completed`."""
    return set(section.get("requires", [])) <= set(completed)


def _has_opened(section, answers):
    """✨ Whether a section with opening conditions has opened, as stored the first time it did (ADR 0019)."""
    return has_content(answers.get(opened_key(section["id"])))


def unmet_opening_notes(section, answers, role="participant"):
    """✨ The authored message of each of a section's opening conditions that fails, in the order authored, said once
    each (ADR 0019), or none while they all pass. None fail once the section has opened, since that is stored and they
    are never asked again."""
    if _has_opened(section, answers):
        return []
    return unmet({"gate": section.get("opens_when", {})}, answers, role)


class WaitingOn(NamedTuple):
    """✨ What a part of a section waits on: that section, and the block in it holding the way to the part shut, if a
    block does (None while that section is locked, or its page with the signpost not yet reached)."""

    section: dict
    holding: dict | None


def _waiting_on(part, completed, answers, sections, moved_past):
    """✨ What a part of a section is shut by until the participant reaches it from that section, as a `WaitingOn`, or
    None once it is reached. The original prototype opens its Strengths assessment only from Section 1, once its
    passages are read (ticket 41b). A part whose section has no signpost to it opens with that section; one whose
    section is outside the track, such as the offline track's Strengths assessment without Section 1, by its own
    requirements alone."""
    parent = next((section for section in sections if section["id"] == part.get("part_of")), None)
    if parent is None:
        return None
    if is_locked(parent, completed, answers):
        return WaitingOn(parent, None)
    signpost = next(
        (block for block in parent["blocks"] if block["type"] == "section_signpost" and block["section"] == part["id"]),
        None,
    )
    if signpost is None:
        return None
    reached = page_reached(parent, moved_past, answers, sections)
    blocks, all_open = open_blocks(parent, answers, sections, up_to_page=reached)
    if signpost in blocks:
        return None
    return WaitingOn(parent, None if all_open else blocks[-1])


class Piece(NamedTuple):
    """✨ A stretch of a lock note's text, and whether a page draws it in italics, as it does each section title."""

    text: str
    italic: bool = False


def plain(text):
    """✨ A piece of a lock note drawn as it is."""
    return Piece(text)


def italic(text):
    """✨ A piece of a lock note drawn in italics: a section title it names (developer's call, 23 Oct)."""
    return Piece(text, italic=True)


class LockNote(str):
    """✨ What the hub says under a locked section (ticket 79), always built from `pieces`, each a `Piece` (ticket 86):
    plain text as a string, and, as a page draws it, each italic piece in italics."""

    def __new__(cls, pieces):
        note = super().__new__(cls, "".join(piece.text for piece in pieces))
        note.pieces = tuple(pieces)
        return note

    def __html__(self):
        return mark_safe(
            "".join(
                format_html("<em>{}</em>", piece.text) if piece.italic else escape(piece.text) for piece in self.pieces
            )
        )


# ✨ The engine's general lock note, for a section locked by what comes before it with nothing more to name.
GENERAL_LOCK_NOTE = "Complete what comes before this to open it."


def _lock_note(section, completed, answers, sections, moved_past, role):
    """✨ What the hub says under a locked section: the sections it requires still unfinished, and with them its
    opening conditions in the sentence it carries for that; once those sections are done, the message of each failing
    opening condition (ADR 0019); for a part waiting on its section, where it opens from and, while a reading there is
    unconfirmed, what opens it; otherwise the engine's general note."""
    notes = unmet_opening_notes(section, answers, role)
    if not _requires_met(section, completed):
        named = _unfinished_named(section, completed, sections, role)
        with_sections = section.get("opens_when", {}).get("with_sections")
        if named and notes and with_sections:
            return LockNote(_filled(text_for(with_sections, role), "{sections}", named))
        if not named:
            return LockNote([plain(GENERAL_LOCK_NOTE)])
        return LockNote([plain("Opens once you've "), *named, plain(".")])
    if notes:
        return LockNote([plain(" ".join(notes))])
    waiting = _waiting_on(section, completed, answers, sections, moved_past)
    if waiting is None:
        return LockNote([plain(GENERAL_LOCK_NOTE)])
    title = italic(text_for(waiting.section["title"], role))
    if waiting.holding is not None and BLOCK_TYPES[waiting.holding["type"]].opens_what_follows:
        return LockNote([plain("Opens from "), title, plain(", once you've read the passages.")])
    return LockNote([plain("Opens from "), title, plain(".")])


def _unfinished_named(section, completed, sections, role):
    """✨ What is left in the sections a section requires that are not yet complete, as the lock note's pieces, or None.
    Each is named by its authored phrase for what finishing it takes (ticket 79), or else as "finished {title}", as the
    faithful port names its sections (ticket 52), in the order of its requirements; those next to each other sharing a
    phrase together, so none is moved ahead of a section between them (sprint 3b code review). A phrase's {min} is its
    section's own `links_issued` minimum, filled before they are grouped (ticket 81). A required section outside the
    track is not named."""
    by_id = {other["id"]: other for other in sections}
    runs = []
    for required in section.get("requires", []):
        other = by_id.get(required)
        if other is None or required in completed:
            continue
        if "to_finish" in other:
            phrase = with_people_minimum(text_for(other["to_finish"], role), clauses_of(other))
        else:
            phrase = "finished {title}"
        if runs and runs[-1][0] == phrase:
            runs[-1][1].append(other)
        else:
            runs.append((phrase, [other]))
    if not runs:
        return None
    return _joined([_named_by(phrase, group, role) for phrase, group in runs])


def _named_by(phrase, group, role):
    """✨ The pieces naming a `group` of sections sharing a `phrase`. In it, {section} is what the engine's wording calls
    them ("Sections 1 and 2"), and {title} their titles, in italics, as a section's title is wherever a note names it
    (developer's call, 23 Oct)."""
    titles = [text_for(other["title"], role) for other in group]
    called = _called([(other.get("number"), title) for other, title in zip(group, titles)])
    return _filled(phrase.replace("{section}", called), "{title}", _joined([[italic(title)] for title in titles]))


def _filled(text, placeholder, pieces):
    """✨ `text` as pieces, with `pieces` wherever it says `placeholder`. Replaced as plain text, never through
    `format()`, so an author's other braces stay as written."""
    filled = []
    for index, part in enumerate(text.split(placeholder)):
        if index:
            filled.extend(pieces)
        filled.append(plain(part))
    return filled


def _joined(items):
    """✨ Lists of pieces joined as the lock note joins what it names: "A, B and C"."""
    joined = []
    for index, item in enumerate(items):
        if index:
            joined.append(plain(" and " if index == len(items) - 1 else ", "))
        joined.extend(item)
    return joined


def _joined_text(words):
    """✨ `words` joined as `_joined` joins pieces, as plain text."""
    return "".join(piece.text for piece in _joined([[plain(word)] for word in words]))


def complete_sections(sections, answers, completed):
    """✨ The sections that are complete: those the participant completed, each part of a section whose gate passes, and
    each hub side card whose gate passes once it is open.

    A part has no completion of its own (ticket 41b), as the original prototype's Strengths assessment has none within
    Section 1, so it is complete exactly when its gate passes, worked out here rather than stored. A side card has nothing
    to press either (ticket 52): it is complete once it is open and its gate passes, and the caller stores that, so it
    stays complete when its links later expire or are revoked.
    """
    parts_done = {section["id"] for section in sections if "part_of" in section and gate_passes(section, answers)}
    done = set(completed) | parts_done
    cards_done = {
        section["id"]
        for section in sections
        if "side_card" in section and _requires_met(section, done) and gate_passes(section, answers)
    }
    return done | cards_done


def is_once_only_and_complete(section, completed):
    """✨ Whether a section is never seen again: a once-only section the participant has completed (ticket 69). It is
    left out of the hub, the sidebar and the count, and every way into it leads to the hub."""
    return bool(section.get("once_only")) and section["id"] in completed


def listed_sections(sections, completed):
    """✨ The sections the hub lists, given those complete as `complete_sections` works them out: all but a once-only
    section once complete. Progress counts these alone, or some of them (`counted_sections`)."""
    return [section for section in sections if not is_once_only_and_complete(section, completed)]


def counted_sections(sections, completed):
    """✨ The sections progress counts, on the hub and as an organisation's admins see it: of those listed, only the
    numbered ones in a pathway that numbers any, leaving out its parts, its side cards and its wizard (sprint 3c, ticket
    87); every one listed in a pathway that numbers none, as the faithful port."""
    listed = listed_sections(sections, completed)
    numbered = [section for section in listed if section.get("number")]
    return numbered or listed


def hub_for(sections, answers, completed, role="participant", moved_past=None):
    """✨ A participant's hub over one track's sections, less any once-only section once complete. `moved_past` holds,
    by section, the pages moved past."""
    moved_past = moved_past or {}
    completed = complete_sections(sections, answers, completed)
    listed = listed_sections(sections, completed)
    states = [_state(section, answers, completed, role, moved_past, sections) for section in listed]
    blocks = {block["id"]: block for section in sections for block in section["blocks"]}
    open_states = [state for state in states if state.status in (NOT_STARTED, IN_PROGRESS)]
    waiting = {
        state.id for state, section in zip(states, listed) if _waits_only_on_comparison(section, answers, blocks)
    }
    next_step = next((state for state in open_states if state.id not in waiting), None)
    states = [state._replace(is_next=state is next_step) for state in states]
    waiting_on_answers = next((state for state in open_states if state.id in waiting), None)
    coach_wait = next(
        (
            CoachWait(
                state,
                only=_requires_met(section, completed)
                and _waiting_on(section, completed, answers, sections, moved_past) is None,
            )
            for section, state in zip(listed, states)
            if state.is_locked and _waits_on_coach(section, answers)
        ),
        None,
    )
    counted = {section["id"] for section in counted_sections(sections, completed)}
    return Hub(
        sections=tuple(states),
        next_step=next((state for state in states if state.is_next), None),
        complete=sum(1 for state in states if state.id in counted and state.status == COMPLETE),
        total=len(counted),
        coach_wait=coach_wait,
        waiting_on_answers=None if next_step is not None else waiting_on_answers,
    )


def _waits_only_on_comparison(section, answers, blocks):
    """✨ Whether a section's only open work waits on other people: every clause of its gate still unmet names a block
    waiting on the comparison (ticket 68), as Section 2's reflection does in *Whatever You Do* (ticket 87). The hub's
    next step passes over it (ADR 0019)."""
    clauses = unmet_clauses(section, answers)
    return bool(clauses) and all(waits_on_comparison(blocks.get(clause["block"], {}), answers) for clause in clauses)


def _waits_on_coach(section, answers):
    """✨ Whether a section not yet opened has a `coach_accepted` opening condition that fails (ADR 0019)."""
    if _has_opened(section, answers):
        return False
    clauses = section.get("opens_when", {}).get("clauses", [])
    return any(clause["type"] == "coach_accepted" and not clause_passes(clause, answers) for clause in clauses)


def _state(section, answers, completed, role, moved_past, sections):
    status = _status(section, answers, completed, sections, moved_past)
    return SectionState(
        id=section["id"],
        title=text_for(section["title"], role),
        status=status,
        label=LABELS[status],
        estimate=_estimate(section, status, role),
        # ✨ A completed section is reopened to reread, so from its start rather than where it was left (ticket 41e).
        page=1 if status == COMPLETE else page_reached(section, moved_past, answers, sections),
        part_of=section.get("part_of"),
        lock_note=_lock_note(section, completed, answers, sections, moved_past, role) if status == LOCKED else None,
        number=section.get("number"),
        side_card=text_for(section["side_card"]["sentence"], role) if "side_card" in section else None,
        next_step=_next_step_wording(section, role),
    )


def _next_step_wording(section, role):
    """✨ The heading and sentence the section carries for when it is the next step, each None for a section carrying
    only its `waiting` sentence (ticket 87), or None."""
    if "next_step" not in section:
        return None
    wording = {field: text_for(text, role) for field, text in section["next_step"].items()}
    return NextStepWording(wording.get("heading"), wording.get("sentence"), wording.get("waiting"))


def _estimate(section, status, role):
    """✨ How long the section takes, said only until the participant has begun it, after which it no longer holds."""
    if "estimate" not in section or status not in (LOCKED, NOT_STARTED):
        return None
    return text_for(section["estimate"], role)


def _status(section, answers, completed, sections, moved_past):
    if section["id"] in completed:
        return COMPLETE  # ✨ completing is the participant's own act, so it outlasts any later change
    if is_locked(section, completed, answers, sections, moved_past):
        return LOCKED
    # ✨ A section's own blocks and its parts' count, so a section whose own blocks take no answer is in progress once
    # its part is begun (ticket 87).
    parts = [other for other in sections if other.get("part_of") == section["id"]]
    if any(has_content(answers.get(block["id"])) for other in (section, *parts) for block in _interactive_blocks(other)):
        return IN_PROGRESS
    return NOT_STARTED


def _interactive_blocks(section):
    """✨ The section's own blocks the participant does something with. Progress counts these and no others."""
    return [block for block in section["blocks"] if BLOCK_TYPES[block["type"]].is_interactive]
