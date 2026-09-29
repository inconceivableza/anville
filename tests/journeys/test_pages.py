"""✨ Pages within a section over HTTP (ticket 33): one after another with "Continue →", as the prototype's screens are.

Having moved past a page is stored, since a page with nothing it needs (the coach step, a contact list left empty)
would otherwise hold nobody back. As with locks and readings, every page is shut or open on the request itself, so
a typed address, an autosave or a coach checklist step reaches no further than the pages the participant has gone
through. Each page is a plain page with an address of its own, and going on is a plain form.
"""

import re
from html import unescape

import pytest

from tests.documents import pathway_document
from tests.journeys.pages import gate_checklist, version_on
from tests.journeys.test_coach_checklist import step, the_coach_checklist
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

FIRST = "/sections/onboarding/"
SECOND = "/sections/onboarding/pages/2/"
THIRD = "/sections/onboarding/pages/3/"
SAY_WHY = "Say why you are here to continue."
WHY_PROMPT = "Why are you here?"
STORY_PROMPT = "Tell us your story."
FAREWELL = "That is everything for now."


def paged_onboarding(second_page=None):
    """✨ The test pathway with onboarding split in three: a question the gate needs, a page nothing is needed on,
    and a last page to complete it from."""
    document = pathway_document()
    onboarding = document["content"]["sections"][0]
    onboarding["blocks"] = [
        *onboarding["blocks"],
        {"id": "why", "type": "long_text", "prompt": WHY_PROMPT},
        {"id": "to-2", "type": "page_break"},
        *(second_page or [{"id": "story", "type": "long_text", "prompt": STORY_PROMPT}]),
        {"id": "to-3", "type": "page_break"},
        {"id": "farewell", "type": "rich_text", "body": FAREWELL},
    ]
    onboarding["gate"] = {"clauses": [{"type": "has_answer", "block": "why", "message": SAY_WHY}]}
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(paged_onboarding())
    return signed_in_client


def shown(client, address=FIRST):
    return client.get(address).content.decode()


def save(client, block_id, value, htmx=True):
    """✨ Save an answer as its block does, naming the version the first page was rendered from."""
    form = {"value": value, "version": version_on(shown(client))}
    headers = {"HTTP_HX_REQUEST": "true"} if htmx else {}
    return client.post(f"/answers/{block_id}/", form, **headers)


def move_past(client, page):
    return client.post(f"/sections/onboarding/pages/{page}/continue/")


def through_to(client, page):
    """✨ Answer what the first page needs and move past each page in turn until `page` is reached."""
    save(client, "why", "To find out.")
    for number in range(1, page):
        move_past(client, number)
    return client


def way_on(page):
    """✨ The form at the foot of a page: where it goes, its button's words, and whether the button is disabled."""
    form = re.search(
        r'<div id="completion".*?<form method="post" action="([^"]+)">.*?<button([^>]*)>(.*?)</button>', page, re.S
    )
    return form.group(1), unescape(form.group(3)).strip(), " disabled" in form.group(2)


def back(page):
    """✨ Where a page's "← Back" leads, or None if it has none."""
    link = re.search(r'<a [^>]*href="([^"]+)"[^>]*>← Back</a>', page)
    return link.group(1) if link else None


# One page at a time


@pytest.mark.django_db
def test_the_first_page_shows_its_own_blocks_and_none_from_the_pages_after_it(participant):
    page = shown(participant)

    assert "Welcome to the pathway." in page
    assert WHY_PROMPT in page
    assert STORY_PROMPT not in page
    assert FAREWELL not in page


@pytest.mark.django_db
def test_each_page_but_the_last_ends_in_continue(participant):
    assert way_on(shown(participant)) == ("/sections/onboarding/pages/1/continue/", "Continue →", True)


@pytest.mark.django_db
def test_a_pages_unmet_clauses_are_listed_beneath_its_continue(participant):
    assert gate_checklist(shown(participant)) == {SAY_WHY: False}


@pytest.mark.django_db
def test_answering_what_the_page_needs_opens_its_continue_without_a_reload(participant):
    sent_back = save(participant, "why", "To find out.").content.decode()

    assert '<button type="submit" class="btn btn-primary btn-full">Continue →</button>' in sent_back


@pytest.mark.django_db
def test_going_on_leads_to_the_next_page_with_only_its_own_blocks(participant):
    save(participant, "why", "To find out.")

    response = move_past(participant, 1)

    assert (response.status_code, response.url) == (303, SECOND)
    page = shown(participant, SECOND)
    assert STORY_PROMPT in page
    assert WHY_PROMPT not in page


@pytest.mark.django_db
def test_without_javascript_a_saved_answer_leads_back_to_the_page_it_is_on(participant):
    """✨ Not to the section's first page, which is where the autosave's fallback led before there were pages."""
    through_to(participant, 2)

    response = save(participant, "story", "It began in a small town.", htmx=False)

    assert (response.status_code, response["Location"]) == (303, f"{SECOND}#block-story")


