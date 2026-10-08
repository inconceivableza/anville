"""✨ Locks, gates and completion over HTTP, which is the only place they count.

The prototype's locks were `display:none` on a div, so anything that navigated directly walked straight
past them (docs/prototype/02-sections.md). Here every one of them is decided by the server on the request.
"""

import json
import re

import pytest

from engine.models import Response
from tests.documents import complete_sort, pathway_document, scripture_reading, sort_pathway, translated
from tests.journeys.pages import gate_checklist, loads_the_built_stylesheet, main_of
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_results import in_order

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
    assert response.url == "/hub/"


@pytest.mark.django_db
def test_a_locked_sections_content_never_reaches_the_browser(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    hub = signed_in_client.get("/hub/").content.decode()
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
    assert response.url == "/hub/"
    assert not Response.objects.exists()


@pytest.mark.django_db
def test_a_section_opens_once_the_section_it_requires_is_complete(open_calling):
    client = open_calling()

    assert client.get(CALLING).status_code == 200


# The gate, re-checked by the server when the section is completed


@pytest.mark.django_db
def test_a_section_whose_gate_does_not_pass_says_what_is_missing_and_offers_no_way_on(open_calling):
    page = open_calling().get(CALLING).content.decode()

    assert gate_checklist(page) == {"Write a statement of at least ten characters.": False}
    assert "<button type=\"submit\" class=\"btn btn-primary btn-full\" disabled>Mark complete</button>" in page


@pytest.mark.django_db
def test_what_the_gate_says_comes_after_the_button_so_the_button_stays_put_as_it_changes(open_calling):
    """✨ The messages come and go with each autosave; above the button, they pushed it up and down."""
    client = open_calling()

    refused = client.post(COMPLETE_CALLING).content.decode()

    assert in_order(
        refused,
        "Mark complete</button>",
        "Write a statement of at least ten characters.",
        "This section was not marked complete",
    )


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

    shown = gate_checklist(client.get(CALLING).content.decode())
    assert shown == {"Write a statement of at least ten characters.": True}
    response = client.post(COMPLETE_CALLING)

    assert response.status_code == 303
    assert set(Response.objects.get().completed_sections) == {"onboarding", "calling"}


@pytest.mark.django_db
def test_completing_a_section_onboarding_included_leads_back_to_the_hub(signed_in_client, load_pathway):  # noqa: F811
    """✨ As the prototype's `completePillar` goes to the hub, which points at the next step (ticket 41b)."""
    load_pathway(pathway_document())

    response = signed_in_client.post("/sections/onboarding/complete/")

    assert (response.status_code, response.url) == (303, "/hub/")


@pytest.mark.django_db
def test_completing_the_last_section_leads_back_to_the_hub(open_calling):
    client = open_calling()
    client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})

    response = client.post(COMPLETE_CALLING)

    assert (response.status_code, response.url) == (303, "/hub/")


@pytest.mark.django_db
def test_a_section_may_word_its_button_its_own_way(signed_in_client, load_pathway):  # noqa: F811
    """✨ Onboarding's is the prototype's "Continue →"; a section that says nothing keeps "Mark complete"."""
    document = pathway_document()
    document["content"]["sections"][0]["complete_label"] = "Continue →"
    load_pathway(document)

    onboarding = signed_in_client.get(ONBOARDING).content.decode()

    assert '<button type="submit" class="btn btn-primary btn-full">Continue →</button>' in onboarding
    assert "Mark complete" not in onboarding
    signed_in_client.post("/sections/onboarding/complete/")
    assert "Mark complete</button>" in signed_in_client.get(CALLING).content.decode()


