# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Retaking the self-assessment, a demo-only tool (fix-19): on a development or demo system, a participant can
clear their own sort and everything worked out from it, and sort the cards again from the start. Nothing else of
theirs is touched, and nothing of anyone else's."""

import json
import re
from datetime import timedelta

import pytest
from django.test import Client
from django.utils.html import escape

from engine.models import Contact, Invitation, ObserverResponse, Response, Result
from engine.scenario_loading import prefill
from engine.tie_break_scenarios import seeding, summary
from tests.journeys.pages import version_on
from tests.journeys.test_answers import answer, participant  # noqa: F401 (participant is a fixture)
from tests.journeys.test_comparison import THREE_OBSERVERS, press_compare
from tests.journeys.test_consent import give_consent
from tests.journeys.test_observer_responses import an_observer
from tests.journeys.test_results import SORT, STRENGTHS, results, submit_sort
from tests.journeys.test_tie_break import CLEAR, TIED_ON_ONE, choose, tie_breaking_pathway
from tests.journeys.test_whatever_you_do import answer_onboarding as wyd_onboarding
from tests.journeys.test_whatever_you_do import the_pathway as wyd_pathway
from tests.journeys.test_whatever_you_do_faithful_port import answer as answer_published
from tests.journeys.test_whatever_you_do_faithful_port import answer_onboarding as faithful_onboarding
from tests.journeys.test_whatever_you_do_faithful_port import the_pathway as faithful_port

RETAKE = f"/results/{SORT}/retake/"


def retake_pathway():
    """✨ The tie-break's test pathway with the Strengths assessment a part of the calling section, whose gate needs the
    sort as well as the statement, as Section 1's does in Whatever You Do."""
    document = tie_breaking_pathway()
    sections = {section["id"]: section for section in document["content"]["sections"]}
    sections[STRENGTHS]["part_of"] = "calling"
    sections["calling"]["gate"]["clauses"].append({"type": "has_answer", "block": SORT, "message": "Finish the sort."})
    return document


@pytest.fixture
def demo(settings):
    """✨ A demo system, whatever the developer's `.env` sets."""
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = "This is a demo."


@pytest.fixture
def sorted_in(demo, client, participant, load_pathway):  # noqa: F811
    """✨ A participant who has sent a sort tied on one framework, answered both its pairs, and seen their results."""
    load_pathway(retake_pathway())
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    submit_sort(client, TIED_ON_ONE)
    choose(client, 0, "prophet")
    choose(client, 1, "apostle")
    results(client)
    return client


@pytest.mark.django_db
def test_with_debug_off_and_no_demo_notice_there_is_no_retake_and_no_link_to_it(sorted_in, settings):
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = ""

    assert sorted_in.get(RETAKE).status_code == 404
    assert sorted_in.post(RETAKE).status_code == 404
    assert RETAKE not in results(sorted_in).content.decode()
    assert Result.objects.exists()


@pytest.mark.django_db
def test_on_a_demo_system_the_link_is_hidden_until_revealed(sorted_in):
    """✨ fix-20: the link is in the page but `hidden` (not seen, not in the tab order, not read out) until the
    participant holds Option/Alt or presses and holds the title; those reveals are hand checks."""
    page = results(sorted_in).content.decode()

    assert f'<p class="back-to-hub" data-demo-reveal hidden><a href="{RETAKE}">' in page
    assert "<h1 data-demo-reveal-hold>" in page


@pytest.mark.django_db
def test_off_a_demo_system_neither_the_hidden_link_nor_its_reveal_is_in_the_page(sorted_in, settings):
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = ""

    page = results(sorted_in).content.decode()

    assert "data-demo-reveal" not in page  # ✨ nor data-demo-reveal-hold, which starts the same


@pytest.mark.django_db
def test_retaking_clears_the_sort_its_result_and_its_tie_break_and_the_assessment_shows_the_sort_again(sorted_in):
    answer(sorted_in, "statement", "To build things that last.")
    sorted_in.post("/sections/calling/complete/")
    press_compare(sorted_in)
    assert Result.objects.get().reweighted is not None
    assert RETAKE in results(sorted_in).content.decode()
    asked = sorted_in.get(RETAKE)
    assert f'action="{RETAKE}"' in asked.content.decode()
    assert Result.objects.exists()  # ✨ opening the page clears nothing

    retaken = sorted_in.post(RETAKE)

    response = Response.objects.get()
    assert retaken.status_code == 303
    assert not Result.objects.exists()
    assert SORT not in response.answers
    assert SORT not in response.comparisons_visited
    assert "calling" not in response.completed_sections
    shown = sorted_in.get(f"/sections/{STRENGTHS}/")
    assert shown.status_code == 200
    assert f'data-sort="sort-{SORT}"' in shown.content.decode()
    assert submit_sort(sorted_in, CLEAR)["HX-Redirect"] == f"/results/{SORT}/"


