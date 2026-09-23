import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from engine.models import Response
from tests.documents import pathway_document
from tests.journeys.pages import version_on
from tests.journeys.test_access import PASSWORD
from tests.journeys.test_hub import a_fresh_participant

# ✨ Where the blocks these tests use live. An answer is typed on its section's page, never on the hub.
CALLING, ONBOARDING = "calling", "onboarding"


@pytest.fixture
def participant(django_user_model):
    return django_user_model.objects.create_user(
        username="participant", email="participant@example.com", password=PASSWORD
    )


@pytest.fixture
def newly_signed_in(client, participant, load_pathway):
    """✨ A participant who has answered and completed nothing, so only the first section is open."""
    load_pathway(pathway_document())
    client.force_login(participant)
    return client


@pytest.fixture
def signed_in(newly_signed_in):
    """✨ The same participant with the calling section open, since it requires onboarding to be complete."""
    newly_signed_in.post(f"/sections/{ONBOARDING}/complete/")
    return newly_signed_in


def shown(client, section=CALLING):
    """✨ One section as the participant sees it."""
    return client.get(f"/sections/{section}/").content.decode()


def answer(client, block_id, value, *, section=CALLING, page=None, **extra):
    """✨ Save an answer as the browser does, sending the pathway version of the page it was typed on."""
    version = version_on(page if page is not None else shown(client, section))
    form = {"value": value, **({"version": version} if version else {}), **extra}
    return client.post(f"/answers/{block_id}/", form, HTTP_HX_REQUEST="true")


@pytest.mark.django_db
def test_an_answer_is_saved_on_its_own_and_acknowledged(signed_in):
    saved = answer(signed_in, "statement", "To build things that last.")

    assert saved.status_code == 200
    assert "Saved" in saved.content.decode()
    assert "To build things that last." in shown(signed_in)


@pytest.mark.django_db
def test_saving_one_answer_leaves_every_other_answer_untouched(signed_in):
    answer(signed_in, "statement", "First draft.")
    answer(signed_in, "baseline-bible", "4", section=ONBOARDING)

    answer(signed_in, "statement", "Second draft.")

    assert "Second draft." in shown(signed_in)
    assert "First draft." not in shown(signed_in)
    assert _chosen_point(shown(signed_in, ONBOARDING), "baseline-bible") == "4"


@pytest.mark.django_db
def test_an_answer_saved_from_a_stale_page_does_not_undo_another_saved_since(signed_in, participant):
    """✨ Two tabs open on the same response: each save changes only its own block."""
    other_tab = Client()
    other_tab.force_login(participant)
    answer(signed_in, "statement", "Written in the first tab.")

    answer(other_tab, "baseline-bible", "9", section=ONBOARDING)

    assert "Written in the first tab." in shown(signed_in)
    assert _chosen_point(shown(signed_in, ONBOARDING), "baseline-bible") == "9"


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["0", "11", "seven", ""])
def test_an_agreement_scale_answer_outside_one_to_ten_is_refused_and_nothing_is_stored(signed_in, value):
    refused = answer(signed_in, "baseline-bible", value, section=ONBOARDING)

    assert refused.status_code == 400
    assert "Choose a number from 1 to 10." in refused.content.decode()
    assert _chosen_point(shown(signed_in, ONBOARDING), "baseline-bible") is None


@pytest.mark.django_db
def test_a_refused_answer_keeps_the_answer_saved_before_it(signed_in):
    answer(signed_in, "baseline-bible", "6", section=ONBOARDING)

    answer(signed_in, "baseline-bible", "60", section=ONBOARDING)

    assert _chosen_point(shown(signed_in, ONBOARDING), "baseline-bible") == "6"


@pytest.mark.django_db
def test_an_overlong_text_answer_is_refused(signed_in):
    refused = answer(signed_in, "statement", "x" * 20_001)

    assert refused.status_code == 400
    assert "This answer is too long to save." in refused.content.decode()


@pytest.mark.django_db
def test_a_long_text_box_tells_the_browser_the_length_the_server_accepts(signed_in):
    assert re.search(r'<textarea id="answer-statement"[^>]*maxlength="20000"', shown(signed_in))


@pytest.mark.django_db
@pytest.mark.parametrize("block_id", ["no-such-block", "welcome"])
def test_an_answer_to_a_block_that_takes_none_is_refused(signed_in, block_id):
    refused = answer(signed_in, block_id, "Anything")

    assert refused.status_code == 404
    assert "Anything" not in shown(signed_in)


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
    answer(signed_in, "baseline-bible", "8", section=ONBOARDING)

    phone = Client()
    phone.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD})

    assert "What I wrote on my laptop." in shown(phone)
    assert _chosen_point(shown(phone, ONBOARDING), "baseline-bible") == "8"


@pytest.mark.django_db
def test_a_participant_never_sees_another_participants_answers(signed_in, client):
    answer(signed_in, "statement", "Private reflection.")

    other = a_fresh_participant(client, "other@example.com")
    other.post(f"/sections/{ONBOARDING}/complete/")

    assert "Private reflection." not in shown(other)


@pytest.mark.django_db
def test_without_javascript_saving_returns_the_participant_to_the_section_they_were_reading(signed_in):
    version = version_on(shown(signed_in))

    saved = signed_in.post("/answers/statement/", {"value": "Saved by pressing the button.", "version": version})

    assert saved.status_code == 303
    assert saved.url == f"/sections/{CALLING}/#block-statement"


@pytest.mark.django_db
def test_a_participant_in_progress_stays_on_the_version_they_started(signed_in, client, load_pathway):
    answer(signed_in, "statement", "Started on the first version.")
    edited = pathway_document()
    edited["content"]["sections"][1]["blocks"][0]["prompt"] = "A prompt from the second version."
    load_pathway(edited)

    page = shown(signed_in)
    assert "Write your statement." in page
    assert "A prompt from the second version." not in page
    assert "Started on the first version." in page

    newcomer = a_fresh_participant(client, "newcomer@example.com")
    newcomer.post(f"/sections/{ONBOARDING}/complete/")
    assert "A prompt from the second version." in shown(newcomer)


@pytest.mark.django_db
def test_a_first_answer_is_recorded_against_the_version_the_participant_was_shown(newly_signed_in, load_pathway):
    """✨ Answered in the first open section, because this participant has completed nothing yet."""
    page_on_first_version = shown(newly_signed_in, ONBOARDING)
    edited = pathway_document()
    edited["content"]["sections"][0]["blocks"][1]["prompt"] = "A prompt from the second version."
    load_pathway(edited)

    answer(newly_signed_in, "baseline-bible", "7", page=page_on_first_version)

    page = shown(newly_signed_in, ONBOARDING)
    assert "I understand what the Bible teaches about work." in page
    assert "A prompt from the second version." not in page
    assert _chosen_point(page, "baseline-bible") == "7"


@pytest.mark.django_db
@pytest.mark.parametrize("version", ["999999", "not-a-number", None])
def test_a_first_answer_naming_no_published_version_is_refused(newly_signed_in, participant, version):
    form = {"value": "7", **({"version": version} if version else {})}

    refused = newly_signed_in.post("/answers/baseline-bible/", form, HTTP_HX_REQUEST="true")

    assert refused.status_code == 404
    assert not Response.objects.filter(participant=participant).exists()


@pytest.mark.django_db
def test_an_agreement_scale_shows_its_prompt_and_both_anchor_labels(signed_in):
    page = shown(signed_in, ONBOARDING)

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
