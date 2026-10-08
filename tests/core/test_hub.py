"""✨ The hub is derived, never authored (CONTEXT.md): status, locks, the next step and progress.

These are the derivation itself, with no browser and no database. What a participant is actually allowed
to open is enforced separately, over HTTP, in tests/journeys/test_sections.py.
"""

import pytest

from engine.hub import COMPLETE, IN_PROGRESS, LOCKED, NOT_STARTED, hub_for, is_locked, open_blocks


def section(id, requires=(), blocks=()):
    return {"id": id, "title": id.title(), "requires": list(requires), "blocks": list(blocks)}


def long_text(id):
    return {"id": id, "type": "long_text", "prompt": "Write something."}


def prose(id):
    return {"id": id, "type": "rich_text", "body": "Something to read."}


A_CHAIN = [
    section("first", blocks=[long_text("a")]),
    section("second", requires=["first"], blocks=[long_text("b")]),
    section("third", requires=["second"], blocks=[long_text("c")]),
]


def statuses(sections, answers=None, completed=()):
    return [state.status for state in hub_for(sections, answers or {}, completed).sections]


# Status


def test_a_section_nobody_has_touched_has_not_been_started():
    assert statuses([section("first")]) == [NOT_STARTED]


def test_a_section_with_an_answer_to_one_of_its_blocks_is_in_progress():
    assert statuses(A_CHAIN, answers={"a": "Some writing"}) == [IN_PROGRESS, LOCKED, LOCKED]


def test_a_section_the_participant_completed_is_complete():
    assert statuses(A_CHAIN, completed=["first"]) == [COMPLETE, NOT_STARTED, LOCKED]


def test_an_answer_to_another_sections_block_does_not_make_this_one_in_progress():
    assert statuses(A_CHAIN, answers={"c": "Written"}, completed=["first"]) == [COMPLETE, NOT_STARTED, LOCKED]


def test_a_section_stays_complete_even_once_everything_around_it_has_moved_on():
    assert statuses(A_CHAIN, answers={"a": "Written"}, completed=["first", "second"])[:2] == [COMPLETE, COMPLETE]


# Locks


def test_a_section_is_locked_until_every_section_it_requires_is_complete():
    assert statuses(A_CHAIN) == [NOT_STARTED, LOCKED, LOCKED]
    assert statuses(A_CHAIN, completed=["first"]) == [COMPLETE, NOT_STARTED, LOCKED]
    assert statuses(A_CHAIN, completed=["first", "second"]) == [COMPLETE, COMPLETE, NOT_STARTED]


def test_a_section_requiring_several_sections_waits_for_all_of_them():
    sections = [section("a"), section("b"), section("last", requires=["a", "b"])]

    assert statuses(sections, completed=["a"]) == [COMPLETE, NOT_STARTED, LOCKED]
    assert statuses(sections, completed=["a", "b"]) == [COMPLETE, COMPLETE, NOT_STARTED]


def test_a_section_requiring_nothing_is_never_locked():
    assert is_locked(section("first"), completed=set()) is False


def test_a_section_the_participant_has_completed_is_never_locked_again():
    """✨ Otherwise the hub would call it complete, link to it, and send the participant back here."""
    assert is_locked(section("second", requires=["first"]), completed={"second"}) is False


def test_locks_come_from_what_a_section_requires_and_not_from_its_position():
    """✨ The third section requires nothing, so it opens straight away even though two sit above it."""
    sections = [section("first"), section("second", requires=["first"]), section("third")]

    assert statuses(sections) == [NOT_STARTED, LOCKED, NOT_STARTED]


# The next step


def test_the_next_step_is_the_first_section_that_is_open_and_not_yet_complete():
    assert hub_for(A_CHAIN, {}, completed=[]).next_step.id == "first"
    assert hub_for(A_CHAIN, {}, completed=["first"]).next_step.id == "second"


def test_the_next_step_is_marked_on_the_section_itself_so_the_hub_can_point_at_it():
    [first, second, third] = hub_for(A_CHAIN, {}, completed=["first"]).sections

    assert [first.is_next, second.is_next, third.is_next] == [False, True, False]


def test_a_section_in_progress_is_the_next_step_before_an_untouched_one_further_down():
    assert hub_for(A_CHAIN, {"a": "Started writing"}, completed=[]).next_step.id == "first"


def test_there_is_no_next_step_once_every_section_is_complete():
    assert hub_for(A_CHAIN, {}, completed=["first", "second", "third"]).next_step is None


def test_a_locked_section_is_never_the_next_step():
    """✨ A pathway whose only unfinished sections are locked has nothing to offer, and says so."""
    sections = [section("first"), section("second", requires=["never-completed"])]

    assert hub_for(sections, {}, completed=["first"]).next_step is None


# Progress


def test_progress_counts_the_blocks_the_participant_does_something_with_and_no_others():
    sections = [section("first", blocks=[prose("intro"), long_text("a"), prose("outro"), long_text("b")])]

    hub = hub_for(sections, {"a": "Written"}, completed=[])
    assert (hub.answered, hub.total) == (1, 2)


def test_progress_counts_across_every_section_of_the_track():
    hub = hub_for(A_CHAIN, {"a": "Written", "c": "Written"}, completed=[])

    assert (hub.answered, hub.total) == (2, 3)


@pytest.mark.parametrize("answer", ["", "   ", None])
def test_a_block_left_blank_is_not_counted_as_answered(answer):
    hub = hub_for([section("first", blocks=[long_text("a")])], {"a": answer}, completed=[])

    assert (hub.answered, hub.total) == (0, 1)


