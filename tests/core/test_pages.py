"""✨ Pages within a section (ticket 33): how an author splits one, and what a participant has reached of it.

A `page_break` block between blocks starts a new page. A section without one is one page, exactly as before. These
are the derivation itself, with no browser and no database; what a participant may open over HTTP is in
tests/journeys/test_pages.py.
"""

from engine.document import Problem, checklist, unmet, validate
from engine.document.blocks import page_of, pages_of
from engine.hub import hub_for, open_blocks, page_reached
from tests.core.test_hub import long_text, prose, reading, section
from tests.documents import pathway_document


def page_break(id):
    return {"id": id, "type": "page_break"}


def ids(blocks):
    return [block["id"] for block in blocks]


THREE_PAGES = section(
    "onboarding",
    blocks=[long_text("a"), long_text("b"), page_break("to-2"), prose("c"), page_break("to-3"), long_text("d")],
)


# How a section is split


def test_a_section_without_a_page_break_is_one_page():
    assert [ids(page) for page in pages_of(section("first", blocks=[long_text("a"), prose("b")]))] == [["a", "b"]]


def test_each_page_break_starts_a_new_page_and_is_not_itself_on_any():
    assert [ids(page) for page in pages_of(THREE_PAGES)] == [["a", "b"], ["c"], ["d"]]


def test_a_block_is_on_the_page_its_break_puts_it_on_counting_from_one():
    assert [page_of(THREE_PAGES, block_id) for block_id in ("a", "b", "c", "d")] == [1, 1, 2, 3]


# The page reached


def test_a_participant_starts_on_the_first_page():
    assert page_reached(THREE_PAGES, set()) == 1


def test_going_on_from_a_page_reaches_the_next():
    assert page_reached(THREE_PAGES, {1}) == 2
    assert page_reached(THREE_PAGES, {1, 2}) == 3


def test_the_page_reached_is_never_beyond_the_last():
    assert page_reached(THREE_PAGES, {1, 2, 3}) == 3


def test_a_page_is_reached_only_through_every_page_ahead_of_it():
    assert page_reached(THREE_PAGES, {2}) == 1


def test_only_the_pages_reached_are_open():
    blocks, all_of_it = open_blocks(THREE_PAGES, {}, [THREE_PAGES], up_to_page=2)

    assert ids(blocks) == ["a", "b", "c"]
    assert all_of_it is True


def test_a_participant_who_has_moved_past_nothing_has_only_the_first_page_open():
    blocks, _ = open_blocks(THREE_PAGES, {}, [THREE_PAGES])

    assert ids(blocks) == ["a", "b"]


def test_an_unconfirmed_reading_still_holds_back_the_pages_after_it():
    held = section("held", blocks=[reading("read"), page_break("to-2"), long_text("a")])

    blocks, all_of_it = open_blocks(held, {}, [held], up_to_page=2)

    assert ids(blocks) == ["read"]
    assert all_of_it is False


def test_the_hub_leads_to_the_page_the_participant_has_reached():
    [state] = hub_for([THREE_PAGES], {}, completed=[], moved_past={"onboarding": {1}}).sections

    assert state.page == 2


def test_the_hub_leads_to_the_first_page_of_a_section_nobody_has_moved_past_any_of():
    [state] = hub_for([THREE_PAGES], {}, completed=[]).sections

    assert state.page == 1


def test_progress_counts_a_sections_blocks_on_every_page_and_not_its_page_breaks():
    hub = hub_for([THREE_PAGES], {"a": "Written", "d": "Written"}, completed=[])

    assert (hub.answered, hub.total) == (2, 3)


# The gate, page by page


def gated(section, *clauses):
    return {
        **section,
        "gate": {
            "clauses": [{"type": "has_answer", "block": block, "message": message} for block, message in clauses]
        },
    }


PAGED_GATE = gated(
    THREE_PAGES,
    ("a", "Answer a."),
    ("d", "Answer d."),
    ("elsewhere", "Do the thing in another section."),
    ("b", "Answer b."),
)


