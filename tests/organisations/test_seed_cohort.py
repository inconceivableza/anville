"""✨ `seed_cohort` gives a developer Example Church, an Autumn cohort of twelve fake members spread across the pathway,
and an organisation admin to sign in as, all marked as test data.
"""

from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from organisations.models import Organisation

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"


def seed():
    out = StringIO()
    call_command("seed_cohort", stdout=out)
    return out.getvalue()


@pytest.fixture
def published():
    call_command("load_pathway", str(DOCUMENT), stdout=StringIO())


@pytest.mark.django_db
def test_it_refuses_unless_debug_is_on_and_creates_nothing(published, settings):
    settings.DEBUG = False

    with pytest.raises(CommandError, match="DEBUG"):
        seed()

    assert not Organisation.objects.exists()
    assert not get_user_model().objects.exists()


@pytest.mark.django_db
def test_it_refuses_without_a_published_pathway(settings):
    settings.DEBUG = True

    with pytest.raises(CommandError, match="No pathway is published"):
        seed()

    assert not Organisation.objects.exists()
