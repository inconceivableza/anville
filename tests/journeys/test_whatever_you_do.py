"""✨ The shipped *Whatever You Do* pathway, read as a participant meets it.

Every other journey test builds its own small document. These read `pathways/whatever-you-do.json`
itself, because what is being checked here is the content: the wording migrated from the prototype,
the gates it asks for, and the locks that follow from its `requires` lists. Nothing here is engine
behaviour that `test_sections.py` does not already cover; it is the slice-1 document doing its job.
"""

import json
from pathlib import Path

import pytest
from django.test import Client
from django.utils.html import escape

from engine.models import Publication, Response
from tests.journeys.test_hub import a_fresh_participant, signed_in_client  # noqa: F401  (a fixture, used by name)

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"

BASELINE_STATEMENTS = {
    "bl-bible": "I have a detailed understanding of what the Bible teaches about 'work' and 'calling'",
    "bl-gifts": "I have a detailed understanding of what my God-given talents/gifts and limitations are",
    "bl-call": "I have a strong sense of what God's specific 'call' and purpose is for my life",
    "bl-plan": (
        "I have a clear, practical plan for how to pursue God's purpose for my life, "
        "in terms of 'work' / 'calling'"
    ),
}
ANSWER_ALL_FOUR = "Answer all four to continue"
A_STATEMENT = "God seems to have designed me to make difficult things clear."
A_LETTER = "Dear me, remember what you found here."


def the_pathway():
    """✨ The shipped document, fresh each time so a test may edit its copy."""
    return json.loads(DOCUMENT.read_text(encoding="utf-8"))


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(the_pathway())
    return signed_in_client


def version():
    return Publication.current_version().pk


def answer(client, block_id, value):
    return client.post(f"/answers/{block_id}/", {"value": value, "version": version()})


def complete(client, section_id):
    return client.post(f"/sections/{section_id}/complete/")


def answer_the_baseline(client, prefix="bl"):
    for slot in ("bible", "gifts", "call", "plan"):
        answer(client, f"{prefix}-{slot}", "7")


def through_to_the_calling_statement(client):
    """✨ A participant who has done the baseline and opened the calling activity."""
    answer_the_baseline(client)
    complete(client, "onboarding")
    answer(client, "s2a-reading", "true")
    return client


def through_to_the_letter(client):
    through_to_the_calling_statement(client)
    answer(client, "cl-statement", A_STATEMENT)
    complete(client, "calling")
    return client


# The four baseline ratings


@pytest.mark.django_db
def test_the_four_baseline_statements_are_asked_with_the_prototypes_wording(participant):
    page = participant.get("/sections/onboarding/").content.decode()

    for statement in BASELINE_STATEMENTS.values():
        assert escape(statement) in page


@pytest.mark.django_db
def test_each_baseline_statement_is_rated_from_one_to_ten_between_its_anchors(participant):
    page = participant.get("/sections/onboarding/").content.decode()

    assert page.count("Strongly disagree") == 4
    assert page.count("Strongly agree") == 4
    for point in range(1, 11):
        assert f'value="{point}"' in page


@pytest.mark.django_db
def test_all_four_baseline_ratings_are_needed_before_the_participant_may_continue(participant):
    for slot in ("bible", "gifts", "call"):
        answer(participant, f"bl-{slot}", "5")

    refused = complete(participant, "onboarding")

    assert refused.status_code == 400
    assert ANSWER_ALL_FOUR in refused.content.decode()
    assert "onboarding" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_the_four_missing_ratings_are_one_sentence_and_not_four(participant):
    """✨ Four `has_answer` clauses share one message, so the participant reads it once."""
    page = participant.get("/sections/onboarding/").content.decode()

    assert page.count(ANSWER_ALL_FOUR) == 1


@pytest.mark.django_db
def test_the_way_on_opens_once_all_four_are_answered(participant):
    answer_the_baseline(participant)

    page = participant.get("/sections/onboarding/").content.decode()
    assert ANSWER_ALL_FOUR not in page

    assert complete(participant, "onboarding").status_code == 303


# The calling-statement section


@pytest.mark.django_db
def test_the_calling_section_reads_the_passages_and_the_task_migrated_from_the_prototype(participant):
    answer_the_baseline(participant)
    complete(participant, "onboarding")

    page = participant.get("/sections/calling/").content.decode()

    assert "First articulate your specific calling" in page
    assert "Matthew 28:18" in page
    assert "Psalm 37:3" in page
    assert escape("I've read these passages and I'm ready to continue") in page


@pytest.mark.django_db
def test_the_statement_activity_waits_for_the_reading_to_be_confirmed(participant):
    answer_the_baseline(participant)
    complete(participant, "onboarding")

    page = participant.get("/sections/calling/").content.decode()
    assert "Now write it in your own words." not in page

    answer(participant, "s2a-reading", "true")
    assert "Now write it in your own words." in participant.get("/sections/calling/").content.decode()


@pytest.mark.django_db
def test_the_calling_gate_asks_for_a_statement_of_at_least_ten_characters(participant):
    client = through_to_the_calling_statement(participant)
    answer(client, "cl-statement", "too short")

    refused = complete(client, "calling")

    assert refused.status_code == 400
    assert "Write your calling statement to continue." in refused.content.decode()


