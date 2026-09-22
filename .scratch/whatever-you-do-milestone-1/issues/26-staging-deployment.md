# 26: Staging deployment

**What to build:** A private staging instance for the 9 Oct demo and the content owner's own use: Hetzner in an EU region, on an account owned by the content owner with the developer deploying into it, holding fake data only. Needs a human for account and access steps (the wizard skill fits).

**Blocked by:** 05 (Slice 1 content: baseline and calling-statement section)

**Status:** ready-for-human

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

This can start as soon as ticket 05 lands, so hosting surprises surface early.

- [ ] A Hetzner account owned by the content owner exists in an EU region, with deploy access granted to the developer
- [ ] The application runs there behind HTTPS at a private URL, configured entirely from the environment
- [ ] The database has backups and a restore has been tried once
- [ ] The instance holds fake data only, using reserved example domains; nothing real is ever loaded
- [ ] A short runbook records how the instance was stood up, so another deployment can be created the same way (ADR 0002)
- [ ] A smoke test passes on the deployed instance: sign up with the enrolment code, log in, complete a section, resume
- [ ] Open, and not decided by this ticket: who the controller is, retention and the data protection impact assessment (see spec Further Notes). Confirm the arrangement works for everyone involved before any real participant is added

**Carried from 03**

- [ ] Password reset stays hidden and refused on staging, since no email delivery exists; the runbook says how the operator resets a password (`manage.py changepassword`). Re-enabling reset is ticket 28
