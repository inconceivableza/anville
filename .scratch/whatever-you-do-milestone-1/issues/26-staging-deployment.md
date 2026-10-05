# 26: Staging deployment

**What to build:** A private staging instance for the 9 Oct demo and the content owner's own use: Hetzner in an EU region, on an account owned by the content owner with the developer deploying into it, holding fake data only. Needs a human for account and access steps (the wizard skill fits).

**Blocked by:** 05 (Slice 1 content: baseline and calling-statement section)

**Status:** ready-for-human

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

This can start as soon as ticket 05 lands, so hosting surprises surface early.

- [ ] A Hetzner account owned by the content owner exists in an EU region, with deploy access granted to the developer
- [ ] The application runs there behind HTTPS at a private URL, configured entirely from the environment
- [ ] The database has backups and a restore has been tried once
- [ ] The instance holds fake data only, using reserved example domains; nothing real is ever loaded. Since sign-up is open (ticket 37), sign-up and the homepage say plainly that this is a demo, that visitors should use made-up details, and that data may be wiped
- [ ] A short runbook records how the instance was stood up, so another deployment can be created the same way (ADR 0002)
- [ ] The instance sends email from a temporary staging domain, so coach and observer links can be emailed on staging; a lasting email set-up for the real service is separate (2 Oct demo)
- [ ] A smoke test passes on the deployed instance: sign up (with the enrolment code if the deployment turns it on), log in, complete a section, resume
- [ ] Open, and not decided by this ticket: who the controller is, retention and the data protection impact assessment (see spec Further Notes). Confirm the arrangement works for everyone involved before any real participant is added

**Carried from 13b**

- [ ] Behind the TLS proxy, set `SECURE_PROXY_SSL_HEADER` so the observer cookie is marked Secure
- [ ] Observers' links carry their token or secret in the path: keep them out of the web server's access logs

**Carried from 37**

- [ ] The enrolment code is required unless the environment turns it off: staging's environment and the runbook turn it off, or nobody can sign up

**Carried from 03**

- [ ] Password reset stays hidden and refused on staging until ticket 28a, even once staging sends email; the runbook says how the operator resets a password (`manage.py changepassword`). Re-enabling reset is ticket 28a
