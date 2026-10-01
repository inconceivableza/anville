"""✨ The observer's assessment: the same sort, about the participant, in the third person (ADR 0005).

An observer reaches it only through the link they claimed, sends it once, and never sees it again through any link.
"""

import json

import pytest

from tests.documents import sort_pathway
from tests.journeys.test_contact_list import JO, save_contacts
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import issue_link, observer  # noqa: F401  (observer is a fixture, used by name)
from tests.journeys.test_observer_landing import claim, the_observers_page
from tests.journeys.test_results import widget_data


def observed_pathway():
    """✨ The sort pathway with a contact list in onboarding, and observer wording for one bucket and the sort's heading
    (its item a5 already has observer wording)."""
    document = sort_pathway()
    document["content"]["sections"][0]["blocks"].append({"id": "contacts", "type": "contact_list", "min_rows": 2})
    not_me = document["instrument"]["buckets"][0]
    not_me["label"] = {"participant": not_me["label"], "observer": "Not {name}"}
    document["presentation"]["sort_wording"] = {
        "sort_heading": {"participant": "Sort your strengths", "observer": "Sort {name}'s strengths"},
    }
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(observed_pathway())
    save_contacts(signed_in_client, JO, ("Priya", "priya@example.com"))
    return signed_in_client


# The observer's wording


@pytest.mark.django_db
def test_the_observers_widget_is_in_the_observers_wording_naming_the_participant(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))

    page = the_observers_page(observer).content.decode()

    shown = widget_data(page)
    assert shown["items"] == [
        {"id": "a5", "text": "Building something that will outlast them"},
        {"id": "p1", "text": "Going against the grain"},
    ]
    assert shown["buckets"][0]["label"] == "Not participant"
    assert shown["wording"]["sort_heading"] == "Sort participant's strengths"
    assert "{name}" not in json.dumps(shown)
    for participants_wording in ("outlast you", "Sort your strengths", '"Not me"'):
        assert participants_wording not in page
