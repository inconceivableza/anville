# 28a: Password reset

**What to build:** A participant who has forgotten their password resets it by email. The spec leaves this out of this milestone. Until then, sign-in offers no password reset (ticket 03 hid the link and refuses the reset pages, because they crashed without a mail server) and the operator resets a password with `manage.py changepassword`. Google sign-in, split from the same ticket 28, is 28b.

**Blocked by:** a decision outside this plan: an email provider, with a processor agreement

**Status:** needs-triage

**Sprint:** not yet placed

**Parent:** whatever-you-do-milestone-1 spec (Out of Scope: "Account-level features beyond sign-up and login: password reset, Google sign-in and a production identity provider"). After milestone 1; not in the cut order

- [ ] An email provider is chosen and a processor agreement is in place (spec Further Notes, "Legalities are parked, not forgotten")
- [ ] Email delivery is configured from the environment, as every other setting is (ADR 0002)
- [ ] Sign-in offers "Forgot your password?" again and the reset pages are reachable; remove the override that hides the link (`access/templates/account/password_reset_help_text.html`) and the refusal in `config/urls.py`
- [ ] The reset email never reveals whether an address has an account
- [ ] Replace the temporary journey test that asserts reset is neither offered nor reachable with tests of the working flow
