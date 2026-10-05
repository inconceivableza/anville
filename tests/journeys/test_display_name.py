"""✨ The participant is named by the display name they gave at sign-up, never by their email (ticket 37).

An account without one, made before display names existed, is named by the part of its email before the @, taken from
the email and never from the username.
"""

import pytest

from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_access import require_the_code, sign_up
from tests.journeys.test_consent import give_consent
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_invitations import issue_link, observer  # noqa: F401  (observer is a fixture, used by name)
from tests.journeys.test_observer_assessment import observed_pathway
from tests.journeys.test_observer_landing import claim, the_observers_page
from tests.journeys.test_results import results, submit_sort, widget_data

EMAIL, DISPLAY_NAME = "sam.jones@example.com", "Ayodele"


def signed_up_as_ayodele(client, settings):
    require_the_code(settings)
    sign_up(client, email=EMAIL, display_name=DISPLAY_NAME)
    give_consent(client)
    return client


def the_results_page(client):
    client.post("/sections/onboarding/complete/")
    submit_sort(client, complete_sort())
    return results(client).content.decode()


@pytest.mark.django_db
def test_the_participants_own_results_name_them_by_their_display_name_never_their_email(
    client, settings, load_pathway
):
    load_pathway(sort_pathway())

    page = the_results_page(signed_up_as_ayodele(client, settings))

    assert DISPLAY_NAME in page
    assert "sam.jones" not in page


@pytest.mark.django_db
def test_the_observers_welcome_and_sort_name_the_participant_by_their_display_name(
    client, settings, load_pathway, observer  # noqa: F811
):
    load_pathway(observed_pathway())
    participant = signed_up_as_ayodele(client, settings)
    save_contacts(participant, JO, PRIYA)
    link = issue_link(participant, "Jo")

    welcome = observer.get(link).content.decode()
    claim(observer, link)
    sort = widget_data(the_observers_page(observer).content.decode())

    assert DISPLAY_NAME in welcome
    assert "sam.jones" not in welcome
    assert DISPLAY_NAME in sort["wording"]["sort_heading"]


@pytest.mark.django_db
def test_an_account_without_a_display_name_is_named_from_its_email_never_its_username(
    client, django_user_model, load_pathway
):
    load_pathway(sort_pathway())
    client.force_login(django_user_model.objects.create_user(username="someone-else", email=EMAIL))
    give_consent(client)

    page = the_results_page(client)

    assert "sam.jones" in page
    assert "someone-else" not in page
