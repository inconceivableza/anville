# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import pytest

from engine.document import Problem, validate
from tests.documents import pathway_document, sort_pathway


def test_an_item_loading_onto_a_construct_that_does_not_exist_is_reported():
    document = pathway_document()
    document["instrument"]["items"][0]["loads"] = ["apostle", "nowhere"]

    assert validate(document) == [
        Problem(path="/instrument/items/0/loads/1", message="There is no construct 'nowhere' in this pathway.")
    ]


def test_a_gate_clause_naming_an_absent_block_is_reported():
    document = pathway_document()
    document["content"]["sections"][1]["gate"]["clauses"][0]["block"] = "missing"

    assert validate(document) == [
        Problem(path="/content/sections/1/gate/clauses/0/block", message="There is no block 'missing' in this pathway.")
    ]


def test_a_section_requiring_a_section_that_does_not_exist_is_reported():
    document = pathway_document()
    document["content"]["sections"][1]["requires"] = ["onboarding", "section-9"]

    assert validate(document) == [
        Problem(path="/content/sections/1/requires/1", message="There is no section 'section-9' in this pathway.")
    ]


def test_a_description_for_a_construct_that_does_not_exist_is_reported():
    document = pathway_document()
    document["presentation"]["constructs"][0]["construct"] = "prophet"

    assert validate(document) == [
        Problem(path="/presentation/constructs/0/construct", message="There is no construct 'prophet' in this pathway.")
    ]


def test_an_item_must_load_onto_exactly_one_construct_in_each_framework():
    document = pathway_document()
    document["measurement"]["frameworks"][0]["constructs"].append({"id": "prophet", "label": "Prophet"})
    document["instrument"]["items"][0]["loads"] = ["apostle", "prophet"]

    assert validate(document) == [
        Problem(path="/instrument/items/0/loads", message="Item 'a5' loads onto 2 constructs in 'apest'; it must load onto exactly one."),
        Problem(path="/instrument/items/0/loads", message="Item 'a5' loads onto no construct in 'pep'; it must load onto exactly one."),
    ]


def test_two_sections_with_the_same_identifier_are_refused():
    document = pathway_document()
    document["content"]["sections"][1]["id"] = "onboarding"

    assert validate(document) == [
        Problem(
            path="/content/sections/1/id",
            message="The section identifier 'onboarding' is already used at /content/sections/0/id.",
        )
    ]


def test_block_identifiers_must_be_unique_across_the_whole_pathway_not_just_their_section():
    document = pathway_document()
    document["content"]["sections"][1]["blocks"][0]["id"] = "welcome"
    document["content"]["sections"][1]["gate"]["clauses"][0]["block"] = "welcome"

    assert validate(document) == [
        Problem(
            path="/content/sections/1/blocks/0/id",
            message="The block identifier 'welcome' is already used at /content/sections/0/blocks/0/id.",
        )
    ]


def test_construct_identifiers_must_be_unique_across_frameworks():
    document = pathway_document()
    document["measurement"]["frameworks"][1]["constructs"][0]["id"] = "apostle"
    document["instrument"]["items"][0]["loads"] = ["apostle"]

    problems = validate(document)
    assert Problem(
        path="/measurement/frameworks/1/constructs/0/id",
        message="The construct identifier 'apostle' is already used at /measurement/frameworks/0/constructs/0/id.",
    ) in problems


def test_duplicate_items_buckets_and_frameworks_are_refused():
    document = pathway_document()
    document["instrument"]["items"].append(dict(document["instrument"]["items"][0]))
    document["instrument"]["buckets"][1]["id"] = "not-me"
    document["measurement"]["frameworks"][1]["id"] = "apest"

    assert [problem.path for problem in validate(document)] == [
        "/instrument/buckets/1/id",
        "/instrument/items/1/id",
        "/measurement/frameworks/1/id",
    ]


def test_cross_references_are_only_checked_once_the_document_has_the_right_shape():
    document = pathway_document()
    document["instrument"]["items"][0]["loads"] = ["apostle", "nowhere"]
    del document["content"]["sections"][1]["gate"]["clauses"][0]["block"]

    assert validate(document) == [
        Problem(path="/content/sections/1/gate/clauses/0", message="'block' is a required property")
    ]


