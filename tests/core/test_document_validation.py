from engine.document import Problem, validate
from tests.documents import pathway_document


def test_a_well_formed_document_has_no_problems():
    assert validate(pathway_document()) == []


def test_a_missing_field_is_reported_where_it_belongs():
    document = pathway_document()
    del document["content"]["sections"][1]["title"]

    assert validate(document) == [
        Problem(path="/content/sections/1", message="'title' is a required property")
    ]


def test_a_field_the_format_does_not_define_is_refused_so_nothing_executable_can_be_added():
    document = pathway_document()
    document["content"]["sections"][0]["blocks"][0]["onload"] = "alert('x')"

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/0"
    assert "'onload' was unexpected" in problem.message


def test_a_block_type_the_engine_does_not_know_is_refused():
    document = pathway_document()
    document["content"]["sections"][0]["blocks"][0]["type"] = "script"

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/0/type"


def test_role_keyed_text_must_name_the_participant_wording_and_only_known_roles():
    document = pathway_document()
    document["title"] = {"observer": "Their pathway"}
    document["instrument"]["items"][0]["text"] = {"participant": "Pioneering", "coach": "Pioneering"}

    assert [problem.path for problem in validate(document)] == ["/instrument/items/0/text", "/title"]


def test_an_identifier_must_be_a_name_and_never_a_position():
    document = pathway_document()
    document["content"]["sections"][0]["id"] = "0"

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/id"