@pytest.mark.django_db
def test_completing_a_section_is_the_participants_own_act_and_never_follows_from_an_answer(open_calling):
    client = open_calling()

    client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})

    assert "calling" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_a_section_with_no_gate_can_be_completed_straight_away(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    response = signed_in_client.post("/sections/onboarding/complete/")

    assert response.status_code == 303
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
    assert '<button type="submit" class="btn btn-primary btn-full">Mark complete</button>' in sent_back
    assert gate_checklist(sent_back) == {"Write a statement of at least ten characters.": True}


@pytest.mark.django_db
def test_a_met_requirement_stays_listed_so_the_page_keeps_its_height_and_says_it_is_done(open_calling):
    """✨ A message that vanished shortened the page, and a participant scrolled to the bottom saw it all jump.
    The tick is decoration, so a screen reader is told in words."""
    sent_back = autosave(open_calling(), "statement", LONG_ENOUGH)

    met = re.search(r'<li class="gate-item is-met">(.*?)</li>', sent_back, re.S).group(1)
    assert '<span class="gate-mark" aria-hidden="true">✓</span>' in met
    assert '<span class="visually-hidden">Done:</span>' in met


@pytest.mark.django_db
def test_writing_too_little_sends_back_the_gate_message_and_no_way_on(open_calling):
    client = open_calling()

    sent_back = autosave(client, "statement", "too short")

    assert gate_checklist(sent_back) == {"Write a statement of at least ten characters.": False}
    assert '<button type="submit" class="btn btn-primary btn-full" disabled>Mark complete</button>' in sent_back


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
    assert '<button type="submit" class="btn btn-primary btn-full" disabled>Mark complete</button>' in sent_back


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

    assert (response.status_code, response.url) == (303, "/hub/")
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

    page = signed_in_client.get("/hub/").content.decode()

    assert "Before we begin" in page
    assert "Putting your calling into words" in page
    assert "Your next step" in page
    assert "Not started" in page
    assert "Locked" in page


@pytest.mark.django_db
def test_the_hub_follows_the_participant_as_they_go(open_calling):
    client = open_calling()

    page = client.get("/hub/").content.decode()

    assert "Complete" in page
    assert "Locked" not in page  # ✨ the calling section opened when onboarding was completed


@pytest.mark.django_db
def test_progress_counts_the_interactive_blocks_and_not_the_prose(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(pathway_document())

    assert "0 of 2 answered" in signed_in_client.get("/hub/").content.decode()

    signed_in_client.post("/answers/baseline-bible/", {"value": "7", "version": _version_id()})

    assert "1 of 2 answered" in signed_in_client.get("/hub/").content.decode()


# The scripture reading, which opens the activity beneath it


@pytest.fixture
def document_with_a_reading():
    document = translated(pathway_document())
    document["content"]["sections"][1]["blocks"].insert(0, scripture_reading())
    return document


@pytest.mark.django_db
def test_a_passage_names_its_translation_beside_its_reference_only_when_it_is_not_the_documents(
    open_calling, document_with_a_reading
):
    """✨ The credits page says the document's translation is the one used unless otherwise indicated."""
    reading = document_with_a_reading["content"]["sections"][1]["blocks"][0]
    reading["passages"].append({"reference": "Colossians 3:23", "text": "Whatever you do.", "translation": "NIV"})

    page = open_calling(document_with_a_reading).get(CALLING).content.decode()

    assert "Colossians 3:23 (NIV)" in page
    assert "(ESV)" not in page


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
def test_confirming_a_reading_lands_at_its_confirmation_with_the_activity_it_opened_beneath(
    open_calling, document_with_a_reading
):
    """✨ Not back at the reading's top, above the passages just read (ticket 41e)."""
    client = open_calling(document_with_a_reading)

    response = client.post("/answers/reading/", {"value": "true", "version": _version_id()})

    assert (response.status_code, response.url) == (303, f"{CALLING}#block-reading-confirmed")
    assert 'id="block-reading-confirmed"' in client.get(CALLING).content.decode()


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

    assert "0 of 3 answered" in signed_in_client.get("/hub/").content.decode()


@pytest.mark.django_db
def test_a_link_takes_no_answer(open_calling):
    client = open_calling(linking_to_the_sort())

    client.post("/answers/to-strengths/", {"value": "true", "version": _version_id()})

    assert "to-strengths" not in Response.objects.get().answers


def holding_the_statement_for_the_sort():
    """✨ The calling section's statement waits, as Section 1's reflection does, until the sort is in."""
    document = linking_to_the_sort()
    document["content"]["sections"][1]["blocks"][0]["holds_what_follows"] = True
    return document


@pytest.mark.django_db
def test_a_link_can_hold_the_rest_of_its_section_until_the_linked_sections_gate_passes(open_calling):
    client = open_calling(holding_the_statement_for_the_sort())

    page = client.get(CALLING).content.decode()
    assert STRENGTHS_LINK in page
    assert "Write your statement." not in page
    assert "Mark complete" not in page

    client.post("/answers/strengths-sort/", {"value": json.dumps(complete_sort()), "version": _version_id()})
    assert "Write your statement." in client.get(CALLING).content.decode()


@pytest.mark.django_db
def test_a_block_held_by_a_link_cannot_be_answered_either(open_calling):
    """✨ Held back from the page and from the answer endpoint alike, as beneath an unconfirmed reading."""
    client = open_calling(holding_the_statement_for_the_sort())

    refused = client.post("/answers/statement/", {"value": LONG_ENOUGH, "version": _version_id()})

    assert refused.status_code == 403
    assert "statement" not in Response.objects.get().answers


def with_a_button(label="Open Strengths Assessment →"):
    document = linking_to_the_sort()
    document["content"]["sections"][1]["blocks"][0]["button_label"] = label
    return document


@pytest.mark.django_db
def test_a_link_with_a_button_label_leads_there_by_that_button(open_calling):
    page = open_calling(with_a_button()).get(CALLING).content.decode()

    assert re.search(r'href="/sections/strengths/"[^>]*>\s*Open Strengths Assessment →\s*</a>', page)
    assert main_of(page).count(STRENGTHS_LINK) == 1  # ✨ the button is the way there, so the title is not a second one
    assert "Strengths assessment" in page
    assert "status-chip status-not-started" in page


@pytest.mark.django_db
def test_a_button_label_is_escaped_like_any_authored_text(open_calling):
    page = open_calling(with_a_button("Open <b>now</b>")).get(CALLING).content.decode()

    assert "Open &lt;b&gt;now&lt;/b&gt;" in page


@pytest.mark.django_db
def test_a_link_to_a_locked_section_offers_no_button(open_calling):
    document = with_a_button()
    document["content"]["sections"][2]["requires"] = ["calling"]

    page = open_calling(document).get(CALLING).content.decode()

    assert "Strengths assessment" in page
    assert "Open Strengths Assessment →" not in page
    assert STRENGTHS_LINK not in page


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


# Time estimates


def with_estimates(section=None, block=None):
    """✨ The test pathway with an estimate on the calling section, on onboarding's rating, or both."""
    document = pathway_document()
    onboarding, calling = document["content"]["sections"]
    if section:
        calling["estimate"] = section
    if block:
        onboarding["blocks"][1]["estimate"] = block
    return document


@pytest.mark.django_db
def test_a_section_shows_its_time_estimate_at_the_top_as_the_whole_sections(open_calling):
    """✨ Said in so many words, since an activity's own estimate may sit just beneath it (the letter's does)."""
    page = open_calling(with_estimates(section="About 15 minutes")).get(CALLING).content.decode()

    heading = "<h1>Putting your calling into words</h1>"
    assert in_order(page, heading, "Whole section:", "About 15 minutes", "Write your statement.")


@pytest.mark.django_db
def test_a_sections_time_estimate_is_gone_once_something_in_it_is_answered(open_calling):
    """✨ It says how long the section will take, which no longer holds once the participant has begun."""
    client = open_calling(with_estimates(section="About 15 minutes"))
    client.post("/answers/statement/", {"value": "Begun", "version": _version_id()})

    assert "About 15 minutes" not in client.get(CALLING).content.decode()


@pytest.mark.django_db
def test_a_block_shows_its_time_estimate_just_above_it(signed_in_client, load_pathway):  # noqa: F811
    """✨ Where a section has several activities, each one's first block carries its own."""
    load_pathway(with_estimates(block="About 2 minutes"))

    page = signed_in_client.get(ONBOARDING).content.decode()

    rating = "I understand what the Bible teaches about work."
    assert in_order(page, "Welcome to the pathway.", "This part:", "About 2 minutes", rating)


@pytest.mark.django_db
def test_a_time_estimate_is_in_the_participants_wording(open_calling):
    estimate = {"participant": "About 15 minutes", "observer": "About 5 minutes to read"}

    page = open_calling(with_estimates(section=estimate)).get(CALLING).content.decode()

    assert "About 15 minutes" in page
    assert "About 5 minutes to read" not in page


@pytest.mark.django_db
def test_a_section_without_time_estimates_shows_none(open_calling):
    page = open_calling().get(CALLING).content.decode()

    assert "time-estimate" not in page


def _version_id():
    from engine.models import Publication

    return Publication.current_version().pk
