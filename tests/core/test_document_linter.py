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


def test_a_pathway_without_a_sort_needs_no_scoring_method():
    document = pathway_document()
    assert "scoring" not in document["measurement"]

    assert validate(document) == []
