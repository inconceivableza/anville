# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A section whose work is all in its parts and that ends in its signpost to a part ending in a sort, as *Whatever You
Do*'s Section 1 ends in the strengths evaluation, completes itself as the evaluation ends: the sort in and every
tie-break pair answered or skipped (ticket 119, the developer's call of 17 Nov). Its finish's label is then a link on to
the hub, no longer a press. A section with work of its own keeps its press (`test_finishing_from_the_results.py`, and
the faithful port's in `test_whatever_you_do_faithful_port.py`)."""

import pytest
from django.utils.html import escape

from engine.hub import section_by_id
from engine.models import Response
from tests.journeys.pages import main_of
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_consent import give_consent
from tests.journeys.test_results import submit_sort
from tests.journeys.test_tie_break import CLEAR, TIE_BREAK, TIED_ON_ONE, choose, tie_breaking_pathway

GIFTS = "gifts"
LABEL = "I've finished your gifts"
RESULTS = "/results/strengths-sort/"
FINISH = f'action="/sections/{GIFTS}/complete/'
WAY_ON = f'href="/hub/">{escape(LABEL)}</a>'
# ✨ What the section's signpost to its Strengths assessment says before the evaluation ends, and once it has.
OPEN_IT = "Open the strengths assessment →"
FINISHED = "You've finished the strengths assessment."


def ended_by_its_evaluation():
    """✨ The tie-break's test pathway with its Strengths assessment a part of a section that only signposts it."""
    document = tie_breaking_pathway()
    sections = document["content"]["sections"]
    strengths = section_by_id(document, "strengths")
    strengths["part_of"] = GIFTS
    gifts = {
        "id": GIFTS,
        "title": "Your gifts",
        "requires": ["onboarding"],
        "complete_label": LABEL,
        "blocks": [
            {
                "id": "to-strengths",
                "type": "section_signpost",
                "section": "strengths",
                "button_label": OPEN_IT,
                "finished": {"body": FINISHED, "button_label": "View my results →"},
            }
        ],
        "gate": {"clauses": [{"type": "has_answer", "block": "strengths-sort", "message": "Finish the sort first."}]},
    }
    sections.insert(sections.index(strengths), gifts)
    return document


@pytest.fixture
def signed_in(client, participant, load_pathway):  # noqa: F811
    load_pathway(ended_by_its_evaluation())
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


def completed():
    return set(Response.objects.get().completed_sections)


@pytest.mark.django_db
def test_a_sort_with_no_pairs_completes_the_section_it_ends_as_it_is_sent(signed_in):
    assert submit_sort(signed_in, CLEAR)["HX-Redirect"] == RESULTS

    assert GIFTS in completed()


@pytest.mark.django_db
def test_a_sort_with_pairs_completes_it_only_once_the_last_pair_is_answered_or_skipped(signed_in):
    submit_sort(signed_in, TIED_ON_ONE)
    signed_in.get("/hub/")
    assert GIFTS not in completed()

    choose(signed_in, 0, "apostle")
    signed_in.get(TIE_BREAK)
    assert GIFTS not in completed()

    choose(signed_in, 1, "")  # ✨ skipped, which ends the evaluation as an answer does

    assert GIFTS in completed()


@pytest.mark.django_db
def test_its_results_and_its_own_page_offer_its_finish_as_a_way_on_to_the_hub_not_a_press(signed_in):
    submit_sort(signed_in, CLEAR)

    for address in (RESULTS, f"/sections/{GIFTS}/"):
        page = main_of(signed_in.get(address).content.decode())
        assert WAY_ON in page
        assert FINISH not in page
        assert "Mark as not complete" not in page


@pytest.mark.django_db
def test_before_the_evaluation_ends_its_own_page_offers_no_finish_to_press(signed_in):
    """✨ Pressing it would complete the section before the pairs, which the evaluation's end does instead."""
    submit_sort(signed_in, TIED_ON_ONE)

    page = main_of(signed_in.get(f"/sections/{GIFTS}/").content.decode())

    assert FINISH not in page and WAY_ON not in page


@pytest.mark.django_db
def test_its_signpost_says_the_evaluation_is_finished_only_once_the_last_pair_is_answered_or_skipped(signed_in):
    """✨ Until then it keeps its own wording, and its button leads through the sort's section and its results on to the
    next pair (hand check of 18 Nov), where it had said it was finished as soon as the sort was sent."""
    submit_sort(signed_in, TIED_ON_ONE)

    page = main_of(signed_in.get(f"/sections/{GIFTS}/").content.decode())
    assert escape(OPEN_IT) in page and escape(FINISHED) not in page
    assert 'href="/sections/strengths/"' in page
    assert signed_in.get("/sections/strengths/", follow=True).redirect_chain[-1][0] == TIE_BREAK

    choose(signed_in, 0, "apostle")
    choose(signed_in, 1, "")

    page = main_of(signed_in.get(f"/sections/{GIFTS}/").content.decode())
    assert escape(FINISHED) in page and escape(OPEN_IT) not in page
    assert f'href="{RESULTS}"' in page


@pytest.mark.django_db
def test_its_completion_is_never_taken_back_and_a_retake_keeps_it(signed_in):
    """✨ Taking it back would only see it complete again at once; a retake keeps finished sections finished (ADR
    0025)."""
    submit_sort(signed_in, CLEAR)

    assert signed_in.post(f"/sections/{GIFTS}/reopen/").status_code == 404
    assert signed_in.post(f"{RESULTS}retake/").status_code == 303

    signed_in.get("/hub/")
    assert GIFTS in completed()


@pytest.mark.django_db
def test_an_evaluation_ended_before_this_completes_its_section_the_next_time_the_participant_is_seen(signed_in):
    """✨ A participant whose evaluation ended before ticket 119, their section left for the press, is caught up on any
    page, as a hub side card is."""
    submit_sort(signed_in, CLEAR)
    response = Response.objects.get()
    response.completed_sections = {key: when for key, when in response.completed_sections.items() if key != GIFTS}
    response.save(update_fields=["completed_sections"])

    signed_in.get("/hub/")

    assert GIFTS in completed()


@pytest.mark.django_db
def test_the_press_still_completes_it_from_a_page_left_open(signed_in):
    """✨ A page drawn before ticket 119 still carries the form, and the demo shortcut completes sections as a press
    does."""
    submit_sort(signed_in, TIED_ON_ONE)

    pressed = signed_in.post(f"/sections/{GIFTS}/complete/")

    assert (pressed.status_code, pressed.url) == (303, "/hub/")
    assert GIFTS in completed()
