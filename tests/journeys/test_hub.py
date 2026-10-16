# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import re

import pytest
from django.contrib.auth import get_user_model

from tests.documents import pathway_document
from tests.journeys.pages import loads_the_built_stylesheet, version_on
from tests.journeys.test_access import PASSWORD
from tests.journeys.test_consent import give_consent


@pytest.fixture
def signed_in_client(client, django_user_model):
    participant = django_user_model.objects.create_user(
        username="participant", email="participant@example.com"
    )
    client.force_login(participant)
    give_consent(client)
    return client


def a_fresh_participant(client, email):
    client.logout()
    client.force_login(get_user_model().objects.create_user(username=email, email=email))
    give_consent(client)
    return client


def the_calling_section(client):
    """✨ The calling section as the participant reads it, once the onboarding it requires is complete."""
    client.post("/sections/onboarding/complete/")
    return client.get("/sections/calling/").content.decode()


@pytest.mark.django_db
def test_a_participant_sees_an_intentional_empty_state_when_no_pathway_is_published(
    signed_in_client,
):
    response = signed_in_client.get("/hub/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Nothing to begin yet" in content
    assert "No pathway has been published here yet." in content


@pytest.mark.django_db
def test_a_signed_in_participant_is_shown_the_published_pathways_hub(signed_in_client, load_pathway):
    load_pathway(pathway_document())

    content = signed_in_client.get("/hub/").content.decode()

    assert "Test Pathway" in content
    assert "Before we begin" in content
    assert "Putting your calling into words" in content
    assert "Nothing to begin yet" not in content


@pytest.mark.django_db
def test_logging_in_for_the_first_time_asks_for_consent_before_the_pathway(client, django_user_model, load_pathway):
    load_pathway(pathway_document())
    django_user_model.objects.create_user(username="p", email="participant@example.com", password=PASSWORD)

    response = client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD}, follow=True)

    assert response.redirect_chain[-1][0] == "/consent/"
    assert "Test Pathway" not in response.content.decode()


@pytest.mark.django_db
def test_logging_in_after_consenting_leads_straight_to_the_published_pathway(client, django_user_model, load_pathway):
    load_pathway(pathway_document())
    django_user_model.objects.create_user(username="p", email="participant@example.com", password=PASSWORD)
    client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD})
    give_consent(client)
    client.post("/accounts/logout/")

    response = client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD}, follow=True)

    assert "Test Pathway" in response.content.decode()


@pytest.mark.django_db
def test_a_pathway_with_sections_but_no_content_renders_as_empty(signed_in_client, load_pathway):
    document = pathway_document()
    for section in document["content"]["sections"]:
        section["blocks"] = []
        section.pop("gate", None)
    load_pathway(document)

    content = signed_in_client.get("/hub/").content.decode()

    assert "Nothing to begin yet" in content
    assert "Before we begin" not in content


@pytest.mark.django_db
def test_a_participant_sees_their_own_wording_not_the_observers(signed_in_client, load_pathway):
    document = pathway_document()
    document["content"]["sections"][1]["blocks"][0]["prompt"] = {
        "participant": "Write your statement.",
        "observer": "Describe their calling.",
    }
    load_pathway(document)
    signed_in_client.post("/sections/onboarding/complete/")

    content = signed_in_client.get("/sections/calling/").content.decode()

    assert "Write your statement." in content
    assert "Describe their calling." not in content


def hub_entry(page, title):
    """✨ The hub's entry for one section, found by its title."""
    return next(entry for entry in re.findall(r'<li class="hub-section.*?</li>', page, re.S) if title in entry)


@pytest.mark.django_db
def test_each_hub_entry_shows_its_sections_time_estimate_even_while_locked(signed_in_client, load_pathway):
    """✨ So a participant can see how long the calling section takes before onboarding opens it."""
    document = pathway_document()
    document["content"]["sections"][1]["estimate"] = "About 15 minutes"
    load_pathway(document)

    page = signed_in_client.get("/hub/").content.decode()

    assert "About 15 minutes" in hub_entry(page, "Putting your calling into words")
    assert "Whole section:" not in hub_entry(page, "Putting your calling into words")  # ✨ plainly the section's here
    assert "Complete what comes before this to open it." in hub_entry(page, "Putting your calling into words")
    assert "time-estimate" not in hub_entry(page, "Before we begin")


@pytest.mark.django_db
def test_a_hub_entry_drops_its_estimate_once_the_section_is_started(signed_in_client, load_pathway):
    document = pathway_document()
    document["content"]["sections"][0]["estimate"] = "About 1 minute"
    load_pathway(document)
    version = version_on(signed_in_client.get("/sections/onboarding/").content.decode())

    signed_in_client.post("/answers/baseline-bible/", {"value": "5", "version": version})

    assert "About 1 minute" not in hub_entry(signed_in_client.get("/hub/").content.decode(), "Before we begin")


def side_card(page, title):
    """✨ The hub's side card for one section, found by its title."""
    cards = re.findall(r'<section class="card hub-side-card.*?</section>', page, re.S)
    return next(card for card in cards if title in card)


def with_a_side_card(document):
    """✨ The test pathway with a section after onboarding that the hub draws as a side card (ticket 49a)."""
    document["content"]["sections"].append(
        {
            "id": "voices",
            "title": "Five trusted voices",
            "requires": ["onboarding"],
            "side_card": {"sentence": "Invite people who know you well."},
            "blocks": [{"id": "voices-note", "type": "long_text", "prompt": "Who comes to mind?"}],
        }
    )
    return document


