"""✨ Answers an author marks as fixed once their section is complete, such as a baseline measured again later.

In the original prototype the baseline screen cannot be returned to after "Continue", so the first ratings
stand. Here a participant can reopen a section, so the engine keeps them standing instead: a fixed answer
can be changed freely until the section is first completed, and never afterwards, whatever else is reopened.
"""

import re

import pytest

from engine.models import Publication, Response
from tests.documents import pathway_document
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

ONBOARDING = "onboarding"
FIXED_REFUSAL = "This answer was fixed when you completed this section."


def fixed_baseline_pathway():
    """✨ The test pathway with its baseline rating fixed once onboarding is complete, beside an answer that is not."""
    document = pathway_document()
    onboarding = document["content"]["sections"][0]
    onboarding["blocks"][1]["fixed_once_complete"] = True
    onboarding["blocks"].append({"id": "coach-name", "type": "long_text", "prompt": "Who is your coach?"})
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(fixed_baseline_pathway())
    return signed_in_client


def answer(client, block_id, value):
    return client.post(f"/answers/{block_id}/", {"value": value, "version": Publication.current_version().pk})


def complete(client, section_id=ONBOARDING):
    return client.post(f"/sections/{section_id}/complete/")


def reopen(client, section_id=ONBOARDING):
    return client.post(f"/sections/{section_id}/reopen/")


def stored(block_id):
    return Response.objects.get().answers.get(block_id)


def shown(client, section_id=ONBOARDING):
    return client.get(f"/sections/{section_id}/").content.decode()


@pytest.mark.django_db
def test_a_fixed_answer_can_still_be_changed_before_its_section_is_complete(participant):
    """✨ As in the prototype, where a rating can be changed freely until "Continue"."""
    answer(participant, "baseline-bible", "4")

    assert answer(participant, "baseline-bible", "6").status_code == 303
    assert stored("baseline-bible") == 6


@pytest.mark.django_db
def test_completing_the_section_fixes_the_answer(participant):
    answer(participant, "baseline-bible", "4")
    complete(participant)

    refused = answer(participant, "baseline-bible", "9")

    assert refused.status_code == 409
    assert FIXED_REFUSAL in refused.content.decode()
    assert stored("baseline-bible") == 4


@pytest.mark.django_db
def test_a_save_checked_just_before_the_section_was_completed_still_cannot_change_the_fixed_answer(participant):
    """✨ An autosave that read the response before a completion landed must not write over the answer it fixed."""
    answer(participant, "baseline-bible", "4")
    read_before_completing = Response.objects.get()
    complete(participant)

    read_before_completing.save_answer("baseline-bible", 9)

    assert stored("baseline-bible") == 4


@pytest.mark.django_db
def test_completing_again_after_reopening_keeps_the_time_the_answer_was_first_fixed(participant):
    answer(participant, "baseline-bible", "4")
    complete(participant)
    first_fixed = Response.objects.get().fixed_answers["baseline-bible"]
    reopen(participant)

    complete(participant)

    assert Response.objects.get().fixed_answers["baseline-bible"] == first_fixed


@pytest.mark.django_db
def test_a_marked_answer_left_blank_is_fixed_the_next_time_its_section_is_completed(participant):
    complete(participant)
    assert answer(participant, "baseline-bible", "5").status_code == 303

    complete(participant)

    assert answer(participant, "baseline-bible", "8").status_code == 409
    assert stored("baseline-bible") == 5


@pytest.mark.django_db
def test_reopening_the_section_leaves_the_answer_fixed(participant):
    answer(participant, "baseline-bible", "4")
    complete(participant)
    reopen(participant)

    assert answer(participant, "baseline-bible", "9").status_code == 409
    assert stored("baseline-bible") == 4


@pytest.mark.django_db
def test_the_sections_other_answers_can_still_be_changed_after_it_is_reopened(participant):
    """✨ Onboarding will also hold the coach's details, and a participant must be able to correct those."""
    answer(participant, "baseline-bible", "4")
    answer(participant, "coach-name", "Sam")
    complete(participant)
    reopen(participant)

    assert answer(participant, "coach-name", "Sam Jones").status_code == 303
    assert stored("coach-name") == "Sam Jones"


@pytest.mark.django_db
def test_an_answer_the_author_did_not_mark_fixed_stays_changeable_after_completion(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())
    answer(signed_in_client, "baseline-bible", "4")
    complete(signed_in_client)

    assert answer(signed_in_client, "baseline-bible", "9").status_code == 303
    assert stored("baseline-bible") == 9


@pytest.mark.django_db
def test_a_fixed_rating_is_shown_as_chosen_but_cannot_be_changed_on_the_page(participant):
    answer(participant, "baseline-bible", "4")
    complete(participant)

    points = re.findall(r'<input[^>]*id="answer-baseline-bible-\d+"[^>]*>', shown(participant))

    assert len(points) == 10
    assert all(" disabled" in point for point in points)
    assert sum(" checked" in point for point in points) == 1
    assert 'value="4" checked' in next(point for point in points if " checked" in point)


@pytest.mark.django_db
def test_a_completed_section_with_a_fixed_answer_does_not_claim_every_answer_can_still_change(participant):
    answer(participant, "baseline-bible", "4")
    complete(participant)

    page = shown(participant)
    assert "You can still change your answers here." not in page
    assert "Ratings fixed when you completed this section can no longer be changed." in page
