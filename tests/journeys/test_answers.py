import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from engine.models import Response
from tests.documents import pathway_document
from tests.journeys.test_access import PASSWORD
from tests.journeys.test_hub import a_fresh_participant


@pytest.fixture
def participant(django_user_model):
    return django_user_model.objects.create_user(
        username="participant", email="participant@example.com", password=PASSWORD
    )


@pytest.fixture
def signed_in(client, participant, load_pathway):
    load_pathway(pathway_document())
    client.force_login(participant)
    return client


def answer(client, block_id, value, *, page=None, **extra):
    """✨ Save an answer as the browser does, sending the pathway version of the page it was typed on."""
    page = page if page is not None else client.get("/").content.decode()
    shown = re.search(r'name="version" value="(\d+)"', page)
    form = {"value": value, **({"version": shown.group(1)} if shown else {}), **extra}
    return client.post(f"/answers/{block_id}/", form, HTTP_HX_REQUEST="true")


@pytest.mark.django_db
def test_an_answer_is_saved_on_its_own_and_acknowledged(signed_in):
    saved = answer(signed_in, "statement", "To build things that last.")

    assert saved.status_code == 200
    assert "Saved" in saved.content.decode()
    assert "To build things that last." in signed_in.get("/").content.decode()


@pytest.mark.django_db
def test_saving_one_answer_leaves_every_other_answer_untouched(signed_in):
    answer(signed_in, "statement", "First draft.")
    answer(signed_in, "baseline-bible", "4")

    answer(signed_in, "statement", "Second draft.")

    page = signed_in.get("/").content.decode()
    assert "Second draft." in page
    assert "First draft." not in page
    assert _chosen_point(page, "baseline-bible") == "4"


@pytest.mark.django_db
def test_an_answer_saved_from_a_stale_page_does_not_undo_another_saved_since(signed_in, participant):
    """✨ Two tabs open on the same response: each save changes only its own block."""
    other_tab = Client()
    other_tab.force_login(participant)
    answer(signed_in, "statement", "Written in the first tab.")

    answer(other_tab, "baseline-bible", "9")

    page = signed_in.get("/").content.decode()
    assert "Written in the first tab." in page
    assert _chosen_point(page, "baseline-bible") == "9"


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["0", "11", "seven", ""])
def test_an_agreement_scale_answer_outside_one_to_ten_is_refused_and_nothing_is_stored(signed_in, value):
    refused = answer(signed_in, "baseline-bible", value)

    assert refused.status_code == 400
    assert "Choose a number from 1 to 10." in refused.content.decode()
    assert _chosen_point(signed_in.get("/").content.decode(), "baseline-bible") is None


@pytest.mark.django_db
def test_a_refused_answer_keeps_the_answer_saved_before_it(signed_in):
    answer(signed_in, "baseline-bible", "6")

    answer(signed_in, "baseline-bible", "60")

    assert _chosen_point(signed_in.get("/").content.decode(), "baseline-bible") == "6"


@pytest.mark.django_db
def test_an_overlong_text_answer_is_refused(signed_in):
    refused = answer(signed_in, "statement", "x" * 20_001)

    assert refused.status_code == 400
    assert "This answer is too long to save." in refused.content.decode()


@pytest.mark.django_db
def test_a_long_text_box_tells_the_browser_the_length_the_server_accepts(signed_in):
    page = signed_in.get("/").content.decode()

    assert re.search(r'<textarea id="answer-statement"[^>]*maxlength="20000"', page)


@pytest.mark.django_db
@pytest.mark.parametrize("block_id", ["no-such-block", "welcome"])
def test_an_answer_to_a_block_that_takes_none_is_refused(signed_in, block_id):
    refused = answer(signed_in, block_id, "Anything")

    assert refused.status_code == 404
    assert "Anything" not in signed_in.get("/").content.decode()


@pytest.mark.django_db
def test_an_answer_cannot_be_saved_by_a_visitor_who_is_not_signed_in(client, load_pathway):
    load_pathway(pathway_document())

    refused = answer(client, "statement", "Anonymous words.")

    assert refused.status_code == 302
    assert refused.url.startswith("/accounts/login/")


@pytest.mark.django_db
def test_answers_are_saved_only_by_a_post(signed_in):
    assert signed_in.get("/answers/statement/").status_code == 405


