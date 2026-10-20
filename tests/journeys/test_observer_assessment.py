# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The observer's assessment: the same sort, about the participant, in the third person (ADR 0005).

An observer reaches it only through the link they claimed, sends it once, and never sees it again through any link.
"""

import json
import re

import pytest
from django.test import Client
from django.utils import timezone

from access.consent import current_text_version
from access.models import Consent
from engine.models import Contact, Invitation, ObserverAssessments, ObserverResponse, Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_coach_checklist import choose
from tests.journeys.test_coach_link import issue_coach_link, with_a_coach_and_contacts
from tests.journeys.test_consent import give_consent, withdraw_consent
from tests.journeys.test_contact_list import CHRIS, JO, PRIYA, save_contacts, take_off_the_list
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import (  # noqa: F401  (observer is a fixture, used by name)
    A_WRONG_TOKEN,
    invitation_action,
    issue_link,
    observer,
    token_of,
)
from tests.journeys.pages import text_of
from tests.journeys.test_observer_landing import claim, the_observers_page
from tests.journeys.test_results import SORT, submit_sort, widget_data


def observed_pathway():
    """✨ The sort pathway with a contact list in onboarding, and observer wording for one bucket and the sort's heading
    (its item a5 already has observer wording)."""
    document = sort_pathway()
    document["content"]["sections"][0]["blocks"].append({"id": "contacts", "type": "contact_list", "needed": 2})
    not_me = document["instrument"]["buckets"][0]
    not_me["label"] = {"participant": not_me["label"], "observer": "Not {name}"}
    document["presentation"]["sort_wording"] = {
        "sort_heading": {"participant": "Sort your strengths", "observer": "Sort {name}'s strengths"},
    }
    document.setdefault("observers", {})["relationship"] = {
        "question": "Your relationship to {name}",
        "choices": [{"id": "family", "label": "Family member"}, {"id": "friend", "label": "Close friend"}],
    }
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(observed_pathway())
    save_contacts(signed_in_client, JO, PRIYA)
    return signed_in_client


def send(client, assessment, link=None, relationship=None):
    """✨ Send an observer assessment as the widget's form does: through a link if given, else by the observer cookie."""
    posted = {"value": json.dumps(assessment), **({"relationship": relationship} if relationship is not None else {})}
    return client.post(f"{link}assessment/" if link else "/observe/assessment/", posted)


def observer_assessments():
    """✨ What the observer average reads of the participant's observers."""
    return ObserverResponse.assessments_for(Response.objects.get())


# Sending


@pytest.mark.django_db
@pytest.mark.parametrize("through", ["cookie", "own link"])
def test_an_assessment_sent_through_the_claimed_link_counts_on_its_own_and_leaves_the_participants_answers_alone(
    participant, observer, through  # noqa: F811
):
    own_link = claim(observer, issue_link(participant, "Jo"))
    answers_before = Response.objects.get().answers

    if through == "cookie":
        sent = send(observer, complete_sort())
    else:
        sent = send(Client(), complete_sort(), own_link)

    assert sent.status_code == 303
    assert sent["Location"] == ("/observe/" if through == "cookie" else own_link)
    assert observer_assessments() == ObserverAssessments(assessments=[complete_sort()], all_test_data=False)
    assert Response.objects.get().answers == answers_before


@pytest.mark.django_db
def test_an_observer_can_send_straight_after_placing_the_cards_and_each_item_keeps_its_buckets_seed(
    participant, observer  # noqa: F811
):
    claim(observer, issue_link(participant, "Jo"))

    sent = send(observer, {"a5": {"bucket": "strength"}, "p1": {"bucket": "not-me"}})

    assert sent.status_code == 303
    assert observer_assessments().assessments == [
        {"a5": {"bucket": "strength", "value": 85}, "p1": {"bucket": "not-me", "value": 10}}
    ]


@pytest.mark.django_db
def test_sending_without_fine_tuning_has_wording_of_its_own_apart_from_sending_after_it(
    participant, observer  # noqa: F811
):
    claim(observer, issue_link(participant, "Jo"))

    wording = widget_data(the_observers_page(observer).content.decode())["wording"]

    assert wording["send_now_label"] == "Skip fine-tuning and send →"
    assert wording["submit_label"] == "Send my assessment →"


