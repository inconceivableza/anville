"""✨ The comparison: the participant's own result beside the mean of what their observers see (ADR 0005).

Below the minimum number of observers the participant sees how many have answered and no numbers. From the minimum
up they see each construct's percent beside the observers' mean, never a single observer's percent, and never which
person has answered.
"""

import re

import pytest
from django.contrib.auth import get_user_model

from engine.models import Contact, Publication, Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_observer_responses import SEED_PASSWORD, an_observer, seed
from tests.journeys.test_results import (  # noqa: F401 (signed_in is a fixture, used by name)
    SORT,
    STRENGTHS,
    in_order,
    results,
    signed_in,
    submit_sort,
)

PRIYA, CHRIS = "Priya Naidoo", "Chris Mbeki"


def comparison(client, block_id=SORT):
    return client.get(f"/results/{block_id}/comparison/")


def observer_sort(apostle_share):
    """✨ An observer's sort of the two items, splitting 100 between them, so its percents are easy to read: Apostle
    and Deliver get `apostle_share`, Prophet and Ponder the rest."""
    return complete_sort(
        a5={"bucket": "strength", "value": apostle_share}, p1={"bucket": "not-me", "value": 100 - apostle_share}
    )


# ✨ Each observer's percents: 80/20, 70/30 and 60/40, so the means are 70 and 30. The participant's own are 90/10.
THREE_OBSERVERS = [observer_sort(80), observer_sort(70), observer_sort(60)]


def with_observers(client, participant, sorts, **marks):
    """✨ The participant submits their own sort, then an observer response is stored for each of `sorts`."""
    submit_sort(client, complete_sort())
    response = Response.objects.get(participant=participant)
    for sort in sorts:
        an_observer(response, sort, **marks)
    return response


def with_contacts(response, *names):
    for position, name in enumerate(names):
        email = f"{name.split()[0].lower()}@example.com"
        Contact.objects.create(
            response=response, block_id="contacts", role=Contact.Role.CONTACT, position=position, name=name, email=email
        )


@pytest.mark.django_db
def test_below_the_minimum_the_comparison_shows_how_many_have_answered_and_no_numbers(signed_in, participant):
    with_observers(signed_in, participant, THREE_OBSERVERS[:2])

    page = comparison(signed_in)

    shown = page.content.decode()
    assert page.status_code == 200
    assert "2 of 3" in shown
    assert "%" not in shown


@pytest.mark.django_db
def test_no_single_observers_percent_reaches_the_participant_only_the_means(signed_in, participant):
    with_observers(signed_in, participant, THREE_OBSERVERS)

    shown = comparison(signed_in).content.decode()

    assert "70%" in shown and "30%" in shown
    for single in ("80%", "60%", "20%", "40%"):
        assert single not in shown


@pytest.mark.django_db
def test_each_construct_shows_the_participants_percent_beside_the_observers_mean_paired_by_construct(
    signed_in, participant
):
    """✨ Ponder is declared before Deliver but the participant's result ranks Deliver first, so pairing by position
    would put Deliver's 90% beside Ponder's 30%."""
    with_observers(signed_in, participant, THREE_OBSERVERS)

    shown = comparison(signed_in).content.decode()

    assert in_order(shown, "Apostle", "90%", "70%", "Prophet", "10%", "30%")
    assert in_order(shown, "Deliver", "90%", "70%", "Ponder", "10%", "30%")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "observers, count",
    [(1, "1 of 3"), (3, "3 people")],
    ids=["below the minimum", "at the minimum"],
)
def test_the_comparison_shows_how_many_have_answered_never_who(signed_in, participant, observers, count):
    response = with_observers(signed_in, participant, THREE_OBSERVERS[:observers])
    with_contacts(response, PRIYA, CHRIS)

    shown = comparison(signed_in).content.decode()

    assert count in shown
    assert PRIYA not in shown and CHRIS not in shown


@pytest.mark.django_db
def test_another_participants_observers_are_never_counted(signed_in, participant):
    with_observers(signed_in, participant, THREE_OBSERVERS[:2])
    someone_else = get_user_model().objects.create_user(username="someone", email="someone@example.com")
    their_response = Response.objects.create(participant=someone_else, version=Publication.current_version())
    for sort in THREE_OBSERVERS:
        an_observer(their_response, sort)

    shown = comparison(signed_in).content.decode()

    assert "2 of 3" in shown
    assert "%" not in shown


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_data, illustrative",
    [([True, True, True], True), ([True, False, True], False)],
    ids=["every observer test data", "one real observer"],
)
def test_the_comparison_says_it_is_illustrative_only_when_every_observer_is_test_data(
    signed_in, participant, test_data, illustrative
):
    submit_sort(signed_in, complete_sort())
    response = Response.objects.get(participant=participant)
    for sort, is_test_data in zip(THREE_OBSERVERS, test_data):
        an_observer(response, sort, is_test_data=is_test_data)

    shown = comparison(signed_in).content.decode()

    assert ("illustrative" in shown) is illustrative


@pytest.mark.django_db
def test_a_seeded_participant_reaches_the_comparison_from_their_results_page(client, load_pathway):
    """✨ The seeded participant has a result but no onboarding and no completed sections."""
    load_pathway(sort_pathway())
    seed()
    client.post("/accounts/login/", {"login": Response.objects.get().participant.email, "password": SEED_PASSWORD})

    button = re.search(r'action="(/results/[\w-]+/comparison/visit/)"', results(client).content.decode())

    assert button, "no way to the comparison on the results page"
    page = client.post(button.group(1), follow=True)
    assert page.redirect_chain[-1][0].endswith("/comparison/")
    assert page.status_code == 200
    assert "%" in page.content.decode()
    assert "illustrative" in page.content.decode()


@pytest.mark.django_db
def test_before_a_result_the_comparison_leads_to_the_sort(signed_in):
    page = comparison(signed_in)

    assert page.status_code == 302
    assert page.url == f"/sections/{STRENGTHS}/"
