# 28b: Google sign-in

**What to build:** A participant may sign in with Google instead of a password, alongside email and password. The spec leaves this out of this milestone. Split from ticket 28; password reset is 28a.

**Blocked by:** a decision outside this plan: whether Google may process participants' sign-in data

**Status:** needs-triage

**Sprint:** 3 or later

**Parent:** whatever-you-do-milestone-1 spec (Out of Scope: "Account-level features beyond sign-up and login: password reset, Google sign-in and a production identity provider"). After milestone 1; not in the cut order

- [ ] Decide, and record in an ADR, whether Google may process participants' sign-in data. The same GDPR concern kept fonts off Google's servers (ticket 03), and this is the first place a participant's identity would pass through a third party
- [ ] If it may, sign-in with Google is added through allauth's social accounts, alongside email and password, without changing the enrolment code setting (ticket 37) or the consent step (ADR 0004)

**Carried from 08**

- [ ] Google sign-up asks for the 18+ confirmation, and for the enrolment code when the deployment turns it on (ticket 37). Both are fields of the sign-up form (`access/forms.py`), and allauth's social sign-up form is built on that same class, but by default allauth skips the form altogether (`SOCIALACCOUNT_AUTO_SIGNUP = True`). Turn that off, or otherwise make social sign-up show the form, and add journey tests that a Google sign-up without the code or the confirmation gets no account
- The consent step holds for a Google account either way: it guards the engine's views (`access/consent.py`), not sign-up