@pytest.mark.django_db
def test_a_side_card_section_is_drawn_as_a_card_and_not_listed_with_the_sections(signed_in_client, load_pathway):
    load_pathway(with_a_side_card(pathway_document()))

    page = signed_in_client.get("/hub/").content.decode()

    card = side_card(page, "Five trusted voices")
    assert "Invite people who know you well." in card
    assert "Locked" in card
    listed = re.findall(r'<li class="hub-section.*?</li>', page, re.S)
    assert listed and not any("Five trusted voices" in entry for entry in listed)

    signed_in_client.post("/sections/onboarding/complete/")

    assert "Not started" in side_card(signed_in_client.get("/hub/").content.decode(), "Five trusted voices")


@pytest.mark.django_db
def test_section_numbers_are_the_documents_and_none_shows_where_none_is_authored(signed_in_client, load_pathway):
    document = pathway_document()
    document["content"]["sections"][0]["title"] = "Section 1: Before we begin"
    document["content"]["sections"][1]["number"] = "02–04"
    load_pathway(document)

    page = signed_in_client.get("/hub/").content.decode()

    assert '<span class="srow-number">02–04</span>' in hub_entry(page, "Putting your calling into words")
    assert "srow-number" not in hub_entry(page, "Before we begin")


@pytest.mark.django_db
def test_the_header_counts_sections_complete_not_answers(signed_in_client, load_pathway):
    load_pathway(with_a_side_card(pathway_document()))
    version = version_on(signed_in_client.get("/sections/onboarding/").content.decode())
    signed_in_client.post("/answers/baseline-bible/", {"value": "5", "version": version})

    assert "0 of 3 sections complete" in signed_in_client.get("/hub/").content.decode()

    signed_in_client.post("/sections/onboarding/complete/")
    page = signed_in_client.get("/hub/").content.decode()

    assert "1 of 3 sections complete" in page
    assert "answered" not in page


def next_step(page):
    """✨ The hub's next-step panel."""
    return re.search(r'<section class="panel next.*?</section>', page, re.S).group()


@pytest.mark.django_db
def test_the_next_step_shows_the_sections_own_heading_and_sentence_or_else_its_title_and_estimate(
    signed_in_client, load_pathway
):
    """✨ Nothing in the next step is written in a template: what it says is the document's (ticket 49b)."""
    document = pathway_document()
    onboarding, calling = document["content"]["sections"][:2]
    onboarding["estimate"] = "About 1 minute"
    calling["next_step"] = {"heading": "Start with your calling.", "sentence": "Write a sentence or two about it."}
    load_pathway(document)

    panel = next_step(signed_in_client.get("/hub/").content.decode())
    assert "Before we begin" in panel
    assert "About 1 minute" in panel

    signed_in_client.post("/sections/onboarding/complete/")

    panel = next_step(signed_in_client.get("/hub/").content.decode())
    assert "Start with your calling." in panel
    assert "Write a sentence or two about it." in panel
    assert "Putting your calling into words" not in panel


@pytest.mark.django_db
def test_authored_text_is_shown_escaped_and_unaltered(signed_in_client, load_pathway):
    document = pathway_document()
    document["content"]["sections"][0]["blocks"][0]["body"] = '<script>alert("x")</script>'
    load_pathway(document)

    content = signed_in_client.get("/sections/onboarding/").content.decode()

    assert '<script>alert("x")</script>' not in content
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in content


@pytest.mark.django_db
def test_editing_one_prompt_and_loading_again_changes_the_app_for_a_participant_who_starts_afterwards(
    client, load_pathway
):
    load_pathway(pathway_document())
    assert "Write your statement." in the_calling_section(a_fresh_participant(client, "first@example.com"))

    edited = pathway_document()
    edited["content"]["sections"][1]["blocks"][0]["prompt"] = "Write the sentence God has been shaping in you."
    load_pathway(edited)

    content = the_calling_section(a_fresh_participant(client, "second@example.com"))
    assert "Write the sentence God has been shaping in you." in content
    assert "Write your statement." not in content


@pytest.mark.django_db
def test_loading_earlier_content_again_publishes_it_again_without_a_new_version(client, load_pathway):
    load_pathway(pathway_document())
    edited = pathway_document()
    edited["content"]["sections"][1]["blocks"][0]["prompt"] = "An edited prompt."
    load_pathway(edited)

    output = load_pathway(pathway_document())

    assert re.search(r"Republished pathway version \d+", output)
    content = the_calling_section(a_fresh_participant(client, "third@example.com"))
    assert "Write your statement." in content
    assert "An edited prompt." not in content


@pytest.mark.django_db
def test_the_hub_loads_the_built_javascript_module(signed_in_client):
    response = signed_in_client.get("/hub/")

    assert re.search(
        r'<script type="module" crossorigin="" src="/static/assets/main-[\w-]+\.js"></script>',
        response.content.decode(),
    )


@pytest.mark.django_db
def test_the_hub_loads_the_built_stylesheet(signed_in_client):
    assert loads_the_built_stylesheet(signed_in_client.get("/hub/").content.decode())


@pytest.mark.django_db
def test_an_anonymous_visitor_to_the_hub_is_sent_to_log_in(client):
    response = client.get("/hub/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/hub/"
