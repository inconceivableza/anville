"""✨ A sort is scored once, when it is submitted, and the result is kept against the response's pathway version.

The results page shows that stored result with the pathway version's own wording.
"""

import json
import re

import pytest

from engine.document.scoring import score
from engine.models import Response, Result
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import answer, participant  # noqa: F401 (a fixture)
from tests.journeys.test_consent import give_consent
from tests.journeys.test_hub import a_fresh_participant

SORT, STRENGTHS = "strengths-sort", "strengths"


@pytest.fixture
def signed_in(client, participant, load_pathway):
    """✨ A participant with onboarding complete, so the Strengths assessment section is open."""
    load_pathway(sort_pathway())
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


def submit_sort(client, sort):
    return answer(client, SORT, json.dumps(sort), section=STRENGTHS)


def results(client, block_id=SORT):
    return client.get(f"/results/{block_id}/")


def in_order(page, *texts):
    """✨ Whether every text appears on the page, each after the one before it."""
    position = 0
    for text in texts:
        position = page.find(text, position)
        if position < 0:
            return False
        position += len(text)
    return True


@pytest.mark.django_db
def test_submitting_a_sort_stores_its_result_against_the_responses_pathway_version(signed_in, participant):
    submit_sort(signed_in, complete_sort())

    response = Response.objects.get(participant=participant)
    result = Result.objects.get(response=response, block_id=SORT)
    assert response.answers[SORT] == complete_sort()
    assert result.scores == score(sort_pathway(), complete_sort())


@pytest.mark.django_db
def test_a_sort_that_breaks_the_contract_stores_neither_an_answer_nor_a_result(signed_in, participant):
    incomplete = complete_sort()
    del incomplete["p1"]

    refused = submit_sort(signed_in, incomplete)

    assert refused.status_code == 400
    assert not Result.objects.exists()
    assert SORT not in getattr(Response.objects.filter(participant=participant).first(), "answers", {})


@pytest.mark.django_db
def test_a_second_sort_is_refused_and_the_first_result_stands(signed_in, participant):
    """✨ Retake is not offered in this milestone. When it is, it makes a new attempt and keeps this one."""
    submit_sort(signed_in, complete_sort())

    again = submit_sort(signed_in, complete_sort(a5={"bucket": "not-me", "value": 0}))

    assert again.status_code == 409
    assert "not offered" in again.content.decode()
    assert Response.objects.get(participant=participant).answers[SORT] == complete_sort()
    assert [result.scores for result in Result.objects.all()] == [score(sort_pathway(), complete_sort())]


@pytest.mark.django_db
def test_a_later_pathway_version_never_recomputes_a_stored_result(signed_in, participant, load_pathway):
    submit_sort(signed_in, complete_sort())
    rescored = sort_pathway()
    rescored["instrument"]["items"][0]["loads"] = ["prophet", "deliver"]

    load_pathway(rescored)
    signed_in.get(f"/sections/{STRENGTHS}/")

    assert [result.scores for result in Result.objects.all()] == [score(sort_pathway(), complete_sort())]


@pytest.mark.django_db
def test_before_a_sort_is_submitted_the_results_page_sends_the_participant_to_the_sort(signed_in):
    page = results(signed_in)

    assert page.status_code == 302
    assert page.url == f"/sections/{STRENGTHS}/"


@pytest.mark.django_db
def test_the_results_page_greets_the_participant_and_ranks_both_profiles(signed_in):
    submit_sort(signed_in, complete_sort())

    page = results(signed_in).content.decode()

    assert "participant, here’s your profile" in page
    assert in_order(page, "Your gifting", "Apostle", "90%", "Prophet", "10%")
    assert in_order(page, "Your energy", "Deliver", "90%", "Ponder", "10%")


@pytest.mark.django_db
def test_each_profile_carries_its_subtitle_descriptions_and_personas(signed_in):
    submit_sort(signed_in, complete_sort())

    page = results(signed_in).content.decode()

    assert in_order(page, "Fivefold and more", "Pioneers new things.", "Challenges the status quo.")
    assert in_order(page, "What energises you", "The Doer", "Finishes the work.", "The Philosopher", "Thinks deeply.")


@pytest.mark.django_db
def test_the_item_scores_are_listed_in_an_expandable_list_with_the_participants_values(signed_in):
    submit_sort(signed_in, complete_sort())

    page = results(signed_in).content.decode()

    listed = re.search(r"<details.*?</details>", page, re.S).group(0)
    assert in_order(listed, "Apostle", "Building something that will outlast you", "90")
    assert in_order(listed, "Prophet", "Going against the grain", "10")


@pytest.mark.django_db
def test_the_validity_disclaimer_is_shown_with_the_results(signed_in):
    submit_sort(signed_in, complete_sort())

    assert "These results are indicative, not definitive." in results(signed_in).content.decode()


@pytest.mark.django_db
def test_apest_bars_take_their_constructs_tone_and_tied_pep_bars_share_a_rank_colour(signed_in):
    submit_sort(signed_in, complete_sort(a5={"bucket": "strength", "value": 50}, p1={"bucket": "not-me", "value": 50}))

    page = results(signed_in).content.decode()

    assert 'class="bar-fill tone-violet"' in page
    assert 'class="bar-fill tone-rose"' in page
    assert page.count('class="bar-fill rank-1"') == 2
    assert "rank-2" not in page


