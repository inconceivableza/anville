"""✨ Locks, gates and completion over HTTP, which is the only place they count.

The prototype's locks were `display:none` on a div, so anything that navigated directly walked straight
past them (docs/prototype/02-sections.md). Here every one of them is decided by the server on the request.
"""

import json
import re

import pytest

from engine.models import Response
from tests.documents import complete_sort, pathway_document, scripture_reading, sort_pathway
from tests.journeys.pages import loads_the_built_stylesheet
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

CALLING = "/sections/calling/"
COMPLETE_CALLING = "/sections/calling/complete/"
ONBOARDING = "/sections/onboarding/"
LONG_ENOUGH = "A statement long enough to pass the gate."


@pytest.fixture
def open_calling(signed_in_client, load_pathway):  # noqa: F811
    """✨ A participant with the calling section open: its one requirement, onboarding, is complete."""

    def open_it(document=None):
        load_pathway(document or pathway_document())
        signed_in_client.post(COMPLETE_CALLING.replace("calling", "onboarding"))
        return signed_in_client

    return open_it


# Reaching a section at all


@pytest.mark.django_db
def test_a_participant_opens_a_section_from_the_hub(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    page = signed_in_client.get(ONBOARDING)

    assert page.status_code == 200
    assert "Before we begin" in page.content.decode()
    assert "Welcome to the pathway." in page.content.decode()


@pytest.mark.django_db
def test_a_section_page_loads_the_built_stylesheet(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    assert loads_the_built_stylesheet(signed_in_client.get(ONBOARDING).content.decode())


@pytest.mark.django_db
def test_a_section_the_pathway_does_not_have_is_not_found(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    assert signed_in_client.get("/sections/no-such-section/").status_code == 404


@pytest.mark.django_db
def test_an_anonymous_visitor_cannot_open_a_section(client, load_pathway):
    load_pathway(pathway_document())

    response = client.get(CALLING)

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={CALLING}"


# Locks, enforced on the request and not in the markup


@pytest.mark.django_db
def test_a_locked_section_stays_locked_when_its_address_is_typed_straight_in(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    response = signed_in_client.get(CALLING)

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_a_locked_sections_content_never_reaches_the_browser(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    hub = signed_in_client.get("/").content.decode()
    locked = signed_in_client.get(CALLING, follow=True).content.decode()

    assert "Write your statement." not in hub
    assert "Write your statement." not in locked


@pytest.mark.django_db
def test_a_block_in_a_locked_section_cannot_be_answered_either(signed_in_client, load_pathway):  # noqa: F811
    """✨ Otherwise a participant could fill a section in without opening it, and the lock would be decoration."""
    load_pathway(pathway_document())

    refused = signed_in_client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})

    assert refused.status_code == 403
    assert not Response.objects.exists()


@pytest.mark.django_db
def test_a_locked_section_cannot_be_completed(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    response = signed_in_client.post(COMPLETE_CALLING)

    assert response.status_code == 302
    assert response.url == "/"
    assert not Response.objects.exists()


@pytest.mark.django_db
def test_a_section_opens_once_the_section_it_requires_is_complete(open_calling):
    client = open_calling()

    assert client.get(CALLING).status_code == 200


# The gate, re-checked by the server when the section is completed


@pytest.mark.django_db
def test_a_section_whose_gate_does_not_pass_says_what_is_missing_and_offers_no_way_on(open_calling):
    page = open_calling().get(CALLING).content.decode()

    assert "Write a statement of at least ten characters." in page
    assert "<button type=\"submit\" class=\"btn btn-primary\" disabled>Mark complete</button>" in page


@pytest.mark.django_db
def test_completion_is_refused_when_the_gate_does_not_pass_however_the_request_arrives(open_calling):
    """✨ The button was disabled; a participant who re-enables it in their browser still gets nowhere."""
    client = open_calling()
    client.post("/answers/statement/", {"value": "too short", "version": _version_id()})

    response = client.post(COMPLETE_CALLING)

    assert response.status_code == 400
    assert "Write a statement of at least ten characters." in response.content.decode()
    assert "calling" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_a_participant_completes_a_section_once_its_gate_passes(open_calling):
    client = open_calling()
    client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})

    assert "Write a statement of at least ten characters." not in client.get(CALLING).content.decode()
    response = client.post(COMPLETE_CALLING)

    assert (response.status_code, response.url) == (303, "/")
    assert set(Response.objects.get().completed_sections) == {"onboarding", "calling"}


@pytest.mark.django_db
def test_completing_a_section_is_the_participants_own_act_and_never_follows_from_an_answer(open_calling):
    client = open_calling()

    client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})

    assert "calling" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_a_section_with_no_gate_can_be_completed_straight_away(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    response = signed_in_client.post("/sections/onboarding/complete/")

    assert (response.status_code, response.url) == (303, "/")
    assert list(Response.objects.get().completed_sections) == ["onboarding"]


@pytest.mark.django_db
def test_a_completed_section_still_shows_the_participants_answers_so_they_can_reread_them(open_calling):
    client = open_calling()
    client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})
    client.post(COMPLETE_CALLING)

    page = client.get(CALLING).content.decode()

    assert LONG_ENOUGH in page
    assert "You marked this section complete." in page


