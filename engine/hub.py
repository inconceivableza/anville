# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ The hub: the engine's view of where a participant has got to.

A hub is derived from the pathway's sections and what the participant has answered and completed. None of
it is an authored block (CONTEXT.md), so an author cannot write a status, a lock or a next-step banner, and
cannot accidentally leave one out. Nothing here touches the database or a request: the same derivation
serves the hub page, the guard on a section page and the re-check when a section is completed.
"""

from typing import NamedTuple

from engine.document.blocks import BLOCK_TYPES, page_count, page_of, pages_of
from engine.document.gates import gate_passes, has_content
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


class SectionState(NamedTuple):
    """✨ One section as the hub sees it. `is_next` marks the one section the hub points the participant at.
    `estimate` is the authored time it takes, or None once the section has been begun. `page` is the page of it
    the participant has reached, or the first once it is complete, which is where the hub leads. `part_of` is the
    section it is a part of, if any. `lock_note` says, while it is locked, what opens it."""

    id: str
    title: str
    status: str
    label: str
    is_next: bool = False
    estimate: str | None = None
    page: int = 1
    part_of: str | None = None
    lock_note: str | None = None

    @property
    def is_locked(self):
        return self.status == LOCKED


class OutlineEntry(NamedTuple):
    """✨ One section as the hub and the sidebar list it, with the parts of it listed under it (ticket 41b)."""

    section: SectionState
    parts: tuple


class Hub(NamedTuple):
    """✨ A participant's whole hub: their track's sections, the one to do next, and how much is answered."""

    sections: tuple
    next_step: SectionState | None
    answered: int
    total: int

    def outline(self):
        """✨ The sections as the hub and the sidebar list them, as `OutlineEntry`s, each with the parts listed under it.
        A part of a section outside the track is listed on its own."""
        listed = {state.id for state in self.sections if state.part_of is None}
        return [
            OutlineEntry(state, tuple(part for part in self.sections if part.part_of == state.id))
            for state in self.sections
            if state.part_of not in listed
        ]


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
    has been answered. A link marked `holds_what_follows` holds it shut until the linked section's gate
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
    held link, then made its section's gate fail again, is back on the link's page rather than on one with nothing.
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
        return linked is None or not gate_passes(linked, answers)  # ✨ a link outside the track opens nothing
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
    """✨ Whether a section is still shut, because a section it requires has not been completed, or, for a part of a
    section in the track's `sections`, because the participant has not yet reached that section's link to it.

    A section the participant has already completed is never shut again, whatever happens to the sections
    it required. Otherwise the hub would show it as complete, link to it, and bounce them back here.
    """
    if section["id"] in completed:
        return False
    if not _requires_met(section, completed):
        return True
    return _waiting_on(section, completed, answers or {}, sections, moved_past or {}) is not None


def _requires_met(section, completed):
    """✨ Whether every section this one requires has been completed."""
    return set(section.get("requires", [])) <= set(completed)


class WaitingOn(NamedTuple):
    """✨ What a part of a section waits on: that section, and the block in it holding the way to the part shut, if a
    block does (None while that section is locked, or its page with the link not yet reached)."""

    section: dict
    holding: dict | None


def _waiting_on(part, completed, answers, sections, moved_past):
    """✨ What a part of a section is shut by until the participant reaches it from that section, as a `WaitingOn`, or
    None once it is reached. The original prototype opens its Strengths assessment only from Section 1, once its
    passages are read (ticket 41b). A part whose section has no link to it opens with that section; one whose section
    is outside the track, such as the offline track's Strengths assessment without Section 1, by its own requirements
    alone."""
    parent = next((section for section in sections if section["id"] == part.get("part_of")), None)
    if parent is None:
        return None
    if is_locked(parent, completed):
        return WaitingOn(parent, None)
    link = next(
        (block for block in parent["blocks"] if block["type"] == "section_link" and block["section"] == part["id"]),
        None,
    )
    if link is None:
        return None
    reached = page_reached(parent, moved_past, answers, sections)
    blocks, all_open = open_blocks(parent, answers, sections, up_to_page=reached)
    if link in blocks:
        return None
    return WaitingOn(parent, None if all_open else blocks[-1])


def _lock_note(section, completed, answers, sections, moved_past, role):
    """✨ What the hub says under a locked section: for a part waiting on its section, where it opens from and, while a
    reading there is unconfirmed, what opens it; otherwise the engine's general note."""
    waiting = _waiting_on(section, completed, answers, sections, moved_past)
    if waiting is None or not _requires_met(section, completed):
        return "Complete what comes before this to open it."
    title = text_for(waiting.section["title"], role)
    if waiting.holding is not None and BLOCK_TYPES[waiting.holding["type"]].opens_what_follows:
        return f"Opens from {title}, once you've read the passages."
    return f"Opens from {title}."


def complete_sections(sections, answers, completed):
    """✨ The sections that are complete: those the participant completed, and each part of a section whose gate passes.

    A part has no completion of its own (ticket 41b), as the original prototype's Strengths assessment has none within
    Section 1, so it is complete exactly when its gate passes, worked out here rather than stored.
    """
    parts_done = {section["id"] for section in sections if "part_of" in section and gate_passes(section, answers)}
    return set(completed) | parts_done


def hub_for(sections, answers, completed, role="participant", moved_past=None):
    """✨ A participant's hub over one track's sections. `moved_past` holds, by section, the pages moved past."""
    moved_past = moved_past or {}
    completed = complete_sections(sections, answers, completed)
    states = [_state(section, answers, completed, role, moved_past, sections) for section in sections]
    next_step = next((state for state in states if state.status in (NOT_STARTED, IN_PROGRESS)), None)
    states = [state._replace(is_next=state is next_step) for state in states]
    interactive = [block for section in sections for block in _interactive_blocks(section)]
    return Hub(
        sections=tuple(states),
        next_step=next((state for state in states if state.is_next), None),
        answered=sum(1 for block in interactive if has_content(answers.get(block["id"]))),
        total=len(interactive),
    )


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
    )


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
    if any(has_content(answers.get(block["id"])) for block in _interactive_blocks(section)):
        return IN_PROGRESS
    return NOT_STARTED


def _interactive_blocks(section):
    """✨ The blocks the participant does something with. Progress counts these and no others."""
    return [block for block in section["blocks"] if BLOCK_TYPES[block["type"]].is_interactive]
