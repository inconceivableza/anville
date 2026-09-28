"""✨ *Whatever You Do* as the content owner now wants it, which adds a fifth rating the original prototype does not have.

After the first demo the content owner asked for a fifth statement, asked at the start and again at the end, to
see whether a participant trusts God's plan more, not less, once they have been through the pathway. The faithful
port keeps the original prototype's four, and the last test here keeps the two documents from drifting apart in
any other way, so each can keep growing and be compared once everything is built.
"""

import json
from pathlib import Path

import pytest
from django.utils.html import escape

from engine.models import Response
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_whatever_you_do_faithful_port import (
    A_LETTER,
    A_STATEMENT,
    ANSWER_ALL_FOUR,
    BASELINE_STATEMENTS,
    answer,
    complete,
)
from tests.journeys.test_whatever_you_do_faithful_port import SLOTS as PROTOTYPE_SLOTS
from tests.journeys.test_whatever_you_do_faithful_port import the_pathway as the_faithful_port

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"

PEACE = "I am at peace with God's plan for my life"
ANSWER_ALL_FIVE = "Answer all five to continue"
# ✨ The prototype's two minimum-length messages, each with how much is needed added.
SAYS_HOW_MUCH = {
    "Write your calling statement to continue.": "Write your calling statement (at least 10 characters) to continue.",
    "Write at least one part of your letter before sealing it.": (
        "Write at least one part of your letter (10 characters or more) before sealing it."
    ),
}
SLOTS = (*PROTOTYPE_SLOTS, "peace")


def the_pathway():
    return json.loads(DOCUMENT.read_text(encoding="utf-8"))


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(the_pathway())
    return signed_in_client


def answer_all_five(client, prefix="bl"):
    for slot in SLOTS:
        answer(client, f"{prefix}-{slot}", "7")


def through_to_the_letter(client):
    answer_all_five(client)
    complete(client, "onboarding")
    answer(client, "s2a-reading", "true")
    answer(client, "cl-statement", A_STATEMENT)
    complete(client, "calling")
    return client


@pytest.mark.django_db
def test_the_fifth_statement_is_asked_after_the_original_prototypes_four(participant):
    page = participant.get("/sections/onboarding/").content.decode()

    for statement in BASELINE_STATEMENTS.values():
        assert escape(statement) in page
    assert page.index(escape(BASELINE_STATEMENTS["bl-plan"])) < page.index(escape(PEACE))
    assert page.count("Strongly disagree") == 5


@pytest.mark.django_db
def test_all_five_ratings_are_needed_before_the_participant_may_continue(participant):
    for slot in PROTOTYPE_SLOTS:
        answer(participant, f"bl-{slot}", "5")

    refused = complete(participant, "onboarding")

    assert refused.status_code == 400
    assert refused.content.decode().count(ANSWER_ALL_FIVE) == 1
    assert "onboarding" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_the_way_on_opens_once_all_five_are_answered(participant):
    answer_all_five(participant)

    assert complete(participant, "onboarding").status_code == 303


@pytest.mark.django_db
def test_the_fifth_statement_is_asked_again_at_the_end(participant):
    page = through_to_the_letter(participant).get("/sections/letter/").content.decode()

    assert escape(PEACE) in page
    assert page.count("Strongly disagree") == 5


@pytest.mark.django_db
def test_the_letter_cannot_be_sent_without_the_fifth_after_rating(participant):
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    for slot in PROTOTYPE_SLOTS:
        answer(client, f"pl-{slot}", "8")

    refused = complete(client, "letter")

    assert refused.status_code == 400
    assert refused.content.decode().count(ANSWER_ALL_FIVE) == 1

    answer(client, "pl-peace", "8")
    assert complete(client, "letter").status_code == 303


@pytest.mark.django_db
def test_progress_counts_the_two_new_ratings(participant):
    assert "0 of 16 answered" in participant.get("/").content.decode()  # ✨ the faithful port's 14, and two more


@pytest.mark.django_db
def test_all_five_start_ratings_are_fixed_once_onboarding_is_complete(participant):
    answer_all_five(participant)
    complete(participant, "onboarding")

    for slot in SLOTS:
        assert answer(participant, f"bl-{slot}", "2").status_code == 409
    assert set(Response.objects.get().answers.values()) == {7}


@pytest.mark.django_db
def test_all_five_end_ratings_are_fixed_once_the_letter_is_sent(participant):
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    answer_all_five(client, prefix="pl")
    complete(client, "letter")

    for slot in SLOTS:
        assert answer(client, f"pl-{slot}", "2").status_code == 409
    assert {Response.objects.get().answers[f"pl-{slot}"] for slot in SLOTS} == {7}


def test_every_section_but_section_1_says_how_long_it_takes():
    """✨ Our own figures, not the prototype's, which gave none: to confirm with the owner. A section that is not
    mostly built yet says "? min" until it is (Sections 2 and 4, Section 3's sentence builder, and the letter,
    until it has been timed by hand). Section 1 has none: it cannot be finished without the sort, so its own
    few minutes would read as less than the Strengths assessment it leads to."""
    sections = the_pathway()["content"]["sections"]

    assert {section["id"]: section.get("estimate") for section in sections} == {
        "onboarding": "About 1 minute",
        "designed": None,
        "strengths": "About 10 minutes",
        "shape": "? min",
        "calling": "? min",
        "growth": "? min",
        "letter": "? min",
    }


def test_the_letter_and_the_closing_ratings_each_say_how_long_they_take():
    """✨ The letter section is the only one with two activities, so each carries its own estimate, on the
    block that starts it. A scripture reading leads into an activity rather than being one (the spec)."""
    estimated = [
        (section["id"], block["id"], block["estimate"])
        for section in the_pathway()["content"]["sections"]
        for block in section["blocks"]
        if block.get("estimate")
    ]

    assert estimated == [("letter", "lt-task", "? min"), ("letter", "pl-intro", "? min")]


def without_estimates(document):
    """✨ The faithful port has no estimates, since the prototype gave none."""
    for section in document["content"]["sections"]:
        section.pop("estimate", None)
        for block in section["blocks"]:
            block.pop("estimate", None)
    return document


def test_the_pathway_is_the_faithful_port_with_a_fifth_rating_and_nothing_else():
    """✨ The fifth rating is added to the faithful port here and the result compared whole, so a change made to
    one document and not the other fails, and so does a slip in the fifth rating itself (its place, its anchors,
    its gate clause, or a message still saying four). The minimum-length messages are reworded the same way,
    and the time estimates, checked above, are set aside."""
    expected = the_faithful_port()
    for section in expected["content"]["sections"]:
        for clause in section.get("gate", {}).get("clauses", []):
            clause["message"] = SAYS_HOW_MUCH.get(clause["message"], clause["message"])
    for section_id, prefix in (("onboarding", "bl"), ("letter", "pl")):
        section = next(section for section in expected["content"]["sections"] if section["id"] == section_id)
        blocks = section["blocks"]
        plan = next(index for index, block in enumerate(blocks) if block["id"] == f"{prefix}-plan")
        blocks.insert(plan + 1, {**blocks[plan], "id": f"{prefix}-peace", "prompt": PEACE})
        clauses = section["gate"]["clauses"]
        for clause in clauses:
            if clause["message"] == ANSWER_ALL_FOUR:
                clause["message"] = ANSWER_ALL_FIVE
        clauses.append({"type": "has_answer", "block": f"{prefix}-peace", "message": ANSWER_ALL_FIVE})

    assert without_estimates(the_pathway()) == expected
