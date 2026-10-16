# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from tests.documents import complete_sort, pathway_document, sort_pathway
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


@pytest.fixture
def trusted_voices(signed_in_client, load_pathway):
    """✨ A participant past Before we begin, whose hub has Five trusted voices beside it, over the sort pathway so that
    observers can answer."""
    from tests.journeys.test_contact_list import with_trusted_voices  # ✨ here, as that module imports this one

    load_pathway(with_trusted_voices(sort_pathway()))
    signed_in_client.post("/sections/onboarding/complete/")
    return signed_in_client


def voices_card(client):
    """✨ The hub's Five trusted voices card."""
    page = client.get("/hub/").content.decode()
    return re.search(r'<section class="card dark hub-side-card hub-voices.*?</section>', page, re.S).group()


def meters(card):
    """✨ The card's meters, as {"Invited": n, "Answered": n}."""
    return {label: int(count) for label, count in re.findall(r"<span>(Invited|Answered)</span><span>(\d+) /", card)}


def tag_of(card):
    return re.search(r'<span class="tag[^"]*">(.*?)</span>', card).group(1)


def add_people_with_links(client, *people):
    """✨ Add each person on Five trusted voices' page, which makes their link, and return the links."""
    from tests.journeys.test_contact_list import VOICES, add_person, link_shown  # ✨ as above

    return [link_shown(client.get(add_person(client, person, VOICES).url).content.decode()) for person in people]


@pytest.mark.django_db
def test_the_voices_card_counts_working_links_as_invited_and_assessments_sent_as_answered(trusted_voices):
    from tests.journeys.test_invitations import invitation_action  # ✨ as above
    from tests.journeys.test_observer_assessment import send
    from tests.journeys.test_observer_landing import claim

    jo, priya, _ = add_people_with_links(trusted_voices, *PEOPLE)
    trusted_voices.post(invitation_action(trusted_voices, "Chris", "revoke"))
    assert meters(voices_card(trusted_voices)) == {"Invited": 2, "Answered": 0}

    claim(Client(), priya)
    jos_observer = Client()
    claim(jos_observer, jo)
    assert meters(voices_card(trusted_voices)) == {"Invited": 2, "Answered": 0}

    send(jos_observer, complete_sort())
    assert meters(voices_card(trusted_voices)) == {"Invited": 2, "Answered": 1}


@pytest.mark.django_db
def test_the_voices_card_names_nobody(trusted_voices):
    add_people_with_links(trusted_voices, *PEOPLE)

    card = voices_card(trusted_voices)

    for name, email in PEOPLE:
        assert name not in card
        assert email not in card


@pytest.mark.django_db
def test_once_five_trusted_voices_is_complete_the_card_never_asks_for_more_people(trusted_voices):
    add_people_with_links(trusted_voices, PEOPLE[0])
    assert tag_of(voices_card(trusted_voices)) == "2 more needed"

    trusted_voices.post("/sections/voices/complete/")

    card = voices_card(trusted_voices)
    assert tag_of(card) == "Complete"
    assert "needed" not in card


PEOPLE = (("Jo", "jo@example.com"), ("Priya", "priya@example.com"), ("Chris", "chris@example.com"))


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


def with_a_photo(document, section_id="calling"):
    """✨ The test pathway with the hub's photo of grass, a file beside the document, named by a section (ticket 49b)."""
    document["photos"] = {
        section_id: {"file": "grass.jpg", "credit": {"kind": "courtesy", "text": "Photograph of grass from Unsplash."}}
    }
    return document


@pytest.mark.django_db
def test_the_next_step_is_drawn_over_its_sections_photo_and_without_one_where_it_has_none(
    signed_in_client, load_pathway
):
    load_pathway(with_a_photo(pathway_document()))

    page = signed_in_client.get("/hub/")
    assert page.status_code == 200
    assert "<img" not in next_step(page.content.decode())

    signed_in_client.post("/sections/onboarding/complete/")

    photo = re.search(r'<img src="([^"]+)"', next_step(signed_in_client.get("/hub/").content.decode())).group(1)
    served = signed_in_client.get(photo)
    assert served.status_code == 200
    assert served["Content-Type"] == "image/jpeg"


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
