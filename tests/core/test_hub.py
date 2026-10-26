# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The hub is derived, never authored (CONTEXT.md): status, locks, the next step and progress.

These are the derivation itself, with no browser and no database. What a participant is actually allowed
to open is enforced separately, over HTTP, in tests/journeys/test_sections.py.
"""

import pytest
from django.utils.html import conditional_escape

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


def test_progress_counts_the_sections_complete_not_the_answers():
    """✨ "2 of 5 sections complete", as the prototype's hub says (ticket 49a)."""
    hub = hub_for(A_CHAIN, {"a": "Written", "b": "Written", "c": "Written"}, completed=["first"])

    assert (hub.complete, hub.total) == (1, 3)


@pytest.mark.parametrize("answer", ["", "   ", None])
def test_a_block_left_blank_does_not_start_its_section(answer):
    assert statuses([section("first", blocks=[long_text("a")])], {"a": answer}) == [NOT_STARTED]


def test_prose_alone_does_not_start_a_section():
    assert statuses([section("first", blocks=[prose("intro")])], {"intro": "Read"}) == [NOT_STARTED]


def test_progress_counts_only_the_sections_it_is_given_so_a_track_counts_only_its_own():
    """✨ Tracks arrive in ticket 23; the hub already counts only the sections handed to it."""
    hub = hub_for(A_CHAIN[:2], {}, completed=["first", "third"])

    assert (hub.complete, hub.total) == (1, 2)


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


def signpost(id, to, **fields):
    return {"id": id, "type": "section_signpost", "section": to, **fields}


def gated_on(section, block_id):
    return {**section, "gate": {"clauses": [{"type": "has_answer", "block": block_id, "message": "Do the sort."}]}}


STRENGTHS = gated_on(section("strengths", blocks=[long_text("sort")]), "sort")


