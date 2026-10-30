# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The letter's closing ratings save quietly in *Whatever You Do* (sprint-3c-r3-fix-15), as its wizard's do: nothing
on a save, only a refusal's reason. The document asks for it (`ratings_save_quietly`); the faithful port does not, so
its ratings still say "Saved", and so does the letter itself."""

import pytest

from engine.models import Publication
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_whatever_you_do import participant, the_pathway, through_to_the_letter  # noqa: F401
from tests.journeys.test_whatever_you_do_faithful_port import A_LETTER
from tests.journeys.test_whatever_you_do_faithful_port import participant as port_participant  # noqa: F401
from tests.journeys.test_whatever_you_do_faithful_port import through_to_the_letter as through_to_the_ports_letter

HTMX = {"HX-Request": "true"}


def autosave(client, block_id, value):
    return client.post(
        f"/answers/{block_id}/", {"value": value, "version": Publication.current_version().pk}, headers=HTMX
    )


@pytest.mark.django_db
def test_a_closing_rating_answered_says_nothing_and_sends_back_only_its_gate(participant):  # noqa: F811
    saved = autosave(through_to_the_letter(participant), "pl-peace", "8")

    assert saved.status_code == 200
    assert saved.content.decode().startswith('<div id="gate-refusal"')


@pytest.mark.django_db
def test_a_refused_closing_rating_still_says_why(participant):  # noqa: F811
    refused = autosave(through_to_the_letter(participant), "pl-peace", "11")

    assert refused.status_code == 400
    assert "Not saved." in refused.content.decode()


@pytest.mark.django_db
def test_the_letter_itself_still_says_saved(participant):  # noqa: F811
    saved = autosave(through_to_the_letter(participant), "lt-message", A_LETTER)

    assert "Saved" in saved.content.decode()


@pytest.mark.django_db
def test_the_faithful_ports_closing_ratings_still_say_saved(port_participant):  # noqa: F811
    saved = autosave(through_to_the_ports_letter(port_participant), "pl-bible", "8")

    assert "Saved" in saved.content.decode()