@pytest.mark.django_db
def test_retaking_leaves_observers_assessments_the_coach_link_and_other_answers_alone(sorted_in):
    answer(sorted_in, "statement", "To build things that last.")
    response = Response.objects.get()
    for sort in THREE_OBSERVERS:
        an_observer(response, sort)
    [coach] = response.replace_contacts("coach", [{"name": "Sam", "email": "sam@example.com"}], Contact.Role.COACH)
    Invitation.issue(coach, timedelta(days=30))
    press_compare(sorted_in, confirmed=True)
    assert Response.objects.get().collection_frozen_at is not None

    sorted_in.post(RETAKE)

    response = Response.objects.get()
    assert response.answers["statement"] == "To build things that last."
    assert "onboarding" in response.completed_sections
    assert sorted(ObserverResponse.objects.values_list("assessment", flat=True), key=str) == sorted(
        THREE_OBSERVERS, key=str
    )
    assert Invitation.objects.filter(contact__role=Contact.Role.COACH).exists()
    assert response.collection_frozen_at is None


@pytest.mark.django_db
def test_without_javascript_a_refused_choice_comes_back_on_the_retake_page_with_nothing_cleared(sorted_in):
    """✨ Never the bare status line (spec, Engine; fix-2)."""
    refused = sorted_in.post(RETAKE, {"profile": "no-such-profile"})

    page = refused.content.decode()
    assert refused.status_code == 400
    assert Result.objects.get().tie_break_answers
    assert SORT in Response.objects.get().answers
    assert refused.templates[0].name == "engine/retake.html"
    assert '<body class="framed">' in page
    assert "Not saved." in page


@pytest.mark.django_db
def test_a_participant_can_clear_only_their_own_assessment(sorted_in, django_user_model):
    someone_else = django_user_model.objects.create_user(username="someone", email="someone@example.com")
    other = Client()
    other.force_login(someone_else)
    give_consent(other)

    other.post(RETAKE)
    Client().post(RETAKE)

    assert Result.objects.get().tie_break_answers
    assert SORT in Response.objects.get(participant__username="participant").answers


# ✨ Demo profiles (fix-21): one of `seed_tie_break`'s starting profiles, with a way of answering its pairs (fix-25),
# loaded into the participant's own sort, from the retake page or, before any sort, from the sort page. The profiles
# are made for Whatever You Do.
WYD_SORT = "strengths-sort"
WYD_SORT_PAGE = "/sections/strengths/"
WYD_RETAKE = f"/results/{WYD_SORT}/retake/"


def on_the_sort(client, django_user_model, load_pathway, document, onboard):
    """✨ A participant of `document` signed in, consent given, onboarding done and Section 1's reading confirmed, so its
    sort is open to them."""
    load_pathway(document)
    client.force_login(django_user_model.objects.create_user(username="demo", email="demo@example.com"))
    give_consent(client)
    onboard(client)
    client.post("/sections/onboarding/complete/")
    answer_published(client, "gifts-reading", "true")
    return client


@pytest.fixture
def on_whatever_you_do(demo, client, django_user_model, load_pathway):
    return on_the_sort(client, django_user_model, load_pathway, wyd_pathway(), wyd_onboarding)


def load_profile(client, profile, answers=None):
    """✨ The choice's button pressed with `profile` and `answers` chosen, then on to the sort it leads to (fix-23)."""
    loaded = client.post(WYD_RETAKE, {"profile": profile, "answers": answers or ""})
    assert loaded.status_code == 303
    assert loaded["Location"].startswith(f"{WYD_SORT_PAGE}?")
    return client.get(loaded["Location"])


def widget_of(page):
    """✨ What the sort page hands its widget, as `json_script` writes it beside the form."""
    found = re.search(rf'<script id="sort-{WYD_SORT}" type="application/json">(.*?)</script>', page, re.S)
    return json.loads(found.group(1))


def send_as_shown(client, page):
    """✨ The sort sent as the widget would send it untouched: every item in the bucket and at the value it was handed,
    to the address the form posts to."""
    sort = widget_of(page)["placed"]
    action = re.search(r'hx-post="([^"]+)"', page).group(1).replace("&amp;", "&")
    return client.post(action, {"value": json.dumps(sort), "version": version_on(page)}, HTTP_HX_REQUEST="true")


