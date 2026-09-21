import pytest


@pytest.fixture
def signed_in_client(client, django_user_model):
    participant = django_user_model.objects.create_user(
        username="participant", email="participant@example.com"
    )
    client.force_login(participant)
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
def test_an_anonymous_visitor_is_sent_to_log_in(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/"