@pytest.mark.django_db
def test_a_long_enough_statement_completes_the_calling_section(participant):
    client = through_to_the_calling_statement(participant)

    answer(client, "cl-statement", A_STATEMENT)

    assert "Write your calling statement to continue." not in client.get("/sections/calling/").content.decode()
    assert complete(client, "calling").status_code == 303
    assert "calling" in Response.objects.get().completed_sections


# The hub: five sections, and locks the server enforces


@pytest.mark.django_db
def test_all_five_sections_appear_on_the_hub(participant):
    page = participant.get("/").content.decode()

    assert escape("Section 1: How you've been designed") in page
    assert "Section 2: The shape of your life" in page
    assert "Section 3: Putting your calling into words" in page
    assert "Section 4: Growth plan" in page
    assert "Section 5: A letter to your future self" in page


@pytest.mark.django_db
def test_the_sections_after_the_calling_statement_are_locked_until_it_is_complete(participant):
    answer_the_baseline(participant)
    complete(participant, "onboarding")

    for section_id in ("growth", "letter"):
        assert participant.get(f"/sections/{section_id}/").status_code == 302


@pytest.mark.django_db
def test_those_locks_lift_when_the_calling_statement_is_complete(participant):
    through_to_the_letter(participant)

    for section_id in ("growth", "letter"):
        assert participant.get(f"/sections/{section_id}/").status_code == 200


@pytest.mark.django_db
def test_a_locked_sections_content_is_refused_however_the_request_arrives(participant):
    """✨ The lock is decided on the request, so neither the page nor the answer is available early."""
    refused = answer(participant, "lt-message", A_LETTER)

    assert refused.status_code == 403
    assert not Response.objects.exists()


# Section 5: the letter, and the four ratings asked again


@pytest.mark.django_db
def test_the_letter_section_asks_for_the_letter_and_then_the_four_statements_again(participant):
    client = through_to_the_letter(participant)

    page = client.get("/sections/letter/").content.decode()

    assert escape("Write to yourself as you will be in twelve months' time") in page
    assert "Your letter" in page
    for statement in BASELINE_STATEMENTS.values():
        assert escape(statement) in page


@pytest.mark.django_db
def test_the_letter_cannot_be_sent_without_the_letter_itself(participant):
    client = through_to_the_letter(participant)
    answer_the_baseline(client, prefix="pl")

    refused = complete(client, "letter")

    assert refused.status_code == 400
    assert "Write at least one part of your letter before sealing it." in refused.content.decode()


@pytest.mark.django_db
def test_the_letter_cannot_be_sent_without_all_four_after_ratings(participant):
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    for slot in ("bible", "gifts", "call"):
        answer(client, f"pl-{slot}", "8")

    refused = complete(client, "letter")

    assert refused.status_code == 400
    assert refused.content.decode().count(ANSWER_ALL_FOUR) == 1


@pytest.mark.django_db
def test_the_letter_is_sent_once_it_is_written_and_all_four_are_answered(participant):
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    answer_the_baseline(client, prefix="pl")

    assert complete(client, "letter").status_code == 303
    assert "letter" in Response.objects.get().completed_sections


# Progress, which belongs to the participant rather than the browser


@pytest.mark.django_db
def test_progress_survives_a_reload(participant):
    answer_the_baseline(participant)

    page = participant.get("/sections/onboarding/").content.decode()

    assert page.count('value="7" checked') == 4


@pytest.mark.django_db
def test_progress_follows_the_participant_to_a_second_device(participant, django_user_model):
    through_to_the_calling_statement(participant)
    answer(participant, "cl-statement", A_STATEMENT)

    second_device = Client()
    second_device.force_login(django_user_model.objects.get(username="participant"))

    assert A_STATEMENT in second_device.get("/sections/calling/").content.decode()
    assert "Complete" in second_device.get("/").content.decode()


# The demo check: the document is the app's content


@pytest.mark.django_db
def test_editing_a_prompt_in_the_document_changes_the_app_for_a_fresh_participant(client, load_pathway):  # noqa: F811
    load_pathway(the_pathway())
    first = a_fresh_participant(client, "first@example.com")
    answer_the_baseline(first)
    complete(first, "onboarding")
    assert "Read these passages before continuing" in first.get("/sections/calling/").content.decode()

    edited = the_pathway()
    calling = next(s for s in edited["content"]["sections"] if s["id"] == "calling")
    next(b for b in calling["blocks"] if b["id"] == "s2a-reading")["heading"] = "Sit with these before you write"
    load_pathway(edited)

    second = a_fresh_participant(client, "second@example.com")
    answer_the_baseline(second)
    complete(second, "onboarding")
    page = second.get("/sections/calling/").content.decode()
    assert "Sit with these before you write" in page
    assert "Read these passages before continuing" not in page


@pytest.mark.django_db
def test_a_participant_already_in_progress_stays_on_the_version_they_started(participant, load_pathway):  # noqa: F811
    """✨ Pinning is the behaviour, not a bug: the demo is checked on someone who has not begun."""
    answer(participant, "bl-bible", "6")

    edited = the_pathway()
    edited["content"]["sections"][0]["blocks"][0]["body"] = "Rewritten after they began."
    load_pathway(edited)

    assert "Rewritten after they began." not in participant.get("/sections/onboarding/").content.decode()
