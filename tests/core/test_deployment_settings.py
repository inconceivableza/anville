# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ How the settings a deployed environment needs are read from the environment (docs/server-approach.md).

Settings are read once, when Django starts, so each case here starts a fresh Python with the environment it describes.
A developer's own .env is left out, so that what is unset here really is unset.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = {
    "DJANGO_SECRET_KEY": "not-a-real-key",
    "DATABASE_URL": "postgres://anville:anville@localhost:5432/anville",
}

READ_SETTINGS = """
import json, sys
import environ
environ.Env.read_env = classmethod(lambda *args, **kwargs: None)
from config import settings
print(json.dumps({name: getattr(settings, name, None) for name in sys.argv[1:]}, default=str))
"""


def settings_with(environment, *names):
    """✨ The named settings, as Django would have them when started with only this environment."""
    read = subprocess.run(
        [sys.executable, "-c", READ_SETTINGS, *names],
        cwd=ROOT,
        env={**REQUIRED, **environment},
        capture_output=True,
        text=True,
    )
    assert read.returncode == 0, read.stderr
    return json.loads(read.stdout)


def test_with_nothing_set_no_forwarded_header_is_trusted_and_https_is_not_insisted_on():
    settings = settings_with(
        {},
        "SECURE_PROXY_SSL_HEADER",
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SECURE_HSTS_SECONDS",
        "CSRF_TRUSTED_ORIGINS",
    )

    assert settings == {
        "SECURE_PROXY_SSL_HEADER": None,
        "SECURE_SSL_REDIRECT": None,
        "SESSION_COOKIE_SECURE": None,
        "CSRF_COOKIE_SECURE": None,
        "SECURE_HSTS_SECONDS": None,
        "CSRF_TRUSTED_ORIGINS": [],
    }


def test_django_https_trusts_the_proxy_and_insists_on_https_except_for_the_health_check():
    settings = settings_with(
        {"DJANGO_HTTPS": "true", "DJANGO_HSTS_SECONDS": "3600"},
        "SECURE_PROXY_SSL_HEADER",
        "SECURE_SSL_REDIRECT",
        "SECURE_REDIRECT_EXEMPT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SECURE_HSTS_SECONDS",
    )

    assert settings == {
        "SECURE_PROXY_SSL_HEADER": ["HTTP_X_FORWARDED_PROTO", "https"],
        "SECURE_SSL_REDIRECT": True,
        "SECURE_REDIRECT_EXEMPT": ["^healthz$"],
        "SESSION_COOKIE_SECURE": True,
        "CSRF_COOKIE_SECURE": True,
        "SECURE_HSTS_SECONDS": 3600,
    }


def test_trusted_origins_are_a_list_from_the_environment():
    settings = settings_with({"DJANGO_CSRF_TRUSTED_ORIGINS": "https://a.example,https://b.example"}, "CSRF_TRUSTED_ORIGINS")

    assert settings["CSRF_TRUSTED_ORIGINS"] == ["https://a.example", "https://b.example"]


def test_with_no_email_url_email_is_fake():
    settings = settings_with({}, "EMAIL_BACKEND", "DEFAULT_FROM_EMAIL")

    assert settings["EMAIL_BACKEND"] == "django.core.mail.backends.console.EmailBackend"
    assert settings["DEFAULT_FROM_EMAIL"] == "webmaster@localhost"


def test_an_empty_email_url_counts_as_unset():
    settings = settings_with({"EMAIL_URL": ""}, "EMAIL_BACKEND")

    assert settings["EMAIL_BACKEND"] == "django.core.mail.backends.console.EmailBackend"


def test_an_email_url_names_the_provider_and_its_credentials():
    settings = settings_with(
        {"EMAIL_URL": "smtp+tls://api-key:secret-key@in-v3.mailjet.com:587", "DEFAULT_FROM_EMAIL": "Anville <hello@example.org>"},
        "EMAIL_BACKEND",
        "EMAIL_HOST",
        "EMAIL_PORT",
        "EMAIL_USE_TLS",
        "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD",
        "DEFAULT_FROM_EMAIL",
    )

    assert settings == {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "in-v3.mailjet.com",
        "EMAIL_PORT": 587,
        "EMAIL_USE_TLS": True,
        "EMAIL_HOST_USER": "api-key",
        "EMAIL_HOST_PASSWORD": "secret-key",
        "DEFAULT_FROM_EMAIL": "Anville <hello@example.org>",
    }


def test_a_disclaimer_wraps_whichever_email_backend_was_chosen():
    fake = settings_with({"ANVILLE_EMAIL_DISCLAIMER": "From a test system."}, "EMAIL_BACKEND", "ANVILLE_DISCLAIMED_EMAIL_BACKEND")
    real = settings_with(
        {"ANVILLE_EMAIL_DISCLAIMER": "From a test system.", "EMAIL_URL": "smtp+tls://key:secret@smtp.example.org:587"},
        "EMAIL_BACKEND",
        "ANVILLE_DISCLAIMED_EMAIL_BACKEND",
    )

    assert fake == {
        "EMAIL_BACKEND": "config.email.DisclaimerBackend",
        "ANVILLE_DISCLAIMED_EMAIL_BACKEND": "django.core.mail.backends.console.EmailBackend",
    }
    assert real == {
        "EMAIL_BACKEND": "config.email.DisclaimerBackend",
        "ANVILLE_DISCLAIMED_EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    }


def test_with_no_disclaimer_the_email_backend_is_not_wrapped():
    settings = settings_with({"ANVILLE_EMAIL_DISCLAIMER": ""}, "EMAIL_BACKEND", "ANVILLE_DISCLAIMED_EMAIL_BACKEND")

    assert settings == {
        "EMAIL_BACKEND": "django.core.mail.backends.console.EmailBackend",
        "ANVILLE_DISCLAIMED_EMAIL_BACKEND": None,
    }


def test_the_demo_notice_is_empty_unless_the_environment_gives_one():
    assert settings_with({}, "ANVILLE_DEMO_NOTICE")["ANVILLE_DEMO_NOTICE"] == ""
    assert settings_with({"ANVILLE_DEMO_NOTICE": "A demo."}, "ANVILLE_DEMO_NOTICE")["ANVILLE_DEMO_NOTICE"] == "A demo."


def test_database_connections_are_closed_after_each_request_unless_an_age_is_given():
    assert settings_with({}, "DATABASES")["DATABASES"]["default"]["CONN_MAX_AGE"] == 0
    kept = settings_with({"DATABASE_CONN_MAX_AGE": "60"}, "DATABASES")["DATABASES"]["default"]
    assert kept["CONN_MAX_AGE"] == 60
    assert kept["CONN_HEALTH_CHECKS"] is True


def test_the_commit_is_unknown_unless_the_image_names_it():
    assert settings_with({}, "ANVILLE_COMMIT")["ANVILLE_COMMIT"] == "unknown"
    assert settings_with({"ANVILLE_COMMIT": "0123abc"}, "ANVILLE_COMMIT")["ANVILLE_COMMIT"] == "0123abc"


def test_only_the_files_vite_names_by_their_content_are_cached_for_good():
    immutable = re.compile(settings_with({}, "WHITENOISE_IMMUTABLE_FILE_TEST")["WHITENOISE_IMMUTABLE_FILE_TEST"])
    built = [path.name for path in (ROOT / "frontend" / "dist" / "assets").iterdir()]

    assert built
    assert all(immutable.match(f"/static/assets/{name}") for name in built)
    assert not immutable.match("/static/admin/css/base.css")
    assert not immutable.match("/static/manifest.json")