@pytest.mark.django_db
@pytest.mark.parametrize("by", ["unclaimed copy", "claimed copy", "wrong link", "no claim"])
def test_neither_the_participants_copy_nor_a_wrong_link_nor_no_claim_can_send_an_assessment(
    participant, observer, by  # noqa: F811
):
    link = issue_link(participant, "Jo")
    if by == "claimed copy":
        claim(observer, link)
    if by == "wrong link":
        link = f"/observe/{A_WRONG_TOKEN}/"

    refused = send(participant, complete_sort(), None if by == "no claim" else link)

    assert refused.status_code == 404
    assert not ObserverResponse.objects.exists()


@pytest.mark.django_db
def test_once_sent_the_assessment_is_locked_and_no_link_offers_it_or_shows_it_again(participant, observer):  # noqa: F811
    own_link = claim(observer, issue_link(participant, "Jo"))
    first = complete_sort(a5={"bucket": "strength", "value": 73})
    send(observer, first)

    again = send(Client(), complete_sort(), own_link)

    assert again.status_code == 409
    assert observer_assessments().assessments == [first]
    for page in (the_observers_page(observer), Client().get(own_link)):
        assert page.status_code == 200
        assert widget_data(page.content.decode()) is None
        assert 'name="value"' not in page.content.decode()


@pytest.mark.django_db
def test_an_assessment_that_breaks_the_contract_is_refused_and_nothing_is_stored(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))

    refused = send(observer, complete_sort(a5={"bucket": "strength", "value": 101}))

    assert refused.status_code == 400
    assert not ObserverResponse.objects.exists()


@pytest.mark.django_db
def test_the_relationship_chosen_is_stored_with_the_assessment(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))
    asked = the_observers_page(observer).content.decode()
    assert re.search(r'<select[^>]*name="relationship"', asked)

    send(observer, complete_sort(), relationship="friend")

    assert ObserverResponse.objects.get().relationship == "friend"


@pytest.mark.django_db
def test_a_relationship_outside_the_offered_choices_is_refused_and_nothing_is_stored(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))

    refused = send(observer, complete_sort(), relationship="colleague")

    assert refused.status_code == 400
    assert not ObserverResponse.objects.exists()


# Outliving the link (ADR 0007), held apart from who sent it


@pytest.mark.django_db
@pytest.mark.parametrize("ended", ["revoked", "reissued", "taken off the list"])
def test_a_sent_assessment_survives_its_link_being_revoked_or_reissued_or_its_person_taken_off_the_list(
    participant, observer, ended  # noqa: F811
):
    claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())

    if ended == "revoked":
        participant.post(invitation_action(participant, "Jo", "revoke"))
    if ended == "reissued":
        issue_link(participant, "Jo")
    if ended == "taken off the list":
        take_off_the_list(participant, "Jo")

    assert observer_assessments().assessments == [complete_sort()]


@pytest.mark.django_db
def test_a_reissued_link_once_claimed_sends_an_assessment_of_its_own_and_both_count(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())
    reissued_to = Client()
    claim(reissued_to, issue_link(participant, "Jo"))

    assert send(reissued_to, complete_sort()).status_code == 303

    assert len(observer_assessments().assessments) == 2


@pytest.mark.django_db
def test_nothing_kept_with_a_sent_assessment_ties_it_to_the_contact_or_their_link(participant, observer):  # noqa: F811
    secret = token_of(claim(observer, issue_link(participant, "Jo")))
    send(observer, complete_sort())

    invitation = Invitation.objects.get(contact__name="Jo")
    kept = ObserverResponse.objects.values().get()
    assert "contact_id" not in kept and "invitation_id" not in kept
    ties = {invitation.token_hash, invitation.secret_hash, secret}
    assert [field for field, value in kept.items() if str(value) in ties] == []


# Withdrawing (ticket 15b)


def withdraw(client, link=None):
    """✨ Withdraw as the observer's page does: through a link if given, else by the observer cookie."""
    return client.post(f"{link}withdraw/" if link else "/observe/withdraw/")