# The gate keeps up with what is being written, without a reload


def autosave(client, block_id, value):
    """✨ Save an answer the way the text box does, over htmx."""
    return client.post(
        f"/answers/{block_id}/", {"value": value, "version": _version_id()}, HTTP_HX_REQUEST="true"
    ).content.decode()


@pytest.mark.django_db
def test_writing_enough_opens_the_way_on_without_the_participant_reloading(open_calling):
    """✨ The gate is re-rendered beside the save, so the button follows what has just been written."""
    client = open_calling()

    sent_back = autosave(client, "statement", LONG_ENOUGH)

    assert 'hx-swap-oob="true"' in sent_back
    assert '<button type="submit" class="btn btn-primary">Mark complete</button>' in sent_back
    assert "Write a statement of at least ten characters." not in sent_back


@pytest.mark.django_db
def test_writing_too_little_sends_back_the_gate_message_and_no_way_on(open_calling):
    client = open_calling()

    sent_back = autosave(client, "statement", "too short")

    assert "Write a statement of at least ten characters." in sent_back
    assert '<button type="submit" class="btn btn-primary" disabled>Mark complete</button>' in sent_back


@pytest.mark.django_db
def test_an_autosave_still_says_the_answer_was_saved(open_calling):
    assert "Saved" in autosave(open_calling(), "statement", LONG_ENOUGH)


@pytest.mark.django_db
def test_a_refused_answer_leaves_the_gate_where_it_was(open_calling):
    """✨ Nothing was stored, so nothing about the section has changed and the refusal is all there is to say."""
    client = open_calling()

    sent_back = autosave(client, "statement", "x" * 20_001)

    assert "This answer is too long to save." in sent_back
    assert "hx-swap-oob" not in sent_back


@pytest.mark.django_db
def test_the_gate_keeps_up_with_an_answer_taken_back_again(open_calling):
    client = open_calling()
    autosave(client, "statement", LONG_ENOUGH)

    sent_back = autosave(client, "statement", "")

    assert "Write a statement of at least ten characters." in sent_back
    assert '<button type="submit" class="btn btn-primary" disabled>Mark complete</button>' in sent_back


# Reopening, the mirror of completing


@pytest.fixture
def completed_calling(open_calling):
    """✨ A participant who has completed both sections of the test pathway."""
    client = open_calling()
    client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})
    client.post(COMPLETE_CALLING)
    return client


@pytest.mark.django_db
def test_a_participant_reopens_a_section_they_marked_complete(completed_calling):
    response = completed_calling.post("/sections/calling/reopen/")

    assert (response.status_code, response.url) == (303, "/")
    assert "calling" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_a_reopened_section_keeps_every_answer_and_offers_the_way_on_again(completed_calling):
    completed_calling.post("/sections/calling/reopen/")

    page = completed_calling.get(CALLING).content.decode()

    assert LONG_ENOUGH in page
    assert "You marked this section complete." not in page
    assert "Mark complete" in page


