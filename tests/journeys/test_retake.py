# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Retaking the strengths evaluation, on any system (29 Oct), in place of fix-19's demo-only retake: the results page
links to a page asking first, and only its button clears the sort, its result and its tie-break. The sections the
participant finished stay finished, and their view of the comparison stays, so nothing already opened locks again.
What the people they invited sent is deleted, with a warning first, and their links keep working, so they can answer
again. The coach sees the evaluation as not done until the participant chooses to show them the new results.

Loading a demo profile stays demo-only (tests/journeys/test_demo_retake.py)."""

import pytest
from django.test import Client
from django.utils.html import escape

from engine.models import Contact, Invitation, ObserverResponse, Response, Result
from tests.journeys.test_coach_checklist import choose
from tests.journeys.test_coach_link import answer_as_coach
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_observer_assessment import send
from tests.journeys.test_whatever_you_do import (
    a_whole_sort,
    participant,  # noqa: F401  (a fixture, used by name)
    people_answer,
    press_compare,
    reissue_coach_link,
    serves_workbook_1,
    through_section_1,
)
from tests.journeys.test_whatever_you_do_faithful_port import complete

SORT = "strengths-sort"
RESULTS = f"/results/{SORT}/"
RETAKE = f"{RESULTS}retake/"
SORT_PAGE = "/sections/strengths/"
NOT_DONE = "finishes the strengths evaluation and sends it to you"


@pytest.fixture
def live(settings):
    """✨ A production system: neither DEBUG nor a demo notice, whatever the developer's `.env` sets."""
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = ""


def compared(client):
    """✨ Section 1 finished, three people's answers in and the comparison viewed, which freezes collection, then
    Section 2 finished; returns each person's browser."""
    through_section_1(client)
    browsers = people_answer(client)
    assert press_compare(client).status_code == 303
    assert complete(client, "others").status_code == 303
    return browsers


@pytest.mark.django_db
def test_off_a_demo_system_the_results_page_links_to_the_retake_which_asks_first_and_offers_no_demo_profile(
    live, participant  # noqa: F811
):
    client = through_section_1(participant)

    results = client.get(RESULTS).content.decode()
    asked = client.get(RETAKE)

    assert f'<a href="{RETAKE}">Retake the strengths evaluation</a>' in results
    assert "data-demo-reveal" not in results
    page = asked.content.decode()
    assert asked.status_code == 200
    assert f'action="{RETAKE}"' in page
    assert "Retaking deletes your results. They can’t be brought back." in page
    # ✨ Keeping them is the default: the green button, first; deleting them the plain one below.
    keep = page.index(f'<a class="pill full" href="{RESULTS}">Keep my results</a>')
    assert keep < page.index('<button type="submit" class="pill ghost full">Delete and retake</button>')
    assert "Demo only" not in page
    assert 'name="profile"' not in page
    assert Result.objects.exists()  # ✨ opening the page clears nothing


@pytest.mark.django_db
def test_retaking_clears_the_sort_and_its_result_and_opens_the_sort_again(live, participant):  # noqa: F811
    client = through_section_1(participant)

    retaken = client.post(RETAKE)

    assert (retaken.status_code, retaken["Location"]) == (303, SORT_PAGE)
    assert not Result.objects.exists()
    assert SORT not in Response.objects.get().answers
    assert f'data-sort="sort-{SORT}"' in client.get(SORT_PAGE).content.decode()


@pytest.mark.django_db
def test_retaking_keeps_every_finished_section_finished_and_the_comparison_viewed(live, participant):  # noqa: F811
    """✨ So Section 2's first workbook, which waits on the comparison, never locks again."""
    compared(participant)
    asked = participant.get(RETAKE).content.decode()

    assert participant.post(RETAKE).status_code == 303

    response = Response.objects.get()
    assert not Result.objects.exists()
    assert "no longer be marked complete" not in asked
    assert {"onboarding", "designed", "others"} <= set(response.completed_sections)
    assert SORT in response.comparisons_viewed
    assert serves_workbook_1(participant)


@pytest.mark.django_db
def test_with_answers_in_the_retake_page_warns_they_will_be_deleted_and_that_the_links_keep_working(
    live, participant  # noqa: F811
):
    compared(participant)

    page = participant.get(RETAKE).content.decode()

    warning = "What the people you invited sent (3 answers). Their links still work, so they can answer again."
    assert f"<li>{warning}</li>" in page
    assert ObserverResponse.objects.count() == 3


@pytest.mark.django_db
def test_retaking_deletes_what_people_sent_and_opens_collection_so_their_own_links_take_answers_again(
    live, participant  # noqa: F811
):
    browsers = compared(participant)

    participant.post(RETAKE)

    response = Response.objects.get()
    assert not ObserverResponse.objects.exists()
    assert response.collection_frozen_at is None
    assert response.observers_withdrew == 0  # ✨ nobody withdrew: the participant cleared them
    assert not Contact.objects.filter(role=Contact.Role.CONTACT, sent_at__isnull=False).exists()
    assert send(browsers[0], a_whole_sort()).status_code == 303
    assert ObserverResponse.objects.count() == 1


@pytest.mark.django_db
def test_after_retaking_the_coach_sees_the_evaluation_as_not_done_until_the_new_results_are_shown_again(
    live, participant  # noqa: F811
):
    compared(participant)
    choose(participant)
    link, coach = reissue_coach_link(participant), Client()
    assert answer_as_coach(coach, link, "accept").status_code == 303
    participant.post(f"{RESULTS}comparison/coach/", {"share": "on"})
    assert escape(NOT_DONE) not in coach.get(link).content.decode()

    participant.post(RETAKE)

    assert escape(NOT_DONE) in coach.get(link).content.decode()
    assert Invitation.objects.get(contact__role=Contact.Role.COACH).results_shared_at is None
