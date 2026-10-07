"""✨ Pages within a section over HTTP (ticket 33): one after another with "Continue →", as the prototype's screens are.

Having moved past a page is stored, since a page with nothing it needs (the coach page, a contact list left empty)
would otherwise hold nobody back. As with locks and readings, every page is shut or open on the request itself, so
a typed address, an autosave or a coach checklist step reaches no further than the pages the participant has gone
through. Each page is a plain page with an address of its own, and going on is a plain form.
"""

import re
from html import unescape

import pytest

from engine.models import Response
from tests.documents import pathway_document, scripture_reading, sort_pathway, translated
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
    return move_past_in(client, "onboarding", page)


def move_past_in(client, section_id, page):
    return client.post(f"/sections/{section_id}/pages/{page}/continue/")


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


# A page that can be skipped

SKIP = "I'll do this later →"


def with_a_skip_label():
    """✨ The paged test pathway, with the second page's way on reading as a skip while nothing on it is answered."""
    document = paged_onboarding()
    onboarding = document["content"]["sections"][0]
    next(block for block in onboarding["blocks"] if block["id"] == "to-3")["skip_label"] = SKIP
    return document


@pytest.fixture
def skippable(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_skip_label())
    return signed_in_client


def way_on_look(page):
    """✨ How the way on at the foot of a page looks: "primary" or "secondary"."""
    button = re.search(r'<div id="completion".*?<button type="submit" class="btn btn-(\w+)', page, re.S)
    return button.group(1)


@pytest.mark.django_db
def test_a_page_with_nothing_answered_on_it_ends_in_its_breaks_skip_label(skippable):
    page = shown(through_to(skippable, 2), SECOND)

    assert way_on(page) == ("/sections/onboarding/pages/2/continue/", SKIP, False)
    assert way_on_look(page) == "secondary"


@pytest.mark.django_db
def test_a_skip_label_is_only_for_the_page_its_break_ends(skippable):
    page = shown(skippable)

    assert way_on(page)[1] == "Continue →"
    assert way_on_look(page) == "primary"


@pytest.mark.django_db
def test_once_anything_on_the_page_is_answered_it_ends_in_continue_again(skippable):
    through_to(skippable, 2)
    save(skippable, "story", "It began in a small town.")

    page = shown(skippable, SECOND)

    assert way_on(page)[1] == "Continue →"
    assert way_on_look(page) == "primary"


@pytest.mark.django_db
def test_the_way_on_follows_an_answer_given_and_taken_back_without_a_reload(skippable):
    through_to(skippable, 2)

    answered = unescape(save(skippable, "story", "It began in a small town.").content.decode())
    taken_back = unescape(save(skippable, "story", "").content.decode())

    assert '<button type="submit" class="btn btn-primary btn-full">Continue →</button>' in answered
    assert f'<button type="submit" class="btn btn-secondary btn-full">{SKIP}</button>' in taken_back


@pytest.mark.django_db
def test_skipping_goes_on_to_the_next_page(skippable):
    through_to(skippable, 2)

    assert move_past(skippable, 2).url == THIRD


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
def test_going_on_past_an_unconfirmed_reading_is_refused_though_the_page_needs_nothing_else(
    signed_in_client, load_pathway  # noqa: F811
):
    """✨ The page offers no "Continue →" beneath an unconfirmed reading; a request made by hand is refused too."""
    load_pathway(translated(paged_onboarding(second_page=[scripture_reading()])))
    through_to(signed_in_client, 2)

    refused = move_past(signed_in_client, 2)

    assert refused.status_code == 400
    assert 2 not in Response.objects.get().moved_past_by_section()["onboarding"]
    assert signed_in_client.get(THIRD).url == SECOND