@pytest.mark.django_db
@pytest.mark.parametrize("through", ["cookie", "own link"])
def test_withdrawing_through_the_claimed_link_deletes_that_observers_answers_and_nobody_elses(
    participant, observer, through  # noqa: F811
):
    own_link = claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())
    someone_else = Client()
    claim(someone_else, issue_link(participant, "Priya"))
    kept = complete_sort(a5={"bucket": "strength", "value": 73})
    send(someone_else, kept)

    withdrawn = withdraw(observer) if through == "cookie" else withdraw(Client(), own_link)

    assert withdrawn.status_code == 200
    assert observer_assessments().assessments == [kept]


@pytest.mark.django_db
def test_a_send_that_reaches_the_store_after_a_withdrawal_on_the_same_link_stores_nothing(participant, observer):  # noqa: F811
    """✨ A send and a withdrawal at the same moment: the send's view has already found the link live when the
    withdrawal ends it, so the store itself must find the link ended and keep nothing. Two real requests racing are
    impractical on the test database, so the send is made straight to the store after the withdrawal."""
    secret = token_of(claim(observer, issue_link(participant, "Jo")))
    withdraw(observer)

    stored = ObserverResponse.send(Response.objects.get(), secret, complete_sort())

    assert stored is None
    assert observer_assessments().assessments == []


@pytest.mark.django_db
@pytest.mark.parametrize("by", ["unclaimed copy", "claimed copy", "revoked own link", "expired own link"])
def test_neither_the_participants_copy_nor_a_link_that_stopped_working_can_withdraw(
    participant, observer, by  # noqa: F811
):
    copy = issue_link(participant, "Jo")
    if by == "unclaimed copy":
        link, sent = copy, None
    else:
        own_link = claim(observer, copy)
        send(observer, complete_sort())
        link, sent = (copy if by == "claimed copy" else own_link), [complete_sort()]
    if by == "revoked own link":
        participant.post(invitation_action(participant, "Jo", "revoke"))
    if by == "expired own link":
        Invitation.objects.update(expires_at=timezone.now())

    refused = withdraw(participant, link)

    assert refused.status_code == 404
    assert observer_assessments().assessments == (sent or [])


@pytest.mark.django_db
@pytest.mark.parametrize("through", ["cookie", "own link"])
def test_opening_the_withdrawal_page_deletes_nothing_and_asks_with_a_post(participant, observer, through):  # noqa: F811
    own_link = claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())

    opened = observer.get("/observe/withdraw/" if through == "cookie" else f"{own_link}withdraw/")

    assert opened.status_code == 200
    assert re.search(r'<form method="post" action="[^"]*/withdraw/"', opened.content.decode())
    assert observer_assessments().assessments == [complete_sort()]
    assert the_observers_page(observer).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("through", ["cookie", "own link"])
def test_after_sending_the_claimed_link_offers_only_the_thanks_and_a_way_to_withdraw(
    participant, observer, through  # noqa: F811
):
    own_link = claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())

    page = (the_observers_page(observer) if through == "cookie" else Client().get(own_link)).content.decode()

    withdraw_at = "/observe/withdraw/" if through == "cookie" else f"{own_link}withdraw/"
    assert f'href="{withdraw_at}"' in page
    assert "<form" not in page and "<select" not in page and "Not built yet" not in page


# While the participant's consent is withdrawn (ticket 45)


@pytest.mark.django_db
@pytest.mark.parametrize("through", ["cookie", "own link"])
def test_while_the_participant_has_withdrawn_no_assessment_is_sent_or_stored(participant, observer, through):  # noqa: F811
    own_link = claim(observer, issue_link(participant, "Jo"))
    withdraw_consent(participant)

    refused = send(observer, complete_sort()) if through == "cookie" else send(Client(), complete_sort(), own_link)

    assert refused.status_code == 404
    assert observer_assessments().assessments == []


@pytest.mark.django_db
@pytest.mark.parametrize("through", ["cookie", "own link"])
def test_while_the_participant_has_withdrawn_an_observer_can_still_withdraw_their_answers(
    participant, observer, through  # noqa: F811
):
    own_link = claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())
    withdraw_consent(participant)

    opened = observer.get("/observe/withdraw/" if through == "cookie" else f"{own_link}withdraw/")
    withdrawn = withdraw(observer) if through == "cookie" else withdraw(Client(), own_link)

    assert opened.status_code == 200
    assert withdrawn.status_code == 200
    assert observer_assessments().assessments == []


