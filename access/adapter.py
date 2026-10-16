# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email, user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404

# ✨ The email is the username (ticket 37), so it can be no longer than the username column. allauth would otherwise cut
# a longer one short to fit, leaving a username that is not the email, and that a second long email could clash with.
USERNAME_MAX_LENGTH = get_user_model()._meta.get_field("username").max_length


class AccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        email = super().clean_email(email)
        if len(email) > USERNAME_MAX_LENGTH:
            raise forms.ValidationError(f"Use an email address of {USERNAME_MAX_LENGTH} characters or fewer.")
        return email

    def populate_username(self, request, user):
        """✨ A new account's username is its email address, in place of allauth's made-up one (ticket 37). Emails
        are unique, so the username is too; sign-in is still by email."""
        user_username(user, user_email(user))


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def list_apps(self, request, provider=None, client_id=None):
        """✨ Google's client comes only from the environment's pair (ticket 28b), read on each request, and never
        from the database: with half a pair or none, there is no app, so no button."""
        from allauth.socialaccount.models import SocialApp  # ✨ not at the top: models load after the app registry

        google_id, secret = settings.ANVILLE_GOOGLE_CLIENT_ID, settings.ANVILLE_GOOGLE_CLIENT_SECRET
        if not (google_id and secret) or provider not in (None, "google") or client_id not in (None, google_id):
            return []
        return [SocialApp(provider="google", name="Google", client_id=google_id, secret=secret)]

    def get_app(self, request, provider, client_id=None):
        """✨ Without the pair, the Google routes are not found, rather than failing for want of an app."""
        from allauth.socialaccount.models import SocialApp

        try:
            return super().get_app(request, provider, client_id=client_id)
        except SocialApp.DoesNotExist:
            raise Http404
