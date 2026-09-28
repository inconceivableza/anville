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


def test_an_agreement_scale_needs_its_prompt_and_both_anchor_labels():
    document = pathway_document()
    del document["content"]["sections"][0]["blocks"][1]["max_label"]

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/1"
    assert "'max_label' is a required property" in problem.message


def test_a_bucket_seed_is_a_whole_number_since_it_becomes_an_untouched_sliders_answer():
    document = pathway_document()
    document["instrument"]["buckets"][0]["seed"] = 45.5

    [problem] = validate(document)
    assert problem.path == "/instrument/buckets/0/seed"


def test_rich_text_may_be_set_off_as_a_hint_and_nothing_else():
    """✨ A note beneath scripture belongs to the scripture reading block, so rich text no longer offers one."""
    document = pathway_document()
    welcome = document["content"]["sections"][0]["blocks"][0]
    welcome.update(variant="hint", label="The big question")
    assert validate(document) == []

    welcome["variant"] = "banner"
    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/0/variant"


def test_an_agreement_scale_may_be_fixed_once_its_section_is_complete_by_a_yes_or_no():
    document = pathway_document()
    rating = document["content"]["sections"][0]["blocks"][1]
    rating["fixed_once_complete"] = True
    assert validate(document) == []

    rating["fixed_once_complete"] = "yes"
    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/1/fixed_once_complete"


def test_a_section_link_may_carry_a_button_label_and_hold_what_follows_by_a_yes_or_no():
    document = pathway_document()
    document["content"]["sections"][1]["blocks"].insert(
        0,
        {
            "id": "to-onboarding",
            "type": "section_link",
            "section": "onboarding",
            "button_label": "Open Strengths Assessment →",
            "holds_what_follows": True,
        },
    )
    assert validate(document) == []

    document["content"]["sections"][1]["blocks"][0]["holds_what_follows"] = "yes"
    [problem] = validate(document)
    assert problem.path == "/content/sections/1/blocks/0/holds_what_follows"