@pytest.mark.django_db
def test_consenting_again_opens_every_observers_link_as_it_was(participant, observer):  # noqa: F811
    unclaimed = issue_link(participant, "Priya")
    own_link = claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())
    expiries = list(Invitation.objects.order_by("pk").values_list("expires_at", flat=True))
    withdraw_consent(participant)

    give_consent(participant)

    assert Client().get(unclaimed).status_code == 200
    assert Client().get(own_link).status_code == 200
    assert the_observers_page(observer).status_code == 200
    assert observer_assessments().assessments == [complete_sort()]
    assert list(Invitation.objects.order_by("pk").values_list("expires_at", flat=True)) == expiries


@pytest.mark.django_db
def test_consent_merely_out_of_date_keeps_every_observers_link_working(participant, observer):  # noqa: F811
    """✨ The consent text changed and the participant has not agreed again: they are asked, but nobody is cut off."""
    link = issue_link(participant, "Jo")
    Consent.objects.update(text_version=current_text_version() - 1)

    claim(observer, link)
    sent = send(observer, complete_sort())

    assert sent.status_code < 400
    assert observer_assessments().assessments == [complete_sort()]


# Answer collection freezes (ticket 55)


def answered_by(participant, *names):
    """✨ Each named person, already on the list, claims a fresh link and sends; returns each one's browser, by name."""
    browsers = {}
    for name in names:
        browsers[name] = Client()
        claim(browsers[name], issue_link(participant, name))
        assert send(browsers[name], complete_sort()).status_code == 303
    return browsers


def press_compare(participant, confirmed=True):
    """✨ The participant's "Compare with how others see you →", and the confirmation's button if `confirmed`."""
    return participant.post(f"/results/{SORT}/comparison/visit/", {"confirmed": "yes"} if confirmed else {})


def freeze(participant):
    """✨ The participant sends their own sort and presses compare, confirming, as freezes collection with the minimum
    in."""
    participant.post("/sections/onboarding/complete/")
    submit_sort(participant, complete_sort())
    assert press_compare(participant).status_code == 303
    assert Response.objects.get().collection_frozen_at is not None


def add(participant, person):
    """✨ Post one new person to the list, as its empty row does, whether or not the page offers that row."""
    name, email = person
    version = Response.objects.get().version_id
    return participant.post("/contacts/contacts/", {"name": name, "email": email, "version": version})


@pytest.fixture
def three_answered(participant):
    """✨ Jo, Priya and Chris have each sent; Sam has claimed a link and not sent."""
    save_contacts(participant, CHRIS, SAM)
    browsers = answered_by(participant, "Jo", "Priya", "Chris")
    browsers["Sam"] = Client()
    claim(browsers["Sam"], issue_link(participant, "Sam"))
    return browsers


SAM = ("Sam", "sam@example.com")


@pytest.mark.django_db
def test_once_frozen_an_observers_send_is_refused_and_nothing_is_stored(participant, three_answered):
    freeze(participant)

    page = the_observers_page(three_answered["Sam"])
    refused = send(three_answered["Sam"], complete_sort())

    assert page.status_code == 200
    assert widget_data(page.content.decode()) is None
    assert refused.status_code == 409
    assert len(observer_assessments().assessments) == 3


@pytest.mark.django_db
def test_once_frozen_the_participant_can_neither_add_people_nor_issue_or_reissue_their_links_but_can_revoke(
    participant, three_answered
):
    freeze(participant)
    contacts_before = Contact.objects.count()
    links_before = set(Invitation.objects.values_list("token_hash", flat=True))
    page = participant.get("/invitations/", follow=True).content.decode()

    added = add(participant, ("Kim", "kim@example.com"))
    issued = participant.post(f"/invitations/{Contact.objects.get(name='Sam').pk}/issue/")
    reissued = participant.post(f"/invitations/{Contact.objects.get(name='Jo').pk}/issue/")

    assert added.status_code == 403 and issued.status_code == 403 and reissued.status_code == 403
    assert Contact.objects.count() == contacts_before
    assert set(Invitation.objects.values_list("token_hash", flat=True)) == links_before
    assert "Get link" not in page and "issue/" not in page
    revoked = participant.post(invitation_action(participant, "Sam", "revoke"))
    assert revoked.status_code == 303
    assert not Invitation.objects.filter(contact__name="Sam").exists()