@pytest.mark.django_db
def test_before_any_sort_a_demo_profile_leads_to_the_sort_with_its_cards_placed(on_whatever_you_do, settings):
    settings.DEBUG, settings.ANVILLE_DEMO_NOTICE = False, ""
    assert "data-demo-reveal" not in on_whatever_you_do.get(WYD_SORT_PAGE).content.decode()
    settings.ANVILLE_DEMO_NOTICE = "This is a demo."
    sort_page = on_whatever_you_do.get(WYD_SORT_PAGE).content.decode()
    assert f'<p class="back-to-hub" data-demo-reveal hidden><a href="{WYD_RETAKE}">' in sort_page
    assert "<h1 data-demo-reveal-hold>" in sort_page

    shown = load_profile(on_whatever_you_do, "tied-both", "leader")

    assert widget_of(shown.content.decode())["placed"]


@pytest.mark.django_db
def test_choosing_a_demo_profile_on_retake_clears_the_sort_and_leads_to_the_sort_with_its_cards_placed(
    on_whatever_you_do,
):
    send_as_shown(on_whatever_you_do, load_profile(on_whatever_you_do, "flat").content.decode())
    assert Result.objects.exists()

    shown = load_profile(on_whatever_you_do, "tied-both", "skip")

    assert not Result.objects.exists()
    assert widget_of(shown.content.decode())["placed"] == prefill(wyd_pathway(), "tied-both", "skip").sort


@pytest.mark.django_db
def test_a_demo_profile_hands_the_sort_its_placements_and_values_its_guide_those_answers_and_stores_nothing(
    on_whatever_you_do,
):
    """✨ fix-23: the widget starts at "All 36 sorted!" from these, with fine-tuning's sliders at their values; that it
    does is a hand check. fix-25: the guide gives the answers chosen."""
    shown = load_profile(on_whatever_you_do, "tied-pep", "behind")

    page = shown.content.decode()
    expected = prefill(wyd_pathway(), "tied-pep", "behind")
    assert widget_of(page)["placed"] == expected.sort
    assert summary("tied-pep", "behind") in page
    for framework, answer in expected.guide.pairs:
        assert f"<li>{escape(framework)}: {escape(answer)}</li>" in page
    assert not Result.objects.exists()
    assert WYD_SORT not in Response.objects.get().answers


@pytest.mark.django_db
def test_a_starting_profile_and_answers_that_do_not_fit_are_refused_with_the_reason(on_whatever_you_do):
    refused = on_whatever_you_do.post(WYD_RETAKE, {"profile": "tied-apest", "answers": "separate-apest-skip-pep"})

    assert refused.status_code == 400
    assert "separate-apest-skip-pep fits only tied-both." in refused.content.decode()


@pytest.mark.django_db
def test_sending_a_demo_profile_s_sort_unchanged_leads_to_its_first_pair_with_its_guide(on_whatever_you_do):
    page = load_profile(on_whatever_you_do, "tied-both", "one-each-way").content.decode()
    sent = send_as_shown(on_whatever_you_do, page)

    pair = on_whatever_you_do.get(sent["HX-Redirect"]).content.decode()
    assert Result.objects.get().scores == seeding(wyd_pathway(), "tied-both", "one-each-way").scores
    assert "1 of 4" in pair
    assert summary("tied-both", "one-each-way") in pair


@pytest.mark.django_db
def test_off_a_demo_system_no_demo_profile_reaches_the_sort(on_whatever_you_do, settings):
    settings.DEBUG, settings.ANVILLE_DEMO_NOTICE = False, ""

    page = on_whatever_you_do.get(f"{WYD_SORT_PAGE}?profile=tied-both&answers=leader").content.decode()

    assert "placed" not in widget_of(page)
    assert summary("tied-both", "leader") not in page


@pytest.mark.django_db
def test_on_the_faithful_port_no_demo_profile_is_offered_and_naming_one_is_refused(
    demo, client, django_user_model, load_pathway
):
    on_the_sort(client, django_user_model, load_pathway, faithful_port(), faithful_onboarding)
    assert WYD_RETAKE not in client.get(WYD_SORT_PAGE).content.decode()
    assert "<option" not in client.get(WYD_RETAKE).content.decode()

    refused = client.post(WYD_RETAKE, {"profile": "tied-both", "answers": "leader"})

    assert refused.status_code == 400
    assert not Result.objects.exists()