@pytest.mark.django_db
def test_a_page_nothing_is_needed_on_still_ends_in_continue_and_no_checklist(participant):
    page = shown(through_to(participant, 2), SECOND)

    assert way_on(page) == ("/sections/onboarding/pages/2/continue/", "Continue →", False)
    assert gate_checklist(page) == {}


@pytest.mark.django_db
def test_the_last_page_ends_in_the_sections_own_completion_button(participant):
    page = shown(through_to(participant, 3), THIRD)

    assert FAREWELL in page
    assert way_on(page) == ("/sections/onboarding/complete/", "Mark complete", False)


# Going on is checked on the server


@pytest.mark.django_db
def test_going_on_is_refused_while_the_pages_clauses_are_unmet_however_the_request_arrives(participant):
    refused = move_past(participant, 1)

    assert refused.status_code == 400
    assert "This page is not finished yet." in refused.content.decode()
    assert participant.get(SECOND).url == FIRST


@pytest.mark.django_db
def test_going_on_from_a_page_not_yet_reached_changes_nothing(participant):
    save(participant, "why", "To find out.")

    response = move_past(participant, 2)

    assert (response.status_code, response.url) == (303, FIRST)
    assert participant.get(SECOND).url == FIRST


@pytest.mark.django_db
def test_there_is_no_going_on_from_the_last_page(participant):
    through_to(participant, 3)

    assert move_past(participant, 3).status_code == 404


@pytest.mark.django_db
def test_completing_from_the_last_page_still_checks_the_whole_gate(participant):
    """✨ A participant who went back and took their answer away is refused, and told why where the button is."""
    through_to(participant, 3)
    save(participant, "why", "")

    refused = participant.post("/sections/onboarding/complete/")

    assert refused.status_code == 400
    assert gate_checklist(shown(participant, THIRD)) == {SAY_WHY: False}
    assert way_on(shown(participant, THIRD))[2] is True


# A page not reached is shut, whatever the address typed


@pytest.mark.django_db
def test_a_page_not_reached_leads_back_to_the_page_reached(participant):
    assert participant.get(THIRD).url == FIRST
    through_to(participant, 2)
    assert participant.get(THIRD).url == SECOND


@pytest.mark.django_db
def test_a_page_the_section_does_not_have_is_not_found(participant):
    assert participant.get("/sections/onboarding/pages/4/").status_code == 404
    assert participant.get("/sections/onboarding/pages/0/").status_code == 404


@pytest.mark.django_db
def test_a_page_with_nothing_needed_on_it_still_holds_the_pages_after_it_until_continue(participant):
    through_to(participant, 2)

    assert participant.get(THIRD).url == SECOND


@pytest.mark.django_db
def test_a_block_on_a_page_not_reached_cannot_be_answered(participant):
    assert save(participant, "story", "Written ahead.").status_code == 403


@pytest.mark.django_db
def test_a_coach_checklist_on_a_page_not_reached_cannot_be_stepped_through(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(paged_onboarding(second_page=[the_coach_checklist()]))
    save(signed_in_client, "why", "To find out.")

    assert step(signed_in_client, "questions", htmx=False).status_code == 403


@pytest.mark.django_db
def test_without_javascript_a_coach_checklist_step_returns_the_page_it_is_on(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(paged_onboarding(second_page=[the_coach_checklist()]))
    through_to(signed_in_client, 2)

    page = step(signed_in_client, "questions", htmx=False).content.decode()

    assert 'data-screen="questions"' in page
    assert WHY_PROMPT not in page
    assert way_on(page)[0] == "/sections/onboarding/pages/2/continue/"


@pytest.mark.django_db
def test_a_locked_sections_pages_stay_locked(participant):
    assert participant.get("/sections/calling/pages/1/").url == "/"


# Going back


@pytest.mark.django_db
def test_each_page_after_the_first_leads_back_to_the_one_before(participant):
    through_to(participant, 3)

    assert back(shown(participant)) is None
    assert back(shown(participant, SECOND)) == FIRST
    assert back(shown(participant, THIRD)) == SECOND


@pytest.mark.django_db
def test_an_earlier_page_can_be_answered_again_after_going_on(participant):
    through_to(participant, 2)

    assert save(participant, "why", "To find out more.").status_code == 200
    assert "To find out more." in shown(participant)


@pytest.mark.django_db
def test_going_back_keeps_the_pages_already_gone_through(participant):
    through_to(participant, 3)

    move_past(participant, 1)  # ✨ as from a tab left open on the first page

    assert participant.get(THIRD).status_code == 200


# The hub


@pytest.mark.django_db
def test_the_hub_shows_a_paged_section_once_and_leads_to_the_page_reached(participant):
    through_to(participant, 2)

    hub = shown(participant, "/")

    assert hub.count("Before we begin</a>") == 1
    assert f'href="{SECOND}"' in hub
    assert f'href="{FIRST}"' not in hub


@pytest.mark.django_db
def test_the_hub_leads_to_the_first_page_until_the_participant_goes_on(participant):
    assert f'href="{FIRST}"' in shown(participant, "/")