def test_a_pathway_with_nothing_interactive_in_it_reports_no_progress_rather_than_dividing_by_zero():
    hub = hub_for([section("first", blocks=[prose("intro")])], {}, completed=[])

    assert (hub.answered, hub.total) == (0, 0)


def test_progress_counts_only_the_sections_it_is_given_so_a_track_counts_only_its_own():
    """✨ Tracks arrive in ticket 23; the hub already counts only the sections handed to it."""
    hub = hub_for(A_CHAIN[:2], {"a": "Written", "c": "Written"}, completed=[])

    assert (hub.answered, hub.total) == (1, 2)


# What a participant has reached within a section


def reading(id):
    return {"id": id, "type": "scripture_reading", "passages": [{"reference": "Psalm 1", "text": "Blessed."}]}


def test_a_section_with_no_reading_in_it_is_open_all_the_way_down():
    first = section("first", blocks=[prose("intro"), long_text("a")])

    blocks, all_of_it = open_blocks(first, {}, [first])

    assert [block["id"] for block in blocks] == ["intro", "a"]
    assert all_of_it is True


def test_an_unconfirmed_reading_holds_back_everything_beneath_it():
    gifts = section("first", blocks=[prose("intro"), reading("read"), long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {}, [gifts])

    assert [block["id"] for block in blocks] == ["intro", "read"]
    assert all_of_it is False


def test_confirming_the_reading_opens_the_rest_of_the_section():
    gifts = section("first", blocks=[prose("intro"), reading("read"), long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {"read": True}, [gifts])

    assert [block["id"] for block in blocks] == ["intro", "read", "a"]
    assert all_of_it is True


def test_a_second_reading_holds_back_what_follows_it_in_turn():
    gifts = section("first", blocks=[reading("first-read"), long_text("a"), reading("second-read"), long_text("b")])

    blocks, all_of_it = open_blocks(gifts, {"first-read": True}, [gifts])

    assert [block["id"] for block in blocks] == ["first-read", "a", "second-read"]
    assert all_of_it is False


def link(id, to, **fields):
    return {"id": id, "type": "section_link", "section": to, **fields}


def gated_on(section, block_id):
    return {**section, "gate": {"clauses": [{"type": "has_answer", "block": block_id, "message": "Do the sort."}]}}


STRENGTHS = gated_on(section("strengths", blocks=[long_text("sort")]), "sort")


def test_a_link_that_holds_what_follows_holds_it_until_the_linked_sections_gate_passes():
    held = link("to-strengths", "strengths", holds_what_follows=True)
    gifts = section("gifts", blocks=[prose("intro"), held, long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {}, [gifts, STRENGTHS])

    assert [block["id"] for block in blocks] == ["intro", "to-strengths"]
    assert all_of_it is False


def test_the_linked_sections_gate_passing_opens_the_rest_without_that_section_being_completed():
    """✨ As in the prototype, the reflection opens once the sort is in, not once its section is marked complete."""
    gifts = section("gifts", blocks=[link("to-strengths", "strengths", holds_what_follows=True), long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {"sort": "Sorted"}, [gifts, STRENGTHS])

    assert [block["id"] for block in blocks] == ["to-strengths", "a"]
    assert all_of_it is True


def test_a_held_link_to_a_section_with_no_gate_holds_nothing_back():
    """✨ A section with no gate may always be completed, so there is nothing to wait for."""
    ungated = section("strengths", blocks=[long_text("sort")])
    gifts = section("gifts", blocks=[link("to-strengths", "strengths", holds_what_follows=True), long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {}, [gifts, ungated])

    assert [block["id"] for block in blocks] == ["to-strengths", "a"]
    assert all_of_it is True


def test_a_link_holds_nothing_back_unless_its_author_asks_it_to():
    gifts = section("gifts", blocks=[link("to-strengths", "strengths"), long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {}, [gifts, STRENGTHS])

    assert [block["id"] for block in blocks] == ["to-strengths", "a"]
    assert all_of_it is True


# A part of a section


def test_a_part_of_a_section_is_complete_once_its_gate_passes_with_nothing_stored():
    """✨ The Strengths assessment within Section 1 (ticket 41b): it has no "Mark complete" of its own."""
    part = {**STRENGTHS, "part_of": "gifts", "requires": []}
    sections = [section("gifts", blocks=[link("to-strengths", "strengths")]), part]

    assert statuses(sections)[1] == NOT_STARTED
    assert statuses(sections, answers={"sort": "Sorted"}, completed=[])[1] == COMPLETE


def test_a_part_is_locked_until_the_participant_reaches_its_sections_link_to_it():
    """✨ As the prototype opens the Strengths assessment only from Section 1, once its passages are read (ticket 41b)."""
    part = {**STRENGTHS, "part_of": "gifts"}
    gifts = section("gifts", blocks=[reading("read"), link("to-strengths", "strengths"), long_text("a")])

    assert statuses([gifts, part])[1] == LOCKED
    assert statuses([gifts, part], answers={"read": True})[1] == NOT_STARTED


# What the hub says about each section


def test_each_section_carries_its_title_and_a_label_for_its_status():
    [first, second, _] = hub_for(A_CHAIN, {}, completed=[]).sections

    assert (first.id, first.title, first.label) == ("first", "First", "Not started")
    assert second.label == "Locked"


def test_a_sections_title_is_shown_in_the_participants_own_wording():
    sections = [{"id": "first", "title": {"participant": "Your gifts", "observer": "Their gifts"}, "blocks": []}]

    assert hub_for(sections, {}, completed=[]).sections[0].title == "Your gifts"
