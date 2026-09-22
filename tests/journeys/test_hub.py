import re

import pytest
from django.contrib.auth import get_user_model

from tests.documents import pathway_document
from tests.journeys.test_access import PASSWORD


@pytest.fixture
def signed_in_client(client, django_user_model):
    participant = django_user_model.objects.create_user(
        username="participant", email="participant@example.com"
    )
    client.force_login(participant)
    return client


def a_fresh_participant(client, email):
    client.logout()
    client.force_login(get_user_model().objects.create_user(username=email, email=email))
    return client


@pytest.mark.django_db
def test_a_participant_sees_an_intentional_empty_state_when_no_pathway_is_published(
    signed_in_client,
):
    response = signed_in_client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Nothing to begin yet" in content
    assert "No pathway has been published here yet." in content


@pytest.mark.django_db
def test_a_signed_in_participant_is_shown_the_published_pathway(signed_in_client, load_pathway):
    load_pathway(pathway_document())

    content = signed_in_client.get("/").content.decode()

    assert "Test Pathway" in content
    assert "Before we begin" in content
    assert "Putting your calling into words" in content
    assert "Write your statement." in content
    assert "Nothing to begin yet" not in content


@pytest.mark.django_db
def test_logging_in_leads_straight_to_the_published_pathway(client, django_user_model, load_pathway):
    load_pathway(pathway_document())
    django_user_model.objects.create_user(username="p", email="participant@example.com", password=PASSWORD)

    response = client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD}, follow=True)

    assert "Test Pathway" in response.content.decode()


@pytest.mark.django_db
def test_a_pathway_with_sections_but_no_content_renders_as_empty(signed_in_client, load_pathway):
    document = pathway_document()
    for section in document["content"]["sections"]:
        section["blocks"] = []
        section.pop("gate", None)
    load_pathway(document)

    content = signed_in_client.get("/").content.decode()

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

    content = signed_in_client.get("/").content.decode()

    assert "Write your statement." in content
    assert "Describe their calling." not in content


@pytest.mark.django_db
def test_authored_text_is_shown_escaped_and_unaltered(signed_in_client, load_pathway):
    document = pathway_document()
    document["content"]["sections"][0]["blocks"][0]["body"] = '<script>alert("x")</script>'
    load_pathway(document)

    content = signed_in_client.get("/").content.decode()

    assert '<script>alert("x")</script>' not in content
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in content


@pytest.mark.django_db
def test_editing_one_prompt_and_loading_again_changes_the_app_for_a_participant_who_starts_afterwards(
    client, load_pathway
):
    load_pathway(pathway_document())
    assert "Write your statement." in a_fresh_participant(client, "first@example.com").get("/").content.decode()

    edited = pathway_document()
    edited["content"]["sections"][1]["blocks"][0]["prompt"] = "Write the sentence God has been shaping in you."
    load_pathway(edited)

    content = a_fresh_participant(client, "second@example.com").get("/").content.decode()
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
    content = a_fresh_participant(client, "third@example.com").get("/").content.decode()
    assert "Write your statement." in content
    assert "An edited prompt." not in content


@pytest.mark.django_db
def test_the_hub_loads_the_built_javascript_module(signed_in_client):
    response = signed_in_client.get("/")

    assert re.search(
        r'<script type="module" crossorigin="" src="/static/assets/main-[\w-]+\.js"></script>',
        response.content.decode(),
    )


@pytest.mark.django_db
def test_an_anonymous_visitor_is_sent_to_log_in(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/"
