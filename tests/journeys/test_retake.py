# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Retaking the strengths evaluation, on any system (29 Oct), in place of fix-19's demo-only retake: the results page
links to a page asking first, and only its button clears the sort, its result and its tie-break. The sections the
participant finished stay finished, and their view of the comparison stays, so nothing already opened locks again.
What the people they invited sent is deleted, with a warning first, and their links keep working, so they can answer
again. The coach sees the evaluation as not done until the participant chooses to show them the new results.

Loading a demo profile stays demo-only (tests/journeys/test_demo_retake.py). What each page says is a hand check; these
tests read what the engine says from where it is written."""

import re

import pytest
from django.test import Client
from django.utils.html import escape

from engine.document.blocks import COMPARISON_STATUSES, COMPARISON_UNSORTED
from engine.document.observers import minimum_observers
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
    section_2,
    serves_workbook_1,
    submit_the_sort,
    the_pathway,
    through_section_1,
)
from tests.journeys.pages import main_of, text_of
from tests.journeys.test_whatever_you_do_faithful_port import complete

SORT = "strengths-sort"
RESULTS = f"/results/{SORT}/"
RETAKE = f"{RESULTS}retake/"
SORT_PAGE = "/sections/strengths/"
VOICES_PAGE = "/sections/trusted-voices/"
CARD = "how-others-see-you"
UNSORTED = " ".join(COMPARISON_UNSORTED)
# ✨ The hub's row and the sidebar say it as a pill, which has no full stop.
UNSORTED_PILL = UNSORTED.removesuffix(".")
# ✨ The press on to the comparison greyed: a span that cannot be followed, in place of the form posting the visit.
GREYED = '<span class="pill is-waiting" role="link" aria-disabled="true">'
VISIT = f'action="{RESULTS}comparison/visit/"'
# ✨ The coach's page drawing the participant's results.
RESULTS_DRAWN = 'class="result-bar-row"'


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

    assert f'href="{RETAKE}"' in results
    assert "data-demo-reveal" not in results
    page = asked.content.decode()
    assert asked.status_code == 200
    # ✨ It asks: a form posting back here to delete, and a way back to the results that keeps them.
    assert f'action="{RETAKE}"' in page
    assert re.search(rf'<a [^>]*href="{RESULTS}"', page)
    assert 'name="profile"' not in page and 'name="answers"' not in page
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

    assert participant.post(RETAKE).status_code == 303

    response = Response.objects.get()
    assert not Result.objects.exists()
    assert {"onboarding", "designed", "others"} <= set(response.completed_sections)
    assert SORT in response.comparisons_viewed
    assert serves_workbook_1(participant)


@pytest.mark.django_db
def test_with_answers_in_the_retake_page_lists_them_among_what_it_deletes_saying_how_many(
    live, participant  # noqa: F811
):
    through_section_1(participant)
    before_answers = deleted_list(participant.get(RETAKE).content.decode())
    people_answer(participant)

    with_answers = deleted_list(participant.get(RETAKE).content.decode())

    added = [item for item in with_answers if item not in before_answers]
    assert len(added) == 1 and re.search(r"\b3\b", added[0])
    assert ObserverResponse.objects.count() == 3


def deleted_list(page):
    """✨ The items of the retake page's first list, what retaking deletes."""
    deletes = re.search(r'<ul class="retake-list">(.*?)</ul>', page, re.S).group(1)
    return re.findall(r"<li>(.*?)</li>", deletes, re.S)


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
    assert RESULTS_DRAWN in coach.get(link).content.decode()

    participant.post(RETAKE)

    assert RESULTS_DRAWN not in coach.get(link).content.decode()
    assert Invitation.objects.get(contact__role=Contact.Role.COACH).results_shared_at is None


# ✨ How others see you, between the retake and the new sort (29 Oct): Section 2 and the hub keep its card and row,
# the press greyed, saying the sort comes first, where before they showed nothing at all.


@pytest.mark.django_db
def test_after_retaking_section_2_keeps_how_others_see_you_greyed_saying_to_finish_the_sort_first(
    live, participant  # noqa: F811
):
    compared(participant)

    participant.post(RETAKE)

    card = card_of(section_2(participant))
    assert f'href="{VOICES_PAGE}"' in card
    assert GREYED in card and VISIT not in card
    assert UNSORTED in text_of(card)
    assert re.search(rf'<a href="{SORT_PAGE}"[^>]*>', card)
    assert "is-complete" not in card


def card_of(page):
    """✨ Section 2's How others see you card."""
    found = re.search(rf'<div id="block-{CARD}" class="signpost comparison-signpost[^"]*">.*?</p>\s*</div>', page, re.S)
    assert found, "Section 2 has no How others see you card"
    return found.group(0)


@pytest.mark.django_db
def test_after_retaking_the_hub_keeps_the_how_others_see_you_row_saying_to_finish_the_sort_first(
    live, participant  # noqa: F811
):
    compared(participant)

    participant.post(RETAKE)

    page = main_of(participant.get("/hub/").content.decode())
    row = re.search(r'<li class="hub-section srow hub-part hub-comparison.*?</li>', page, re.S)
    assert row, "the hub has no How others see you row"
    assert f'<span class="tag status-waiting">{escape(UNSORTED_PILL)}</span>' in row.group(0)
    assert f'href="{SORT_PAGE}"' in row.group(0)
    assert UNSORTED_PILL != UNSORTED, "the pill keeps the sentence's full stop"


@pytest.mark.django_db
def test_once_the_new_sort_is_in_how_others_see_you_counts_the_answers_again(live, participant):  # noqa: F811
    compared(participant)
    participant.post(RETAKE)

    submit_the_sort(participant)

    card = card_of(section_2(participant))
    assert UNSORTED not in text_of(card)
    assert f'href="{SORT_PAGE}"' not in card
    assert GREYED in card  # ✨ the answers went with the retake, so too few are in again
    # ✨ Its three links still out, so none more to invite: it counts the answers, from none.
    counted = COMPARISON_STATUSES["waiting"].format(answered=0, minimum=minimum_observers(the_pathway()))
    assert counted in text_of(card)
