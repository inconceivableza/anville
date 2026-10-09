# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email, user_username
from django import forms
from django.contrib.auth import get_user_model

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
