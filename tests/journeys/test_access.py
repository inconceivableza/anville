import pytest


@pytest.mark.django_db
def test_a_visitor_can_reach_the_login_page(client):
    response = client.get("/accounts/login/")

    assert response.status_code == 200