def test_a_signpost_that_holds_what_follows_holds_it_until_the_linked_sections_gate_passes():
    held = signpost("to-strengths", "strengths", holds_what_follows=True)
    gifts = section("gifts", blocks=[prose("intro"), held, long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {}, [gifts, STRENGTHS])

    assert [block["id"] for block in blocks] == ["intro", "to-strengths"]
    assert all_of_it is False


def test_the_linked_sections_gate_passing_opens_the_rest_without_that_section_being_completed():
    """✨ As in the prototype, the reflection opens once the sort is in, not once its section is marked complete."""
    gifts = section("gifts", blocks=[signpost("to-strengths", "strengths", holds_what_follows=True), long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {"sort": "Sorted"}, [gifts, STRENGTHS])

    assert [block["id"] for block in blocks] == ["to-strengths", "a"]
    assert all_of_it is True


def test_a_holding_signpost_to_a_section_with_no_gate_holds_nothing_back():
    """✨ A section with no gate may always be completed, so there is nothing to wait for."""
    ungated = section("strengths", blocks=[long_text("sort")])
    gifts = section("gifts", blocks=[signpost("to-strengths", "strengths", holds_what_follows=True), long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {}, [gifts, ungated])

    assert [block["id"] for block in blocks] == ["to-strengths", "a"]
    assert all_of_it is True


def test_a_signpost_holds_nothing_back_unless_its_author_asks_it_to():
    gifts = section("gifts", blocks=[signpost("to-strengths", "strengths"), long_text("a")])

    blocks, all_of_it = open_blocks(gifts, {}, [gifts, STRENGTHS])

    assert [block["id"] for block in blocks] == ["to-strengths", "a"]
    assert all_of_it is True


# A part of a section


def test_a_part_of_a_section_is_complete_once_its_gate_passes_with_nothing_stored():
    """✨ The Strengths assessment within Section 1 (ticket 41b): it has no "Mark complete" of its own."""
    part = {**STRENGTHS, "part_of": "gifts", "requires": []}
    sections = [section("gifts", blocks=[signpost("to-strengths", "strengths")]), part]

    assert statuses(sections)[1] == NOT_STARTED
    assert statuses(sections, answers={"sort": "Sorted"}, completed=[])[1] == COMPLETE


def test_a_part_is_locked_until_the_participant_reaches_its_sections_signpost_to_it():
    """✨ As the prototype opens the Strengths assessment only from Section 1, once its passages are read (ticket 41b)."""
    part = {**STRENGTHS, "part_of": "gifts"}
    gifts = section("gifts", blocks=[reading("read"), signpost("to-strengths", "strengths"), long_text("a")])

    assert statuses([gifts, part])[1] == LOCKED
    assert statuses([gifts, part], answers={"read": True})[1] == NOT_STARTED


# A hub side card


def side_card(id, requires=()):
    return {**gated_on(section(id, requires, blocks=[long_text("sort")]), "sort"), "side_card": {"sentence": "Go on."}}


def test_a_side_card_is_complete_once_its_gate_passes_with_nothing_pressed():
    """✨ Walk with a coach and Five trusted voices (ticket 52): complete once their links are made."""
    sections = [section("first"), side_card("card")]

    assert statuses(sections)[1] == NOT_STARTED
    assert statuses(sections, answers={"sort": "Sorted"})[1] == COMPLETE


def test_a_side_card_whose_gate_passes_stays_locked_while_a_section_it_requires_is_not_complete():
    sections = [section("first"), side_card("card", requires=["first"])]

    assert statuses(sections, answers={"sort": "Sorted"})[1] == LOCKED
    assert statuses(sections, answers={"sort": "Sorted"}, completed=["first"])[1] == COMPLETE


def lock_note(sections, completed=(), title_of="last"):
    return next(state for state in hub_for(sections, {}, completed).sections if state.id == title_of).lock_note


def test_with_a_once_only_section_complete_and_left_out_the_waits_on_answers_and_on_the_coach_name_the_right_sections():
    """✨ The hub pairs each section it lists with its own state, not with the section before it (ticket 69, fix-2)."""
    onboarding = {**section("onboarding"), "wizard": True, "once_only": True}
    reflection = {
        **long_text("reflection"),
        "after_comparison": {"sort": "sort", "message": "This opens once you've seen how others see you."},
    }
    designed = {**section("designed", requires=["onboarding"], blocks=[reflection])}
    designed["gate"] = {"clauses": [{"type": "has_answer", "block": "reflection", "message": "Write it."}]}
    calling = section("calling", requires=["onboarding"], blocks=[long_text("statement")])
    calling["opens_when"] = {"clauses": [{"type": "coach_accepted", "block": "coach", "message": "Wait for your coach."}]}

    hub = hub_for([onboarding, designed, calling], {}, completed=["onboarding"])

    assert [state.id for state in hub.sections] == ["designed", "calling"]
    assert hub.next_step is None
    assert hub.waiting_on_answers.id == "designed"
    assert hub.coach_wait.section.id == "calling"


def test_a_locked_section_names_the_sections_it_still_waits_for():
    """✨ As Section 2 names Walk with a coach and Five trusted voices once Section 1 is complete (ticket 52)."""
    sections = [section("a"), section("b"), section("c"), section("last", requires=["a", "b", "c"])]

    assert lock_note(sections) == "Opens once you've finished A, B and C."
    assert lock_note(sections, completed=["a"]) == "Opens once you've finished B and C."
    assert lock_note(sections, completed=["a", "b"]) == "Opens once you've finished C."


def phrased(id, phrase, number=None):
    """✨ A section carrying `phrase` as what finishing it takes (ticket 79), and `number` if given."""
    return {**section(id), "to_finish": phrase, **({"number": number} if number else {})}


def test_a_locked_section_names_what_is_left_in_each_section_by_its_phrase_or_else_by_its_title():
    """✨ As Section 2 names the Strengths assessment and both side cards (ticket 79). Sections without a phrase are
    named together, as the faithful port's are."""
    sections = [
        phrased("a", "done the {title}"),
        section("b"),
        phrased("c", "added at least 3 people in {title}"),
        section("d"),
        section("last", requires=["a", "b", "c", "d"]),
    ]

    assert lock_note(sections) == "Opens once you've done the A, finished B and D and added at least 3 people in C."
    assert lock_note(sections, completed=["a", "b"]) == "Opens once you've added at least 3 people in C and finished D."


def test_a_phrase_says_its_sections_links_issued_minimum_where_it_writes_min():
    """✨ So the number is written once, in the section's own `links_issued` clause (ticket 81)."""
    voices = phrased("c", "added at least {min} people in {title}")
    voices["gate"] = {"clauses": [{"type": "links_issued", "block": "contacts", "min": 4, "message": "Add {min}."}]}

    assert lock_note([voices, section("last", requires=["c"])]) == "Opens once you've added at least 4 people in C."


def test_sections_sharing_a_phrase_are_named_together_and_only_those_left():
    """✨ As Section 3 names Sections 1 and 2 (ticket 79)."""
    sections = [
        phrased("a", "completed {section}", number="01"),
        phrased("b", "completed {section}", number="02"),
        section("last", requires=["a", "b"]),
    ]

    assert lock_note(sections) == "Opens once you've completed Sections 1 and 2."
    assert lock_note(sections, completed=["a"]) == "Opens once you've completed Section 2."


def test_every_title_a_note_names_is_in_italics_and_escaped():
    """✨ The note as the page draws it (ticket 79), whether a phrase names the title or not (developer's call, 23 Oct)."""
    sections = [
        {**phrased("a", "added people in {title}"), "title": "<b>Voices</b>"},
        section("b"),
        section("last", requires=["a", "b"]),
    ]

    assert conditional_escape(lock_note(sections)) == (
        "Opens once you&#x27;ve added people in <em>&lt;b&gt;Voices&lt;/b&gt;</em> and finished <em>B</em>."
    )


# What the hub says about each section


def test_each_section_carries_its_title_and_a_label_for_its_status():
    [first, second, _] = hub_for(A_CHAIN, {}, completed=[]).sections

    assert (first.id, first.title, first.label) == ("first", "First", "Not started")
    assert second.label == "Locked"


def test_a_sections_title_is_shown_in_the_participants_own_wording():
    sections = [{"id": "first", "title": {"participant": "Your gifts", "observer": "Their gifts"}, "blocks": []}]

    assert hub_for(sections, {}, completed=[]).sections[0].title == "Your gifts"
