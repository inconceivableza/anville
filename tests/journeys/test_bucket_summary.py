# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ How the cards were spread over the buckets, shown between the rounds and once every card is placed, unless the
document hides it (`sorts_hide_bucket_summary`, ticket 108): seeing the spread invites people to even it out."""

import pytest

from tests.journeys.test_havent_seen_this import a_participant
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import issue_link, observer  # noqa: F401  (observer is a fixture)
from tests.journeys.test_observer_assessment import observed_pathway
from tests.journeys.test_observer_landing import claim, the_observers_page
from tests.journeys.test_results import STRENGTHS, widget_data


@pytest.mark.django_db
@pytest.mark.parametrize("hides", [True, False], ids=["hidden", "by default"])
def test_neither_the_participants_sort_nor_an_observers_shows_the_bucket_summary_where_the_document_hides_it(
    signed_in_client, load_pathway, observer, hides  # noqa: F811
):
    document = {**observed_pathway(), **({"sorts_hide_bucket_summary": True} if hides else {})}
    a_participant(signed_in_client, load_pathway, document)
    claim(observer, issue_link(signed_in_client, "Jo"))

    participants = widget_data(signed_in_client.get(f"/sections/{STRENGTHS}/").content.decode())
    observers = widget_data(the_observers_page(observer).content.decode())

    assert [participants["bucket_summary"], observers["bucket_summary"]] == [not hides, not hides]