@pytest.mark.parametrize(
    "part, field, needs",
    [
        ("instrument", "buckets", "buckets in its instrument"),
        ("instrument", "items", "items in its instrument"),
        ("measurement", "frameworks", "frameworks in its measurement"),
        ("measurement", "scoring", "a scoring method in its measurement"),
    ],
)
def test_a_sort_in_a_pathway_without_what_it_is_scored_by_is_reported(part, field, needs):
    """✨ Otherwise the document loads, and the participant's page fails when the sort is shown or submitted."""
    document = sort_pathway()
    del document[part][field]

    assert Problem(
        path="/content/sections/2/blocks/0",
        message=f"Block 'strengths-sort' is a sort, so this pathway needs {needs}.",
    ) in validate(document)


def test_a_sort_counts_an_empty_list_as_missing():
    document = sort_pathway()
    document["instrument"]["buckets"] = []

    assert validate(document) == [
        Problem(
            path="/content/sections/2/blocks/0",
            message="Block 'strengths-sort' is a sort, so this pathway needs buckets in its instrument.",
        )
    ]


def test_a_sort_whose_section_could_be_completed_without_it_is_reported():
    """✨ Otherwise a participant could complete the section, and open what follows it, without ever sorting."""
    document = sort_pathway()
    del document["content"]["sections"][2]["gate"]

    assert validate(document) == [
        Problem(
            path="/content/sections/2/blocks/0",
            message="Block 'strengths-sort' is a sort, so its section's gate needs a 'has_answer' clause for it.",
        )
    ]


def results_of(named):
    """✨ The sort pathway with the calling section showing the results of the block `named`."""
    document = sort_pathway()
    document["content"]["sections"][1]["blocks"].append({"id": "shown", "type": "sort_results", "sort": named})
    return document


def test_a_sort_results_block_naming_a_sort_is_accepted():
    assert validate(results_of("strengths-sort")) == []


@pytest.mark.parametrize("named", ["statement", "nowhere"])
def test_a_sort_results_block_naming_anything_but_a_sort_is_reported(named):
    assert validate(results_of(named)) == [
        Problem(path="/content/sections/1/blocks/1/sort", message=f"There is no sort '{named}' in this pathway.")
    ]


def test_a_pathway_without_a_sort_needs_no_scoring_method():
    document = pathway_document()
    assert "scoring" not in document["measurement"]

    assert validate(document) == []


def a_link_to(section_id):
    """✨ The test pathway with a link from the calling section to another section."""
    document = pathway_document()
    document["content"]["sections"][1]["blocks"].append(
        {"id": "to-onboarding", "type": "section_link", "section": section_id, "body": "Go back and look again."}
    )
    return document


def test_a_link_to_a_section_of_the_pathway_is_accepted():
    assert validate(a_link_to("onboarding")) == []


def test_a_link_to_a_section_that_does_not_exist_is_reported():
    assert validate(a_link_to("nowhere")) == [
        Problem(path="/content/sections/1/blocks/1/section", message="There is no section 'nowhere' in this pathway.")
    ]


def a_holding_link_to(section_id):
    """✨ The test pathway with a link at the top of the calling section that holds the statement back."""
    document = pathway_document()
    document["content"]["sections"][1]["blocks"].insert(
        0, {"id": "to-onboarding", "type": "section_link", "section": section_id, "holds_what_follows": True}
    )
    return document


def test_a_link_may_hold_its_section_until_another_section_is_done():
    assert validate(a_holding_link_to("onboarding")) == []


def test_a_link_that_holds_its_own_section_until_that_section_is_done_is_reported():
    """✨ Its gate needs the statement the link is holding back, so the section could never be completed."""
    assert validate(a_holding_link_to("calling")) == [
        Problem(
            path="/content/sections/1/blocks/0/holds_what_follows",
            message="A link cannot hold back the rest of its own section: that section could never be finished.",
        )
    ]


def test_a_link_must_say_which_section_it_leads_to():
    document = a_link_to("onboarding")
    del document["content"]["sections"][1]["blocks"][1]["section"]

    assert validate(document) == [Problem(path="/content/sections/1/blocks/1", message="'section' is a required property")]


def test_a_section_may_be_a_part_of_another_section():
    """✨ The Strengths assessment within Section 1 (ticket 41b)."""
    document = sort_pathway()
    document["content"]["sections"][2]["part_of"] = "calling"

    assert validate(document) == []