@pytest.mark.django_db
def test_reopening_a_section_does_not_touch_any_other_sections_completion(completed_calling):
    completed_calling.post("/sections/onboarding/reopen/")

    assert set(Response.objects.get().completed_sections) == {"calling"}


@pytest.mark.django_db
def test_a_section_stays_reachable_when_the_section_it_required_is_reopened(completed_calling):
    """✨ The participant earned it, so reopening what came before never shuts it behind them."""
    completed_calling.post("/sections/onboarding/reopen/")

    assert completed_calling.get(CALLING).status_code == 200


@pytest.mark.django_db
def test_an_unfinished_section_locks_again_when_the_section_it_required_is_reopened(open_calling):
    client = open_calling()

    client.post("/sections/onboarding/reopen/")

    assert client.get(CALLING).status_code == 302


@pytest.mark.django_db
def test_reopening_a_section_that_was_never_complete_changes_nothing(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    response = signed_in_client.post("/sections/onboarding/reopen/")

    assert response.status_code == 303
    assert not Response.objects.exists()


@pytest.mark.django_db
def test_a_section_is_reopened_only_by_a_post(completed_calling):
    assert completed_calling.get("/sections/calling/reopen/").status_code == 405


# The hub, derived from all of it


@pytest.mark.django_db
def test_the_hub_lists_every_section_with_its_status_and_points_at_the_next_step(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    page = signed_in_client.get("/").content.decode()

    assert "Before we begin" in page
    assert "Putting your calling into words" in page
    assert "Your next step" in page
    assert "Not started" in page
    assert "Locked" in page


@pytest.mark.django_db
def test_the_hub_follows_the_participant_as_they_go(open_calling):
    client = open_calling()

    page = client.get("/").content.decode()

    assert "Complete" in page
    assert "Locked" not in page  # ✨ the calling section opened when onboarding was completed


@pytest.mark.django_db
def test_progress_counts_the_interactive_blocks_and_not_the_prose(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    assert "0 of 2 answered" in signed_in_client.get("/").content.decode()

    signed_in_client.post("/answers/baseline-bible/", {"value": "7", "version": _version_id()})

    assert "1 of 2 answered" in signed_in_client.get("/").content.decode()


# The scripture reading, which opens the activity beneath it


@pytest.fixture
def document_with_a_reading():
    document = pathway_document()
    document["content"]["sections"][1]["blocks"].insert(0, scripture_reading())
    return document


@pytest.mark.django_db
def test_the_activity_beneath_an_unconfirmed_reading_is_absent_from_the_page_not_hidden_in_it(
    open_calling, document_with_a_reading
):
    page = open_calling(document_with_a_reading).get(CALLING).content.decode()

    assert "There are different kinds of gifts." in page
    assert "I have read these" in page
    assert "Write your statement." not in page
    assert "Mark complete" not in page


@pytest.mark.django_db
def test_confirming_the_reading_opens_the_activity_beneath_it(open_calling, document_with_a_reading):
    client = open_calling(document_with_a_reading)

    client.post("/answers/reading/", {"value": "true", "version": _version_id()})

    page = client.get(CALLING).content.decode()
    assert "Write your statement." in page
    assert "There are different kinds of gifts." in page  # ✨ the passages stay, to be read again


@pytest.mark.django_db
def test_a_block_beneath_an_unconfirmed_reading_cannot_be_answered_either(open_calling, document_with_a_reading):
    """✨ Withholding it from the page is not enough: the activity must be unanswerable until it is opened."""
    client = open_calling(document_with_a_reading)

    refused = client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})

    assert refused.status_code == 403
    assert "statement" not in Response.objects.get().answers


@pytest.mark.django_db
def test_the_reading_itself_can_always_be_answered_since_it_is_what_opens_the_rest(
    open_calling, document_with_a_reading
):
    client = open_calling(document_with_a_reading)

    assert client.post("/answers/reading/", {"value": "true", "version": _version_id()}).status_code == 303
    assert client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()}).status_code == 303


