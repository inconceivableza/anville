"""✨ Joining a group by its link (ticket A2): sign up without the enrolment code, consent, then join knowingly."""

import pytest

from organisations.models import Group, Organisation
from tests.journeys.pages import text_of


@pytest.fixture
def cohort():
    church = Organisation.objects.create(name="Example Church")
    return Group.objects.create(organisation=church, name="Autumn cohort", type=Group.Type.COHORT)


def join_link(group):
    return f"/join/{group.join_token}/"


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