def test_a_part_with_no_gate_is_reported():
    """✨ A part is complete once its gate passes, so without one it would be complete before it was ever opened."""
    document = sort_pathway()
    calling = document["content"]["sections"][1]
    calling["part_of"] = "onboarding"
    del calling["gate"]

    assert validate(document) == [
        Problem(
            path="/content/sections/1/part_of",
            message="A part of a section needs a gate: it is complete once its gate passes, so without one it would "
            "be complete before it is begun.",
        )
    ]


@pytest.mark.parametrize(
    "parts, message",
    [
        ({2: "section-9"}, "There is no section 'section-9' in this pathway."),
        ({2: "strengths"}, "A section cannot be a part of itself."),
        ({1: "onboarding", 2: "calling"}, "Section 'calling' is itself a part of a section, so it cannot have parts."),
    ],
)
def test_a_section_that_is_a_part_of_no_section_it_can_be_is_reported(parts, message):
    document = sort_pathway()
    for index, part_of in parts.items():
        document["content"]["sections"][index]["part_of"] = part_of

    assert validate(document) == [Problem(path="/content/sections/2/part_of", message=message)]


# ✨ Hub side cards and section numbers (ticket 49a)


def test_a_section_number_that_is_not_a_number_or_a_range_of_them_is_reported_at_its_path():
    document = pathway_document()
    document["content"]["sections"][1]["number"] = "Section 2"

    assert [problem.path for problem in validate(document)] == ["/content/sections/1/number"]


def test_a_side_card_without_its_sentence_is_reported_at_its_path():
    document = pathway_document()
    document["content"]["sections"][1]["side_card"] = {}

    assert [problem.path for problem in validate(document)] == ["/content/sections/1/side_card"]


def test_a_part_of_a_section_cannot_be_a_side_card_nor_carry_a_number():
    """✨ A part is listed within its section, so it is drawn as no card and shows no number of its own."""
    document = sort_pathway()
    strengths = document["content"]["sections"][2]
    strengths.update(part_of="calling", number="03", side_card={"sentence": "Sort the statements."})

    assert validate(document) == [
        Problem(
            path="/content/sections/2/number",
            message="A part of a section is listed within it, so it shows no number of its own.",
        ),
        Problem(
            path="/content/sections/2/side_card",
            message="A part of a section is listed within it, so it cannot be a hub side card.",
        ),
    ]


def test_a_section_with_parts_cannot_be_a_side_card():
    """✨ Its parts are listed within it, which a card has no room for, so they would be on the hub nowhere."""
    document = sort_pathway()
    document["content"]["sections"][2]["part_of"] = "calling"
    document["content"]["sections"][1]["side_card"] = {"sentence": "Write your statement."}

    assert validate(document) == [
        Problem(
            path="/content/sections/1/side_card",
            message="Section 'calling' has parts, which are listed within it, so it cannot be a hub side card.",
        )
    ]


# ✨ Photos and their credits (ticket 49b)


def with_a_photo(section_id="calling", credit=None):
    document = pathway_document()
    credit = credit if credit is not None else {"kind": "courtesy", "text": "Photograph of grass from Unsplash."}
    document["photos"] = {section_id: {"file": "grass.jpg", "credit": credit}}
    return document


def test_a_photo_named_for_a_section_that_does_not_exist_is_reported():
    assert validate(with_a_photo("nowhere")) == [
        Problem(path="/photos/nowhere", message="There is no section 'nowhere' in this pathway.")
    ]


@pytest.mark.parametrize(
    "credit",
    [
        {"kind": "maybe", "text": "Photograph from Unsplash."},
        {"text": "Photograph from Unsplash."},
        {"kind": "courtesy"},  # ✨ a credit to list needs its wording
        {"kind": "required"},
    ],
)
def test_a_photo_whose_credit_is_not_required_courtesy_or_marked_as_needing_none_is_reported(credit):
    problems = validate(with_a_photo(credit=credit))

    assert problems
    assert all(problem.path.startswith("/photos/calling/credit") for problem in problems)


def test_a_photo_marked_as_needing_no_credit_is_accepted():
    assert validate(with_a_photo(credit={"kind": "none"})) == []
