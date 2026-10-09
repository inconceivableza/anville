"""✨ Joining a group by its link (ticket A2): sign up without the enrolment code, consent, then join knowingly."""

import re
from html import unescape

import pytest
from django.contrib.auth import get_user

from organisations.models import Group, Membership, Organisation
from tests.journeys.pages import text_of, version_on
from tests.journeys.test_access import PASSWORD, require_the_code


@pytest.fixture
def cohort():
    church = Organisation.objects.create(name="Example Church")
    return Group.objects.create(organisation=church, name="Autumn cohort", type=Group.Type.COHORT)


def join_link(group):
    return f"/join/{group.join_token}/"


def hidden_next(page):
    """✨ Where a form sends the browser on afterwards, as its hidden field carries it."""
    found = re.search(r'name="next" value="([^"]*)"', page)
    return unescape(found.group(1)) if found else None


@pytest.mark.django_db
def test_a_new_person_signs_up_without_the_code_consents_and_joins_knowingly(client, settings, cohort):
    require_the_code(settings)

    to_sign_up = client.get(join_link(cohort))
    sign_up_page = client.get(to_sign_up.url).content.decode()
    assert 'name="enrolment_code"' not in sign_up_page
    form = {"display_name": "Sam", "email": "sam@example.com", "password1": PASSWORD, "password2": PASSWORD}
    to_join = client.post("/accounts/signup/", {**form, "is_adult": "on", "next": hidden_next(sign_up_page)})
    assert get_user(client).is_authenticated

    to_consent = client.get(to_join.url)
    consent_page = client.get(to_consent.url).content.decode()
    back_to_join = client.post(
        "/consent/", {"decision": "agree", "version": version_on(consent_page), "next": hidden_next(consent_page)}
    )
    assert back_to_join.url == join_link(cohort)

    join_page = text_of(client.get(join_link(cohort)).content.decode())
    assert "Example Church" in join_page
    assert "Autumn cohort" in join_page
    assert "They never see your answers." in join_page
    assert not Membership.objects.exists()

    joined = client.post(join_link(cohort))

    assert joined.url == "/hub/"
    assert Membership.objects.filter(participant=get_user(client), group=cohort).exists()


@pytest.mark.django_db
def test_an_unknown_or_replaced_link_says_it_no_longer_works_and_names_nothing(client, cohort):
    replaced = join_link(cohort)
    Group.objects.filter(pk=cohort.pk).update(join_token="a-new-token")

    for link in ["/join/no-such-token/", replaced]:
        page = text_of(client.get(link).content.decode())

        assert "This link no longer works" in page
        assert "ask whoever sent it" in page
        assert "Example Church" not in page
        assert "Autumn cohort" not in page
