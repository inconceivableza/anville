# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ An observer who puts every card in "Haven't seen this" has declined (ticket 120; the developer, 17 Nov, from the
hand check of ticket 108: "if they choose not to give any answers other than Haven't seen this it should be equivalent
to that observer declining to answer the questionnaire").

The sort asks first (`frontend/src/sort.js`, checked by hand). Sent, only the decline is kept, apart from who sent it
as answers are, and the observer is thanked and never reminded again. The participant is told how many declined,
naming nobody, as withdrawals are told, and waits on them no longer: the freeze warning counts them as replied, and
Five trusted voices' card has all in once the answers and the declines reach everyone with a link."""

import importlib

import pytest
from django.apps import apps
from django.test import Client
from django.utils.html import escape

from engine.document.blocks import FREEZE_WARNINGS, SENT_ALREADY
from engine.models import Contact, ObserverResponse, Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_contact_list import CHRIS, VOICES, save_contacts, with_trusted_voices
from tests.journeys.test_havent_seen_this import A_CARD_NOT_SEEN, NOTHING_SEEN, offering_it, participant  # noqa: F401
from tests.journeys.test_hub import DEE, PEOPLE, add_people_with_links, answer_through, meters, tag_of, voices_card
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import issue_link
from tests.journeys.test_observer_assessment import SAM, answered_by, press_compare, send, withdraw
from tests.journeys.test_observer_landing import claim, the_observers_page
from tests.journeys.test_observer_responses import an_observer
from tests.journeys.test_results import SORT, submit_sort, widget_data
from tests.journeys.test_retake import deleted_list

THANKS = "We've kept only that you couldn't answer for"


def declines(participant, name):
    """✨ The named person, already on the list, claims a fresh link and sends with every card in "Haven't seen this";
    returns their browser and their own link."""
    browser = Client()
    own_link = claim(browser, issue_link(participant, name))
    assert send(browser, NOTHING_SEEN, relationship="friend").status_code == 303
    return browser, own_link


def the_decline():
    return ObserverResponse.objects.get(declined_at__isnull=False)


@pytest.mark.django_db
def test_a_send_with_nothing_seen_keeps_only_that_the_observer_declined(participant):  # noqa: F811
    declines(participant, "Jo")

    decline = the_decline()
    assert (decline.assessment, decline.relationship, decline.submitted_at) == (None, None, None)
    assert not ObserverResponse.objects.filter(submitted_at__isnull=False).exists()
    assert ObserverResponse.declined(Response.objects.get()) == 1


@pytest.mark.django_db
def test_an_observer_who_declined_is_never_reminded_again(participant):  # noqa: F811
    declines(participant, "Jo")

    assert Contact.objects.get(name="Jo").sent_at is not None


@pytest.mark.django_db
def test_an_observer_who_declined_is_thanked_for_it_offered_no_withdrawal_and_cannot_send_again(
    participant,  # noqa: F811
):
    """✨ Nothing about the participant was kept, so there is nothing to withdraw, as a coach's decline has none."""
    jo, _ = declines(participant, "Jo")

    page = the_observers_page(jo).content.decode()

    assert THANKS in page
    assert "Withdraw my answers" not in page and "data-sort" not in page
    assert "Bookmark this link" not in page  # ✨ there is nothing to come back for
    again = send(jo, complete_sort())
    assert again.status_code == 409 and escape(SENT_ALREADY) in again.content.decode()


@pytest.mark.django_db
def test_an_observer_who_sent_a_card_seen_has_answered_not_declined(participant):  # noqa: F811
    browser = Client()
    claim(browser, issue_link(participant, "Jo"))
    send(browser, A_CARD_NOT_SEEN)

    page = the_observers_page(browser).content.decode()

    assert THANKS not in page and "Withdraw my answers" in page and "Bookmark this link" in page
    assert ObserverResponse.declined(Response.objects.get()) == 0


@pytest.mark.django_db
def test_the_observers_sort_says_what_sending_nothing_seen_means_naming_the_participant(participant):  # noqa: F811
    browser = Client()
    claim(browser, issue_link(participant, "Jo"))

    wording = widget_data(the_observers_page(browser).content.decode())["wording"]

    assert "we’ll keep only that you couldn’t answer" in wording["nothing_seen"]
    assert "{name}" not in wording["nothing_seen"]
    assert wording["decline_label"] == "Send that I couldn’t answer →"


@pytest.mark.django_db
def test_the_freeze_warning_counts_a_decline_as_a_reply_so_waits_on_nobody_who_declined(participant):  # noqa: F811
    """✨ Before ticket 120 Jo was among "anyone who hasn't answered yet", though she had sent."""
    save_contacts(participant, CHRIS, SAM)
    declines(participant, "Jo")
    answered_by(participant, "Priya", "Chris", "Sam")
    submit_sort(participant, complete_sort())

    assert escape(FREEZE_WARNINGS["everyone"]) in press_compare(participant, confirmed=False).content.decode()

    save_contacts(participant, ("Kim", "kim@example.com"))
    some = FREEZE_WARNINGS["some"].format(replied=4, invited=5)
    assert escape(some) in press_compare(participant, confirmed=False).content.decode()


