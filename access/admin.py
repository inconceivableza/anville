# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from allauth.account.adapter import get_adapter
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm


class AdminSignInForm(AdminAuthenticationForm):
    """✨ The admin's sign-in, with wrong passwords counted and refused as allauth's sign-in counts them.

    The admin stays at its own form, since the operator's account has a username and no email address
    (deploy/README.md) and so cannot use the site's sign-in. allauth's adapter checks the limit before the
    password, and gives back the attempt when the password is right.
    """

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if username is not None and password:
            self.user_cache = get_adapter(self.request).authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


admin.site.login_form = AdminSignInForm
