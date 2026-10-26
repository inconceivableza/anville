# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email, user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404

from access.enrolment import asks_for_the_code
from access.models import DISPLAY_NAME_MAX_LENGTH, Account

# ✨ The email is the username (ticket 37), so it can be no longer than the username column. allauth would otherwise cut
# a longer one short to fit, leaving a username that is not the email, and that a second long email could clash with.
USERNAME_MAX_LENGTH = get_user_model()._meta.get_field("username").max_length

# ✨ Signing in leads to the hub and signing out to the homepage, and neither page shows messages, so allauth's
# "Successfully signed in as …" and "You have signed out." waited and showed on the next account page instead, such as
# sign-up. They are not added at all: landing on the hub, with "Sign out" in its header, says the sign-in worked, and
# landing on the homepage says the sign-out did.
UNSHOWN_MESSAGES = {"account/messages/logged_in.txt", "account/messages/logged_out.txt"}


class AccountAdapter(DefaultAccountAdapter):
    def add_message(self, request, level, message_template=None, message_context=None, extra_tags="", message=None):
        if message_template in UNSHOWN_MESSAGES:
            return
        super().add_message(request, level, message_template, message_context, extra_tags, message)

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
    # ✨ Nothing connects a Google account to an existing one, so in place of allauth's "sign in to that account first,
    # then connect", the refusal sends the person to sign in with their password (ticket 77). The Google sign-up form
    # links to signing in and the password reset beside it.
    error_messages = {
        **DefaultSocialAccountAdapter.error_messages,
        "email_taken": "There's already an account with this email address, made with a password. "
        "Sign in with your email and password instead.",
    }

    def validation_error(self, code, *args):
        # ✨ allauth hands its own refusal the provider's name to fill in, which ours does not take.
        if code == "email_taken":
            args = ()
        return super().validation_error(code, *args)

    def is_auto_signup_allowed(self, request, sociallogin):
        """✨ A Google sign-up makes the account at once, with no form (ADR 0021), except where the enrolment code is
        asked for, when the form asks for the code alone. An address too long to be a username goes to the form too,
        to be refused there as on the email-and-password form. allauth sends an address that already has an account
        to the form as well, to be refused (ticket 77)."""
        email = user_email(sociallogin.user) or ""
        return not asks_for_the_code(request) and len(email) <= USERNAME_MAX_LENGTH

    def save_user(self, request, sociallogin, form=None):
        """✨ Names the new account from Google (ADR 0021): its given name, else its full name, else the part of the
        email before the @, the fallback the spec already uses for an account without a name. The participant can
        change it on the entry page."""
        user = super().save_user(request, sociallogin, form=form)
        claims = sociallogin.account.extra_data
        name = (claims.get("given_name") or "").strip() or (claims.get("name") or "").strip()
        name = name or user.email.partition("@")[0]
        Account.objects.create(participant=user, display_name=name[:DISPLAY_NAME_MAX_LENGTH])
        return user

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
