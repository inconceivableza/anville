import json
from pathlib import Path

import pytest

from engine.document import Problem, validate
from engine.document.blocks import BLOCK_TYPES
from tests.documents import pathway_document

WHATEVER_YOU_DO = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"


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


def a_single_select(**fields):
    return {
        "id": "reason",
        "type": "single_select",
        "prompt": "What's bringing you to the course?",
        "options": [{"id": "exploring", "label": "Generally exploring calling"}],
        **fields,
    }


def test_a_single_select_needs_a_prompt_and_at_least_one_option():
    document = pathway_document()
    blocks = document["content"]["sections"][0]["blocks"]
    blocks.append(a_single_select(placeholder="Select..."))
    assert validate(document) == []

    blocks[-1] = a_single_select(options=[])
    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/2/options"

    del blocks[-1]["prompt"]
    assert "/content/sections/0/blocks/2" in [problem.path for problem in validate(document)]


def test_a_single_select_option_is_named_by_an_identifier_and_labelled_with_authored_text():
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].append(
        a_single_select(options=[{"id": "1st choice", "label": {"participant": "First"}}])
    )

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/2/options/0/id"


def test_a_single_selects_options_may_not_share_an_identifier():
    """✨ The answer is the option's identifier, so two options sharing one could not be told apart."""
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].append(
        a_single_select(options=[{"id": "other", "label": "Other"}, {"id": "other", "label": "Something else"}])
    )

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/2/options/1/id"
    assert "'other'" in problem.message


def test_a_contact_list_needs_nothing_but_may_say_how_many_rows_it_opens_with():
    document = pathway_document()
    blocks = document["content"]["sections"][0]["blocks"]
    blocks.append({"id": "contacts", "type": "contact_list"})
    assert validate(document) == []

    blocks[-1]["min_rows"] = 5
    assert validate(document) == []


@pytest.mark.parametrize("min_rows", [0, 51, "5", 2.5])
def test_a_contact_lists_rows_are_a_whole_number_from_one_to_fifty(min_rows):
    """✨ Fifty is the most a participant may add, so a list may not open with more."""
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].append({"id": "contacts", "type": "contact_list", "min_rows": min_rows})

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/2/min_rows"


def test_a_count_of_entries_may_allow_none_by_a_yes_or_no():
    document = pathway_document()
    onboarding = document["content"]["sections"][0]
    onboarding["blocks"].append({"id": "contacts", "type": "contact_list"})
    clause = {"type": "entry_count", "block": "contacts", "min": 5, "allow_none": True, "message": "Five, or none."}
    onboarding["gate"] = {"clauses": [clause]}
    assert validate(document) == []

    clause["allow_none"] = "yes"
    [problem] = validate(document)
    assert problem.path == "/content/sections/0/gate/clauses/0/allow_none"


def a_coach_question(**fields):
    return {
        "id": "coaching",
        "critical": True,
        "question": "Can ask questions rather than hand out answers",
        "note": "Some people genuinely can't resist solving it for you.",
        "why": "This is the commonest way coaching relationships fail.",
        "coach_note": "Some people genuinely can't resist solving things for others.",
        "coach_why": "This is the commonest way coaching relationships fail.",
        "commitment": "I'll ask the questions in the guide and let them find their own answers.",
        **fields,
    }


def a_coach_checklist(**fields):
    return {
        "id": "coach",
        "type": "coach_checklist",
        "heading": "Walking with a coach",
        "lead": "This choice matters more than any other you'll make in the course.",
        "body": "The work ahead asks you to be honest.\n\nThe wrong choice usually isn't a bad person.",
        "not_needed": "Someone who tells you what they'd do in your position.",
        "needed": "Someone who asks the questions in the material.",
        "footnote": "We say coach rather than mentor deliberately.",
        "name_prompt": "Who are you thinking of asking?",
        "name_placeholder": "Their first name",
        "name_hint": "Just a first name for now.",
        "questions": [a_coach_question()],
        **fields,
    }


def test_a_coach_checklist_carries_its_intro_and_its_questions_as_authored_text():
    document = pathway_document()
    blocks = document["content"]["sections"][0]["blocks"]
    blocks.append(a_coach_checklist(heading={"participant": "Walking with a coach"}))
    assert validate(document) == []

    blocks[-1] = {"id": "coach", "type": "coach_checklist", "heading": "Walking with a coach",
                  "name_prompt": "Who are you thinking of asking?", "questions": [a_coach_question()]}
    assert validate(document) == []


@pytest.mark.parametrize("needed", ["heading", "name_prompt", "questions"])
def test_a_coach_checklist_needs_a_heading_a_name_prompt_and_its_questions(needed):
    document = pathway_document()
    checklist = a_coach_checklist()
    del checklist[needed]
    document["content"]["sections"][0]["blocks"].append(checklist)

    assert "/content/sections/0/blocks/2" in [problem.path for problem in validate(document)]


def test_a_coach_checklist_asks_at_least_one_question():
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].append(a_coach_checklist(questions=[]))

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/2/questions"


@pytest.mark.parametrize("needed", ["id", "question", "why"])
def test_a_coach_question_needs_an_identifier_its_wording_and_why_it_matters(needed):
    """✨ The why is what a stop or a second thought says about the answer, so a question without one cannot be flagged."""
    document = pathway_document()
    question = a_coach_question()
    del question[needed]
    document["content"]["sections"][0]["blocks"].append(a_coach_checklist(questions=[question]))

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/2/questions/0"


def test_a_coach_question_is_critical_by_a_yes_or_no():
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].append(a_coach_checklist(questions=[a_coach_question(critical="yes")]))

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/2/questions/0/critical"


def test_a_coach_checklists_questions_may_not_share_an_identifier():
    """✨ Each answer is sent under its question's identifier, so two questions sharing one could not be told apart."""
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].append(
        a_coach_checklist(questions=[a_coach_question(), a_coach_question(critical=False)])
    )

    [problem] = validate(document)
    assert problem.path == "/content/sections/0/blocks/2/questions/1/id"
    assert "'coaching'" in problem.message


def test_every_section_and_every_kind_of_block_may_carry_a_time_estimate():
    """✨ The Whatever You Do pathway holds a block of every kind, so each gets one here."""
    document = json.loads(WHATEVER_YOU_DO.read_text(encoding="utf-8"))
    for section in document["content"]["sections"]:
        section["estimate"] = "About 15 minutes"
        for block in section["blocks"]:
            block["estimate"] = {"participant": "About 5 minutes"}
    assert {block["type"] for section in document["content"]["sections"] for block in section["blocks"]} == set(
        BLOCK_TYPES
    )

    assert validate(document) == []


def test_a_time_estimate_is_authored_text_not_a_number_of_minutes():
    document = pathway_document()
    document["content"]["sections"][1]["estimate"] = 15
    document["content"]["sections"][1]["blocks"][0]["estimate"] = 5

    assert [problem.path for problem in validate(document)] == [
        "/content/sections/1/blocks/0/estimate",
        "/content/sections/1/estimate",
    ]
