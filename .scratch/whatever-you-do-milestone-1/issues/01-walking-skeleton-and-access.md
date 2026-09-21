# 01: Walking skeleton and access

**What to build:** A deployable Django and PostgreSQL application, with HTMX and a Vite build for focused JavaScript modules, in which a participant can sign up (with a shared enrolment code), log in and out, and see an intentional empty state because no pathway exists yet. This is the prefactoring ticket: it also wires up both test seams so every later ticket lands with tests from the first line.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Parent:** whatever-you-do-milestone-1 spec (Demo 1, 25 Sept)

- [x] Sign-up requires a valid enrolment code; a wrong or missing code is refused with a clear message
- [x] Email-and-password sign-up and login work through `django-allauth`, with email verification off (fake-data phase); logout works
- [x] A signed-in participant with no published pathway sees an intentional empty state, never a broken page
- [x] All configuration (secrets, database, enrolment code, allowed hosts) comes from the environment; nothing is hardcoded to *Whatever You Do*
- [x] The Django ORM is the only ORM and migration system (ADR 0001); there is no organisation model or column (ADR 0002)
- [x] The Vite build produces one trivial JavaScript module that a page loads, proving the pipeline for the widget tickets
- [x] Seam 1 is wired: a journey test uses Django's test client against real PostgreSQL (no database mocking) and passes
- [x] Seam 2 is wired: a pure-core test runs without a browser or a database and passes
- [x] Output is escaped on render; user text is never altered on input
