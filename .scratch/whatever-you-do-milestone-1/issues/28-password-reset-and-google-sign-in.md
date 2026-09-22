# 28: Password reset and Google sign-in

**What to build:** Account features beyond sign-up and login, which the spec leaves out of this milestone: a participant who has forgotten their password resets it by email, and a participant may sign in with Google instead of a password. Until then, sign-in offers no password reset (ticket 03 hid the link and refuses the reset pages, because they crashed without a mail server) and the operator resets a password with `manage.py changepassword`.

**Blocked by:** decisions outside this plan: an email provider, with a processor agreement, for password reset; and whether Google may process sign-in data, for Google sign-in

**Status:** needs-triage

**Parent:** whatever-you-do-milestone-1 spec (Out of Scope: "Account-level features beyond sign-up and login: password reset, Google sign-in and a production identity provider"). After milestone 1; not in the cut order

**Password reset**

- [ ] An email provider is chosen and a processor agreement is in place (spec Further Notes, "Legalities are parked, not forgotten")
- [ ] Email delivery is configured from the environment, as every other setting is (ADR 0002)
- [ ] Sign-in offers "Forgot your password?" again and the reset pages are reachable; remove the override that hides the link (`access/templates/account/password_reset_help_text.html`) and the refusal in `config/urls.py`
- [ ] The reset email never reveals whether an address has an account
- [ ] Replace the temporary journey test that asserts reset is neither offered nor reachable with tests of the working flow

**Google sign-in**

- [ ] Decide, and record in an ADR, whether Google may process participants' sign-in data. The same GDPR concern kept fonts off Google's servers (ticket 03), and this is the first place a participant's identity would pass through a third party
- [ ] If it may, sign-in with Google is added through allauth's social accounts, alongside email and password, without changing the enrolment code requirement or the consent step (ADR 0004)
