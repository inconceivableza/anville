"""✨ The hub: the engine's view of where a participant has got to.

A hub is derived from the pathway's sections and what the participant has answered and completed. None of
it is an authored block (CONTEXT.md), so an author cannot write a status, a lock or a next-step banner, and
cannot accidentally leave one out. Nothing here touches the database or a request: the same derivation
serves the hub page, the guard on a section page and the re-check when a section is completed.
"""

from typing import NamedTuple

from engine.document.blocks import BLOCK_TYPES
from engine.document.gates import has_content
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
    """✨ One section as the hub sees it. `is_next` marks the one section the hub points the participant at."""

    id: str
    title: str
    status: str
    label: str
    is_next: bool = False

    @property
    def is_locked(self):
        return self.status == LOCKED


class Hub(NamedTuple):
    sections: tuple
    next_step: SectionState | None
    answered: int
    of: int


def track_sections(document):
    """✨ The sections of the participant's track.

    Until a participant can choose a track (ticket 23), a track is the whole pathway. Everything that
    counts sections or blocks goes through here, so choosing a track later changes this function alone.
    """
    return document["content"]["sections"]


def section_by_id(document, section_id):
    """✨ The section with this identifier within the participant's track, or None."""
    return next((section for section in track_sections(document) if section["id"] == section_id), None)


def is_locked(section, completed):
    """✨ Whether a section is still shut, because a section it requires has not been completed."""
    return not set(section.get("requires", [])) <= set(completed)


def hub_for(sections, answers, completed, role="participant"):
    """✨ A participant's hub over one track's sections."""
    states = [_state(section, answers, completed, role) for section in sections]
    next_step = next((state for state in states if state.status in (NOT_STARTED, IN_PROGRESS)), None)
    states = [state._replace(is_next=state is next_step) for state in states]
    interactive = [block for section in sections for block in _interactive_blocks(section)]
    return Hub(
        sections=tuple(states),
        next_step=next((state for state in states if state.is_next), None),
        answered=sum(1 for block in interactive if has_content(answers.get(block["id"]))),
        of=len(interactive),
    )


def _state(section, answers, completed, role):
    status = _status(section, answers, completed)
    return SectionState(
        id=section["id"],
        title=text_for(section["title"], role),
        status=status,
        label=LABELS[status],
    )


def _status(section, answers, completed):
    if section["id"] in completed:
        return COMPLETE  # ✨ completing is the participant's own act, so it outlasts any later change
    if is_locked(section, completed):
        return LOCKED
    if any(has_content(answers.get(block["id"])) for block in _interactive_blocks(section)):
        return IN_PROGRESS
    return NOT_STARTED


def _interactive_blocks(section):
    """✨ The blocks the participant does something with. Progress counts these and no others."""
    return [block for block in section["blocks"] if BLOCK_TYPES[block["type"]].is_interactive]
