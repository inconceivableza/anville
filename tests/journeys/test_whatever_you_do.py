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
from tests.journeys.test_whatever_you_do_faithful_port import the_pathway as the_faithful_port

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"

PEACE = "I am at peace with God's plan for my life"
ANSWER_ALL_FIVE = "Answer all five to continue"
SLOTS = ("bible", "gifts", "call", "plan", "peace")


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
    for slot in SLOTS[:4]:
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
    for slot in SLOTS[:4]:
        answer(client, f"pl-{slot}", "8")

    refused = complete(client, "letter")

    assert refused.status_code == 400
    assert refused.content.decode().count(ANSWER_ALL_FIVE) == 1

    answer(client, "pl-peace", "8")
    assert complete(client, "letter").status_code == 303


@pytest.mark.django_db
def test_progress_counts_the_two_new_ratings(participant):
    assert "0 of 13 answered" in participant.get("/").content.decode()


def test_the_pathway_is_the_faithful_port_with_a_fifth_rating_and_nothing_else():
    """✨ The fifth rating is added to the faithful port here and the result compared whole, so a change made to
    one document and not the other fails, and so does a slip in the fifth rating itself (its place, its anchors,
    its gate clause, or a message still saying four)."""
    expected = the_faithful_port()
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

    assert the_pathway() == expected
