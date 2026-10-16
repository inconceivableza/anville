# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Rotating the secret key (ticket 47b, deploy/README.md): the old key moves to the fallbacks, so whatever was
signed with it, the participant's session and the cookie that shows a link just issued, still holds.
tests/core/test_deployment_settings.py covers how the fallbacks are read from the environment.
"""

import re

import pytest

from tests.journeys.test_contact_list import (  # noqa: F401  (participant is a fixture, used by name)
    JO,
    participant,
    save_contacts,
    with_a_contact_list,
)
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import invitation_action

A_NEW_KEY = "a-new-key-for-the-rotation-test"
ISSUED_LINK = re.compile(r"http://testserver/observe/[A-Za-z0-9_-]+/")


@pytest.mark.django_db
def test_with_the_old_key_among_the_fallbacks_the_participant_stays_signed_in_and_sees_the_link_just_issued(
    participant, settings
):
    save_contacts(participant, JO)
    old_key = settings.SECRET_KEY
    participant.post(invitation_action(participant, "Jo", "issue"))

    settings.SECRET_KEY = A_NEW_KEY
    settings.SECRET_KEY_FALLBACKS = [old_key]
    page = participant.get("/invitations/", follow=True)

    assert page.status_code == 200
    assert ISSUED_LINK.search(page.content.decode())


@pytest.mark.django_db
def test_once_the_old_key_is_removed_what_it_signed_no_longer_holds(participant, settings):
    settings.SECRET_KEY = A_NEW_KEY
    settings.SECRET_KEY_FALLBACKS = []

    page = participant.get("/invitations/")

    assert page.status_code == 302
    assert "/accounts/login/" in page["Location"]