@pytest.mark.django_db
def test_confirming_a_reading_sends_the_participant_back_to_its_own_section(open_calling, document_with_a_reading):
    client = open_calling(document_with_a_reading)

    response = client.post("/answers/reading/", {"value": "true", "version": _version_id()})

    assert (response.status_code, response.url) == (303, f"{CALLING}#block-reading")


# A link to another section


STRENGTHS_LINK = 'href="/sections/strengths/"'


def linking_to_the_sort():
    """✨ The sort pathway, with the calling section leading to the Strengths assessment before its statement."""
    document = sort_pathway()
    document["content"]["sections"][1]["blocks"].insert(
        0, {"id": "to-strengths", "type": "section_link", "section": "strengths", "body": "Sort your strengths."}
    )
    return document


@pytest.mark.django_db
def test_a_link_shows_the_section_it_leads_to_with_that_sections_status(open_calling):
    page = open_calling(linking_to_the_sort()).get(CALLING).content.decode()

    assert STRENGTHS_LINK in page
    assert "Strengths assessment" in page
    assert "Sort your strengths." in page
    assert "status-chip status-not-started" in page


@pytest.mark.django_db
def test_the_links_status_follows_the_participant_through_the_other_section(open_calling):
    client = open_calling(linking_to_the_sort())

    client.post("/answers/strengths-sort/", {"value": json.dumps(complete_sort()), "version": _version_id()})
    assert "status-chip status-in-progress" in client.get(CALLING).content.decode()

    client.post("/sections/strengths/complete/")
    assert "status-chip status-complete" in client.get(CALLING).content.decode()


@pytest.mark.django_db
def test_a_link_to_a_locked_section_names_it_but_does_not_lead_there(open_calling):
    document = linking_to_the_sort()
    document["content"]["sections"][2]["requires"] = ["calling"]

    page = open_calling(document).get(CALLING).content.decode()

    assert "Strengths assessment" in page
    assert "status-chip status-locked" in page
    assert STRENGTHS_LINK not in page


@pytest.mark.django_db
def test_a_link_counts_towards_no_progress(signed_in_client, load_pathway):  # noqa: F811
    """✨ It is a way to somewhere else, not something the participant answers: the rating, the statement and
    the sort are the three."""
    load_pathway(linking_to_the_sort())

    assert "0 of 3 answered" in signed_in_client.get("/").content.decode()


@pytest.mark.django_db
def test_a_link_takes_no_answer(open_calling):
    client = open_calling(linking_to_the_sort())

    client.post("/answers/to-strengths/", {"value": "true", "version": _version_id()})

    assert "to-strengths" not in Response.objects.get().answers


# Ghost text in a long text box


def with_a_placeholder(placeholder):
    document = pathway_document()
    document["content"]["sections"][1]["blocks"][0]["placeholder"] = placeholder
    return document


@pytest.mark.django_db
def test_a_long_text_box_shows_its_authored_placeholder(open_calling):
    page = open_calling(with_a_placeholder("Dear me,")).get(CALLING).content.decode()

    assert re.search(r'<textarea id="answer-statement"[^>]*placeholder="Dear me,"', page)


@pytest.mark.django_db
def test_a_placeholder_is_escaped_like_any_authored_text(open_calling):
    page = open_calling(with_a_placeholder('Say "hello" <b>now</b>')).get(CALLING).content.decode()

    assert 'placeholder="Say &quot;hello&quot; &lt;b&gt;now&lt;/b&gt;"' in page


@pytest.mark.django_db
def test_a_long_text_box_without_a_placeholder_has_none(open_calling):
    page = open_calling().get(CALLING).content.decode()

    assert "placeholder=" not in page


@pytest.mark.django_db
def test_a_placeholder_is_never_saved_as_the_answer(open_calling):
    """✨ It is a hint in the empty box, so the gate still asks for a statement."""
    client = open_calling(with_a_placeholder("A statement long enough to pass the gate by itself."))

    assert client.post(COMPLETE_CALLING).status_code == 400


def _version_id():
    from engine.models import Publication

    return Publication.current_version().pk
