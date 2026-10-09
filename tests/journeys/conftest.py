# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import json
from io import StringIO

import pytest
from django.core.cache import cache
from django.core.management import call_command


@pytest.fixture(autouse=True)
def fresh_rate_limits():
    """✨ allauth counts sign-ups and sign-ins per address in the cache (20 sign-ups a minute), and the cache
    outlives each test's database. Without this, a test's sign-up is refused once earlier tests have used
    up the minute's allowance, and it fails only when run with the others."""
    cache.clear()


@pytest.fixture(autouse=True)
def static_files_found_only_when_asked_for(settings):
    """✨ WhiteNoise indexes everything collectstatic gathered each time Django's request handling is built, which is
    once for every test client. With a staticfiles/ directory left by trying the deployed set-up, that made the suite
    four times slower. This is WhiteNoise's development mode, which looks a file up only when it is requested."""
    settings.WHITENOISE_AUTOREFRESH = True


@pytest.fixture
def load_pathway(tmp_path):
    """✨ Write a pathway document to a file and load it the way an author does; returns the command's output."""

    def load(document, *, name="pathway.json", indent=None):
        path = tmp_path / name
        path.write_text(json.dumps(document, indent=indent))
        out = StringIO()
        call_command("load_pathway", str(path), stdout=out)
        return out.getvalue()

    return load
