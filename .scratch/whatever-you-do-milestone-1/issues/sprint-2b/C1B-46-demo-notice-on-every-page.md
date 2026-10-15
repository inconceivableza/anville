# 46: The demo notice on every page

**What to build:** On a demo deployment every page says it is a demo. Ticket 26's notice (step 12a) is shown in full on the homepage and the account pages (sign up, sign in, consent). This adds the full notice to the hub and to the pages observers and coaches land on from their links, since they arrive without seeing the homepage and enter data too, and a smaller, less conspicuous one on every other page.

**Blocked by:** A1-49a (Hub layout and side cards)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Testing Decisions; Operating and demonstrating

- [ ] The full notice, as the homepage shows it, on the hub, the observer's landing page and the coach's page
- [ ] Every other page shows a smaller notice instead: a thin strip or a short line, plainly visible but not competing with the page's content. It says at least that this is a demo and to use made-up details. No page shows both
- [ ] Both are shown only when the deployment's demo notice is set, and neither when it is not. A production environment never sets it
- [ ] A new page gets the smaller notice without anyone remembering it: it is part of the shared page layout, which the pages with the full notice override
- [ ] The manual checks say the smaller notice is readable, at phone width too, and covers nothing the page needs

**Context**

- Builds on ticket 26's step 12a. Its spec point is Testing Decisions, "Fake data uses reserved example domains"
- Where things are: the full notice is `access/demo_notice.html`; the observer's landing page `engine/observer_landing.html`; the coach's page `engine/coach_link.html`; the shared layout `engine/base.html`, where the smaller notice is a block the full-notice pages replace. The setting is `ANVILLE_DEMO_NOTICE`, which the chart sets on staging environments only
- Journey tests: the full notice on the hub, the observer's landing page and the coach's page; the smaller one on a section page, the results and the observer's own page; neither anywhere with the setting unset
- Emails need nothing more: on staging every message already carries the `[TEST]` subject marker and the test-system disclaimer (`ANVILLE_EMAIL_DISCLAIMER`, ticket 26 step 18), fake email included
- The account layout (`access/templates/allauth/layouts/base.html`) already shows the full notice on every account page, the consent pages included, so it needs no change
- The smaller notice's wording may be a fixed short form, or the same `ANVILLE_DEMO_NOTICE` text set smaller; if it needs its own setting, the chart sets it beside `ANVILLE_DEMO_NOTICE` for staging environments only