def test_a_page_is_held_by_the_clauses_naming_its_own_blocks():
    assert unmet(PAGED_GATE, {}, page=1) == ["Answer a.", "Answer b."]


def test_a_page_whose_blocks_no_clause_names_holds_nothing():
    assert unmet(PAGED_GATE, {}, page=2) == []


def test_a_clause_naming_a_block_in_another_section_is_checked_on_the_last_page():
    assert unmet(PAGED_GATE, {}, page=3) == ["Answer d.", "Do the thing in another section."]


def test_the_whole_gate_is_still_what_completing_the_section_checks():
    assert unmet(PAGED_GATE, {"d": "Written", "elsewhere": "Done"}) == ["Answer a.", "Answer b."]


def test_a_pages_checklist_lists_its_own_clauses_met_or_not():
    assert checklist(PAGED_GATE, {"a": "Written"}, page=1) == [("Answer a.", True), ("Answer b.", False)]


def test_the_last_pages_checklist_also_lists_anything_left_unmet_on_an_earlier_page():
    """✨ Completing checks the whole gate, so a rating cleared after going back is said where the button is."""
    answers = {"b": "Written", "d": "Written"}

    assert checklist(PAGED_GATE, answers, page=3) == [
        ("Answer d.", True),
        ("Do the thing in another section.", False),
        ("Answer a.", False),
    ]


# Authoring


def with_blocks(*blocks):
    document = pathway_document()
    document["content"]["sections"][0]["blocks"] = [
        {"id": "welcome", "type": "rich_text", "body": "Welcome to the pathway."},
        *blocks,
    ]
    return document


def test_a_page_break_between_blocks_is_well_formed():
    document = with_blocks(page_break("to-2"), {"id": "more", "type": "rich_text", "body": "More."})

    assert validate(document) == []


def test_a_page_break_carries_nothing_but_its_identifier():
    document = with_blocks({**page_break("to-2"), "title": "Page two"}, {"id": "more", "type": "rich_text", "body": "."})

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/1"
    assert "'title' was unexpected" in problem.message


def test_a_page_break_ending_a_section_is_reported_since_it_leaves_an_empty_page():
    assert validate(with_blocks(page_break("to-2"))) == [
        Problem(path="/content/sections/0/blocks/1", message="A page break must come between blocks, not leave a page empty.")
    ]


def test_a_page_break_starting_a_section_is_reported():
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].insert(0, page_break("to-1"))

    assert validate(document) == [
        Problem(path="/content/sections/0/blocks/0", message="A page break must come between blocks, not leave a page empty.")
    ]


def test_two_page_breaks_together_are_reported():
    document = with_blocks(page_break("to-2"), page_break("to-3"), {"id": "more", "type": "rich_text", "body": "."})

    assert validate(document) == [
        Problem(path="/content/sections/0/blocks/2", message="A page break must come between blocks, not leave a page empty.")
    ]


def test_a_page_break_shares_the_blocks_identifiers_so_two_cannot_clash():
    document = with_blocks(page_break("welcome"), {"id": "more", "type": "rich_text", "body": "."})

    assert validate(document) == [
        Problem(
            path="/content/sections/0/blocks/1/id",
            message="The block identifier 'welcome' is already used at /content/sections/0/blocks/0/id.",
        )
    ]


def test_a_gate_clause_cannot_name_a_page_break():
    document = with_blocks(page_break("to-2"), {"id": "more", "type": "rich_text", "body": "."})
    document["content"]["sections"][0]["gate"] = {
        "clauses": [{"type": "has_answer", "block": "to-2", "message": "Go on."}]
    }

    assert validate(document) == [
        Problem(
            path="/content/sections/0/gate/clauses/0/block",
            message="A 'has_answer' clause cannot be checked against block 'to-2', which is a page_break.",
        )
    ]