@pytest.mark.django_db
@pytest.mark.parametrize("pressed", ["add", "issue"])
def test_once_frozen_without_javascript_adding_or_issuing_is_refused_on_the_lists_page(
    participant, three_answered, pressed
):
    """✨ The list's page again in the participant's frame, its own line saying why, never a bare status (ticket 71)."""
    freeze(participant)
    contacts_before = Contact.objects.count()
    links_before = set(Invitation.objects.values_list("token_hash", flat=True))

    if pressed == "add":
        refused = add(participant, ("Kim", "kim@example.com"))
    else:
        refused = participant.post(f"/invitations/{Contact.objects.get(name='Sam').pk}/issue/")

    page = refused.content.decode()
    assert refused.status_code == 403
    assert '<body class="framed">' in page
    assert 'class="question-card contact-list"' in page
    assert RESULTS_SEEN in text_of(page)
    assert Contact.objects.count() == contacts_before
    assert set(Invitation.objects.values_list("token_hash", flat=True)) == links_before


@pytest.mark.django_db
def test_once_frozen_with_htmx_adding_or_issuing_gets_the_short_status(participant, three_answered):
    freeze(participant)
    htmx = {"HTTP_HX_REQUEST": "true"}
    version = Response.objects.get().version_id

    kim = {"name": "Kim", "email": "kim@example.com", "version": version}
    added = participant.post("/contacts/contacts/", kim, **htmx)
    issued = participant.post(f"/invitations/{Contact.objects.get(name='Sam').pk}/issue/", **htmx)

    for refused in (added, issued):
        assert refused.status_code == 403
        assert text_of(refused.content.decode()) == f"Not saved. {RESULTS_SEEN}"


# ✨ The engine's wording for a list frozen (ticket 55), as the list's page and a refusal give it.
RESULTS_SEEN = "You've seen your results, so no more answers are added."


@pytest.mark.django_db
def test_once_frozen_the_coachs_link_can_still_be_issued_and_reissued(signed_in_client, load_pathway):  # noqa: F811
    """✨ Frozen as the press freezes it, in a pathway with a coach and no sort: the coach's link is no observer's."""
    load_pathway(with_a_coach_and_contacts())
    choose(signed_in_client)
    first = issue_coach_link(signed_in_client)
    Response.objects.update(collection_frozen_at=timezone.now())

    again = issue_coach_link(signed_in_client)

    assert again != first
    assert Invitation.live(token_of(again), role=Contact.Role.COACH) is not None


@pytest.mark.django_db
def test_a_withdrawal_after_the_freeze_deletes_the_answers_and_the_comparison_counts_without_them(
    participant, three_answered
):
    save_contacts(participant, ("Kim", "kim@example.com"))
    answered_by(participant, "Kim")
    freeze(participant)

    withdraw(three_answered["Jo"])

    assert len(observer_assessments().assessments) == 3
    assert send(three_answered["Sam"], complete_sort()).status_code == 409


@pytest.mark.django_db
def test_below_the_minimum_after_a_withdrawal_collection_unfreezes_until_the_next_confirmed_press(
    participant, three_answered
):
    freeze(participant)

    withdraw(three_answered["Jo"])

    assert len(observer_assessments().assessments) == 2
    assert "2 of 3" in participant.get(f"/results/{SORT}/comparison/").content.decode()
    assert send(three_answered["Sam"], complete_sort()).status_code == 303
    assert add(participant, ("Kim", "kim@example.com")).status_code == 303
    assert press_compare(participant, confirmed=False).status_code == 200
    assert Response.objects.get().collection_frozen_at is None
    assert press_compare(participant).status_code == 303
    assert Response.objects.get().collection_frozen_at is not None


@pytest.mark.django_db
def test_with_consent_withdrawn_and_collection_frozen_an_observers_link_gets_the_dead_link_refusal(
    participant, three_answered
):
    save_contacts(participant, ("Kim", "kim@example.com"))
    unclaimed = issue_link(participant, "Kim")
    freeze(participant)
    withdraw_consent(participant)

    for refused in (
        Client().get(unclaimed),
        the_observers_page(three_answered["Sam"]),
        send(three_answered["Sam"], complete_sort()),
    ):
        assert refused.status_code == 404
        assert refused.templates[0].name == "engine/link_refused.html"


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