@pytest.fixture
def voices(signed_in_client, load_pathway):  # noqa: F811
    """✨ A participant past Before we begin, with Five trusted voices beside the hub, whose observers are offered
    "Haven't seen this"."""
    load_pathway(offering_it(with_trusted_voices(sort_pathway())))
    signed_in_client.post("/sections/onboarding/complete/")
    return signed_in_client


def decline_through(link):
    observer = Client()
    claim(observer, link)
    assert send(observer, NOTHING_SEEN).status_code == 303


@pytest.mark.django_db
@pytest.mark.parametrize(
    "declining, said",
    [(1, "1 person replied that they couldn’t answer."), (2, "2 people replied that they couldn’t answer.")],
)
def test_how_many_declined_is_said_on_the_list_page_and_beside_the_cards_answered_count(voices, declining, said):
    links = add_people_with_links(voices, *PEOPLE)
    answer_through(links[2])
    for link in links[:declining]:
        decline_through(link)

    card = voices_card(voices)
    assert f'<small class="meter-note"> · {declining} couldn’t answer</small>' in card
    assert meters(card) == {"Invited": 3, "Answered": 1}
    assert f'<p class="contact-withdrawn">{said}</p>' in voices.get(f"/sections/{VOICES}/").content.decode()


@pytest.mark.django_db
def test_with_a_decline_the_voices_card_has_all_answers_once_the_rest_have_answered(voices):
    """✨ Before ticket 120 it read "Enough answers received", as if Jo might still answer."""
    links = add_people_with_links(voices, *PEOPLE, DEE)
    decline_through(links[0])
    answer_through(*links[1:])

    assert tag_of(voices_card(voices)) == "All answers received"


@pytest.mark.django_db
@pytest.mark.parametrize("declining", [2, 3])
def test_once_all_have_replied_with_too_few_answers_the_voices_card_says_how_many_more_are_needed(voices, declining):
    """✨ Nobody else will answer, so as many more people are needed as answers still are (code review of 23 Nov: with 2
    declined and 1 answered it said "Some answers received" for good, and with all 3 declined "Links issued")."""
    links = add_people_with_links(voices, *PEOPLE)
    for link in links[:declining]:
        decline_through(link)
    answer_through(*links[declining:])

    card = voices_card(voices)

    assert tag_of(card) == f"{declining} more needed"
    assert '<span class="tag status-waiting' in card
    assert escape("You'll see how others see you once 3 people have answered.") in card


@pytest.mark.django_db
def test_while_someone_with_a_link_may_still_answer_the_voices_card_waits_on_them_whatever_others_declined(voices):
    links = add_people_with_links(voices, *PEOPLE, DEE)
    for link in links[:2]:
        decline_through(link)
    answer_through(links[2])

    assert tag_of(voices_card(voices)) == "Some answers received"


@pytest.mark.django_db
def test_a_retake_deletes_the_decline_so_the_observer_is_asked_again(participant):  # noqa: F811
    """✨ As it deletes what observers sent (29 Oct): they can send afresh, and are reminded as before they sent."""
    jo, _ = declines(participant, "Jo")
    submit_sort(participant, complete_sort())

    assert participant.post(f"/results/{SORT}/retake/").status_code == 303

    assert not ObserverResponse.objects.exists()
    assert Contact.objects.get(name="Jo").sent_at is None
    assert "data-sort" in the_observers_page(jo).content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "answering, said",
    [
        ((), "What the people you invited sent (1 reply that they couldn’t answer)."),
        (("Priya",), "What the people you invited sent (1 answer and 1 reply that they couldn’t answer)."),
    ],
)
def test_the_retake_page_counts_a_decline_among_what_it_deletes(participant, answering, said):  # noqa: F811
    """✨ The retake deletes the decline, and that person is asked again, so it says so, as of the answers (code review
    of 23 Nov: with only declines in, it warned of nothing)."""
    declines(participant, "Jo")
    answered_by(participant, *answering)
    submit_sort(participant, complete_sort())

    deletes = deleted_list(participant.get(f"/results/{SORT}/retake/").content.decode())

    assert [item for item in deletes if item.startswith("What the people")] == [
        f"{said} Their links still work, so they can answer again."
    ]


@pytest.mark.django_db
def test_a_decline_reached_through_the_withdrawal_page_goes_without_counting_as_answers_withdrawn(
    participant,  # noqa: F811
):
    jo, own_link = declines(participant, "Jo")

    assert withdraw(jo, own_link).status_code == 200

    assert not ObserverResponse.objects.exists()
    assert Response.objects.get().observers_withdrew == 0


@pytest.mark.django_db
def test_the_migration_turns_a_send_already_made_with_nothing_seen_into_a_decline(participant):  # noqa: F811
    """✨ As the hand check of ticket 108 left Quin's: stored as an assessment, and counted for nothing."""
    response = Response.objects.get()
    saw_nothing = an_observer(response, NOTHING_SEEN)
    saw_some = an_observer(response, A_CARD_NOT_SEEN)
    migration = importlib.import_module("engine.migrations.0032_observerresponse_declined_at")

    migration.keep_only_the_declines(apps, None)

    declined, answered = ObserverResponse.objects.get(pk=saw_nothing.pk), ObserverResponse.objects.get(pk=saw_some.pk)
    assert (declined.assessment, declined.submitted_at, declined.declined_at) == (None, None, saw_nothing.submitted_at)
    assert (answered.assessment, answered.declined_at) == (A_CARD_NOT_SEEN, None)