@pytest.mark.django_db
def test_going_on_past_a_confirmed_reading_is_allowed(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(translated(paged_onboarding(second_page=[scripture_reading()])))
    through_to(signed_in_client, 2)
    save(signed_in_client, "reading", "true")

    assert move_past(signed_in_client, 2).url == THIRD


@pytest.mark.django_db
def test_going_on_past_a_link_still_holding_what_follows_is_refused(signed_in_client, load_pathway):  # noqa: F811
    """✨ Held until the linked section's gate passes, as an unconfirmed reading holds."""
    held = {"id": "to-calling", "type": "section_link", "section": "calling", "holds_what_follows": True}
    load_pathway(paged_onboarding(second_page=[held]))
    through_to(signed_in_client, 2)

    assert move_past(signed_in_client, 2).status_code == 400
    assert signed_in_client.get(THIRD).url == SECOND


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
def test_a_link_holding_the_participant_again_leads_them_back_to_its_own_page(
    signed_in_client, load_pathway  # noqa: F811
):
    """✨ Calling opens with a link held until onboarding's gate passes. Gone on past it, then onboarding's answer
    taken away: the page after the link is shut again, so its address leads to the link's page rather than to a page
    with nothing on it and no way on."""
    document = paged_onboarding()
    calling = document["content"]["sections"][1]
    calling["blocks"] = [
        {"id": "to-onboarding", "type": "section_link", "section": "onboarding", "holds_what_follows": True},
        {"id": "to-statement", "type": "page_break"},
        *calling["blocks"],
    ]
    load_pathway(document)
    through_to(signed_in_client, 3)
    signed_in_client.post("/sections/onboarding/complete/")
    assert signed_in_client.post("/sections/calling/pages/1/continue/").url == "/sections/calling/pages/2/"

    save(signed_in_client, "why", "")

    response = signed_in_client.get("/sections/calling/pages/2/")
    assert (response.status_code, response.get("Location")) == (302, "/sections/calling/")


def calling_held_over_three_pages():
    """✨ Calling opens with a link held until onboarding's gate passes, then its statement, then a last page."""
    document = paged_onboarding()
    calling = document["content"]["sections"][1]
    calling["blocks"] = [
        {"id": "to-onboarding", "type": "section_link", "section": "onboarding", "holds_what_follows": True},
        {"id": "to-statement", "type": "page_break"},
        *calling["blocks"],
        {"id": "to-close", "type": "page_break"},
        {"id": "close", "type": "rich_text", "body": "That is your statement written."},
    ]
    return document


def into_calling_page_2(client):
    """✨ Onboarding answered, gone through and completed, calling's first page moved past and its statement written."""
    through_to(client, 3)
    client.post("/sections/onboarding/complete/")
    client.post("/sections/calling/pages/1/continue/")
    save(client, "statement", "A statement long enough.")
    return client


@pytest.mark.django_db
def test_going_on_past_a_page_behind_a_link_holding_the_participant_again_is_refused(
    signed_in_client, load_pathway  # noqa: F811
):
    load_pathway(calling_held_over_three_pages())
    into_calling_page_2(signed_in_client)
    save(signed_in_client, "why", "")

    response = move_past_in(signed_in_client, "calling", 2)

    assert (response.status_code, response.url) == (303, "/sections/calling/")
    assert 2 not in Response.objects.get().moved_past_by_section()["calling"]


@pytest.mark.django_db
def test_completing_a_section_a_link_holds_again_leads_back_to_the_links_page(
    signed_in_client, load_pathway  # noqa: F811
):
    """✨ Though the last page had been reached and the section's own gate passes."""
    load_pathway(calling_held_over_three_pages())
    into_calling_page_2(signed_in_client)
    move_past_in(signed_in_client, "calling", 2)
    save(signed_in_client, "why", "")

    response = signed_in_client.post("/sections/calling/complete/")

    assert (response.status_code, response.url) == (303, "/sections/calling/")
    assert "calling" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_a_locked_sections_pages_stay_locked(participant):
    assert participant.get("/sections/calling/pages/1/").url == "/hub/"


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

    hub = shown(participant, "/hub/")

    assert hub.count("Before we begin</a>") == 1
    assert f'href="{SECOND}"' in hub
    assert f'href="{FIRST}"' not in hub


@pytest.mark.django_db
def test_the_hub_leads_to_the_first_page_until_the_participant_goes_on(participant):
    assert f'href="{FIRST}"' in shown(participant, "/hub/")


# Every other way to a section leads to the page reached, as the hub does


def calling_beside_part_way_onboarding():
    """✨ The paged onboarding, with calling open beside it (it requires nothing) and linking back to onboarding, so
    onboarding can be left part-way while calling is done."""
    document = paged_onboarding()
    calling = document["content"]["sections"][1]
    calling["requires"] = []
    calling["blocks"].insert(0, {"id": "to-onboarding", "type": "section_link", "section": "onboarding"})
    return document


@pytest.mark.django_db
def test_a_section_link_leads_to_the_page_reached_of_the_section_it_names(
    signed_in_client, load_pathway  # noqa: F811
):
    load_pathway(calling_beside_part_way_onboarding())
    through_to(signed_in_client, 2)

    assert f'<a href="{SECOND}">Before we begin</a>' in shown(signed_in_client, "/sections/calling/")


@pytest.mark.django_db
def test_completing_a_section_leads_on_to_the_page_reached_of_the_next(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(calling_beside_part_way_onboarding())
    through_to(signed_in_client, 2)
    save(signed_in_client, "statement", "A statement long enough.")

    response = signed_in_client.post("/sections/calling/complete/")

    assert (response.status_code, response.url) == (303, SECOND)


@pytest.mark.django_db
def test_before_a_sort_is_in_the_results_page_leads_to_the_page_the_sort_is_on(
    signed_in_client, load_pathway  # noqa: F811
):
    document = sort_pathway()
    strengths = document["content"]["sections"][-1]
    strengths["blocks"] = [
        {"id": "before-the-sort", "type": "rich_text", "body": "Sort these as they fit you."},
        {"id": "to-the-sort", "type": "page_break"},
        *strengths["blocks"],
    ]
    load_pathway(document)
    signed_in_client.post("/sections/onboarding/complete/")
    signed_in_client.post("/sections/strengths/pages/1/continue/")

    response = signed_in_client.get("/results/strengths-sort/")

    assert (response.status_code, response.url) == (302, "/sections/strengths/pages/2/")


# Progress and estimates are the section's, whatever its pages


@pytest.mark.django_db
def test_progress_counts_a_sections_blocks_wherever_they_sit(participant):
    """✨ The rating and "why" on the first page, the story on the second, and the calling statement."""
    assert "0 of 4 answered" in shown(participant, "/hub/")

    through_to(participant, 2)
    save(participant, "story", "It began in a small town.")

    assert "2 of 4 answered" in shown(participant, "/hub/")


@pytest.mark.django_db
def test_a_paged_sections_estimate_is_said_once_for_the_whole_section(signed_in_client, load_pathway):  # noqa: F811
    document = paged_onboarding()
    document["content"]["sections"][0]["estimate"] = "About 3 minutes"
    load_pathway(document)

    assert shown(signed_in_client, "/hub/").count("About 3 minutes") == 1
    assert "Whole section: About 3 minutes" in shown(signed_in_client)