@pytest.mark.django_db
def test_once_the_sort_is_in_its_section_links_to_the_results(signed_in):
    submit_sort(signed_in, complete_sort())

    assert f'href="/results/{SORT}/"' in signed_in.get(f"/sections/{STRENGTHS}/").content.decode()


@pytest.mark.django_db
def test_the_results_page_leads_back_to_the_sorts_section_where_it_is_completed(signed_in):
    """✨ The prototype returned to Section 1, but its assessment had nothing of its own to complete."""
    submit_sort(signed_in, complete_sort())

    page = results(signed_in).content.decode()

    assert f'<a href="/sections/{STRENGTHS}/">← Back to Strengths assessment</a>' in page
    assert "← Back to the hub" not in page


def widget_data(page, block_id=SORT):
    """✨ What the section page hands the sort widget, read the way the widget reads it."""
    data = re.search(rf'<script id="sort-{block_id}" type="application/json">(.*?)</script>', page, re.S)
    return json.loads(data.group(1)) if data else None


@pytest.mark.django_db
def test_the_sort_widget_is_given_every_item_in_the_participants_wording_and_the_buckets_weakest_first(signed_in):
    page = signed_in.get(f"/sections/{STRENGTHS}/").content.decode()

    assert widget_data(page) == {
        "items": [
            {"id": "a5", "text": "Building something that will outlast you"},
            {"id": "p1", "text": "Going against the grain"},
        ],
        "buckets": [
            {"id": "not-me", "label": "Not me", "seed": 10},
            {"id": "strength", "label": "Real strength", "seed": 85},
        ],
    }


@pytest.mark.django_db
def test_once_the_sort_is_in_the_widget_is_not_offered_again(signed_in):
    submit_sort(signed_in, complete_sort())

    assert widget_data(signed_in.get(f"/sections/{STRENGTHS}/").content.decode()) is None


@pytest.mark.django_db
def test_a_submitted_sort_takes_the_participant_to_their_results(signed_in):
    """✨ Without htmx. Completing onboarding gave the participant a response, so no version need be sent."""
    submitted = signed_in.post(f"/answers/{SORT}/", {"value": json.dumps(complete_sort())})

    assert submitted.status_code == 303
    assert submitted.url == f"/results/{SORT}/"


@pytest.mark.django_db
def test_a_sort_submitted_through_htmx_sends_the_browser_to_the_results(signed_in):
    submitted = submit_sort(signed_in, complete_sort())

    assert submitted.status_code == 200
    assert submitted.headers["HX-Redirect"] == f"/results/{SORT}/"


def sort_form(page):
    """✨ The form the sort widget fills in and submits, or nothing if the page has none."""
    form = re.search(rf'<form id="block-{SORT}".*?</form>', page, re.S)
    return form.group(0) if form else ""


@pytest.mark.django_db
def test_the_sort_is_sent_by_a_form_that_saves_the_whole_sort_against_the_pages_version(signed_in, participant):
    """✨ The widget itself is checked by hand; what it relies on is here. It fills in `value`, the form sends it."""
    form = sort_form(signed_in.get(f"/sections/{STRENGTHS}/").content.decode())

    assert f'action="/answers/{SORT}/"' in form
    assert '<input type="hidden" name="value">' in form
    assert f'name="version" value="{Response.objects.get(participant=participant).version_id}"' in form


@pytest.mark.django_db
def test_without_javascript_the_sort_says_it_needs_it(signed_in):
    shown = re.search(r"<noscript>(.*?)</noscript>", signed_in.get(f"/sections/{STRENGTHS}/").content.decode(), re.S)

    assert shown is not None
    assert "The sort needs JavaScript." in shown.group(1)


@pytest.mark.django_db
def test_while_the_sort_is_not_in_its_section_offers_no_way_to_complete_it(signed_in):
    """✨ As in the prototype, the sort leads only to the results, so no Mark complete sits beside it to skip both."""
    page = signed_in.get(f"/sections/{STRENGTHS}/").content.decode()

    assert f"/sections/{STRENGTHS}/complete/" not in page


@pytest.mark.django_db
def test_the_sorts_section_is_refused_completion_before_the_sort_is_in(signed_in):
    assert signed_in.post(f"/sections/{STRENGTHS}/complete/").status_code == 400


@pytest.mark.django_db
def test_once_the_sort_is_in_its_section_can_be_completed(signed_in):
    submit_sort(signed_in, complete_sort())

    assert f'action="/sections/{STRENGTHS}/complete/"' in signed_in.get(f"/sections/{STRENGTHS}/").content.decode()
    assert signed_in.post(f"/sections/{STRENGTHS}/complete/").status_code == 303


@pytest.mark.django_db
def test_a_participant_never_sees_another_participants_results(signed_in):
    submit_sort(signed_in, complete_sort())

    someone_else = a_fresh_participant(signed_in, "someone@example.com")
    someone_else.post("/sections/onboarding/complete/")

    assert results(someone_else).status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("block_id", ["statement", "no-such-block"])
def test_only_a_scored_block_has_a_results_page(signed_in, block_id):
    assert results(signed_in, block_id).status_code == 404