@pytest.mark.django_db
def test_a_participant_signing_in_on_another_device_sees_every_earlier_answer(signed_in):
    answer(signed_in, "statement", "What I wrote on my laptop.")
    answer(signed_in, "baseline-bible", "8")

    phone = Client()
    phone.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD})
    page = phone.get("/").content.decode()

    assert "What I wrote on my laptop." in page
    assert _chosen_point(page, "baseline-bible") == "8"


@pytest.mark.django_db
def test_a_participant_never_sees_another_participants_answers(signed_in, client):
    answer(signed_in, "statement", "Private reflection.")

    page = a_fresh_participant(client, "other@example.com").get("/").content.decode()

    assert "Private reflection." not in page


@pytest.mark.django_db
def test_without_javascript_saving_returns_the_participant_to_the_pathway(signed_in):
    version = re.search(r'name="version" value="(\d+)"', signed_in.get("/").content.decode()).group(1)

    saved = signed_in.post("/answers/statement/", {"value": "Saved by pressing the button.", "version": version})

    assert saved.status_code == 303
    assert saved.url == "/#block-statement"


@pytest.mark.django_db
def test_a_participant_in_progress_stays_on_the_version_they_started(signed_in, client, load_pathway):
    answer(signed_in, "statement", "Started on the first version.")
    edited = pathway_document()
    edited["content"]["sections"][1]["blocks"][0]["prompt"] = "A prompt from the second version."
    load_pathway(edited)

    page = signed_in.get("/").content.decode()
    assert "Write your statement." in page
    assert "A prompt from the second version." not in page
    assert "Started on the first version." in page

    newcomer = a_fresh_participant(client, "newcomer@example.com").get("/").content.decode()
    assert "A prompt from the second version." in newcomer


@pytest.mark.django_db
def test_a_first_answer_is_recorded_against_the_version_the_participant_was_shown(signed_in, load_pathway):
    page_on_first_version = signed_in.get("/").content.decode()
    edited = pathway_document()
    edited["content"]["sections"][1]["blocks"][0]["prompt"] = "A prompt from the second version."
    load_pathway(edited)

    answer(signed_in, "statement", "Typed under the first prompt.", page=page_on_first_version)

    page = signed_in.get("/").content.decode()
    assert "Write your statement." in page
    assert "A prompt from the second version." not in page
    assert "Typed under the first prompt." in page


@pytest.mark.django_db
@pytest.mark.parametrize("version", ["999999", "not-a-number", None])
def test_a_first_answer_naming_no_published_version_is_refused(signed_in, participant, version):
    form = {"value": "Words.", **({"version": version} if version else {})}

    refused = signed_in.post("/answers/statement/", form, HTTP_HX_REQUEST="true")

    assert refused.status_code == 404
    assert not Response.objects.filter(participant=participant).exists()


@pytest.mark.django_db
def test_an_agreement_scale_shows_its_prompt_and_both_anchor_labels(signed_in):
    page = signed_in.get("/").content.decode()

    assert "I understand what the Bible teaches about work." in page
    assert "Strongly disagree" in page
    assert "Strongly agree" in page


@pytest.mark.django_db
def test_a_participant_cannot_answer_a_block_that_exists_only_in_a_later_version(signed_in, load_pathway):
    answer(signed_in, "statement", "Started on the first version.")
    later = pathway_document()
    later["content"]["sections"][1]["blocks"].append({"id": "later-only", "type": "long_text", "prompt": "New."})
    load_pathway(later)

    assert answer(signed_in, "later-only", "Too soon.").status_code == 404


@pytest.mark.django_db
def test_answering_with_no_pathway_published_is_refused(client, participant):
    client.force_login(participant)

    assert answer(client, "statement", "Nothing to answer.").status_code == 404


@pytest.mark.django_db
def test_a_response_is_marked_as_test_data_only_on_the_server_never_by_the_client(signed_in, participant):
    answer(signed_in, "statement", "Pretending to be seed data.", is_test_data="true", test_data="1")

    response = Response.objects.get(participant=participant)
    assert response.is_test_data is False
    assert set(response.answers) == {"statement"}


@pytest.mark.django_db
def test_deleting_an_account_deletes_its_responses(signed_in, participant):
    answer(signed_in, "statement", "Mine to take away.")

    get_user_model().objects.filter(pk=participant.pk).delete()

    assert not Response.objects.exists()


def _chosen_point(page, block_id):
    """✨ The point a participant sees chosen on an agreement scale, read from the rendered radio buttons."""
    match = re.search(rf'id="answer-{block_id}-(\d+)" name="value" value="\d+" checked', page)
    return match.group(1) if match else None
