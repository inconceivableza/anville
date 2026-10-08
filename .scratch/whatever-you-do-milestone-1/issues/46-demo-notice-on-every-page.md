# 46: The demo notice on every page

**What to build:** On a demo deployment every page says it is a demo. Ticket 26's notice (step 12a) is shown in full on the homepage and the account pages (sign up, sign in, consent). This adds the full notice to the hub and to the pages observers and coaches land on from their links, since they arrive without seeing the homepage and enter data too, and a smaller, less conspicuous one on every other page.

**Blocked by:** None (can start immediately); builds on ticket 26's step 12a

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct) if it fits, since observers and coaches meet staging at FaithTech; otherwise 2b

**Spec:** Testing Decisions ("Fake data uses reserved example domains"); ticket 26

- [ ] The full notice, as the homepage shows it (`access/demo_notice.html`), on the hub, the observer's landing page (`engine/observer_landing.html`) and the coach's page (`engine/coach_link.html`)
- [ ] Every other page built on `engine/base.html` shows a smaller notice instead: a thin strip or a short line, plainly visible but not competing with the page's content. It says at least that this is a demo and to use made-up details. No page shows both
- [ ] Both are shown only when `ANVILLE_DEMO_NOTICE` is set, and neither when it is not. A production environment never sets it (the chart sets it on staging environments only)
- [ ] The smaller notice is a block in `engine/base.html` that the pages with the full notice replace, so a new page gets the smaller one without anyone remembering it
- [ ] Journey tests: the full notice on the hub, the observer's landing page and the coach's page; the smaller one on a section page, the results and the observer's own page; neither anywhere with the setting unset
- [ ] `docs/manual-checks.md`: the smaller notice is readable, at phone width too, and does not cover anything the page needs

**Context**

- Emails need nothing more: on staging every message already carries the `[TEST]` subject marker and the test-system disclaimer (`ANVILLE_EMAIL_DISCLAIMER`, ticket 26 step 18), fake email included
- The account layout (`access/templates/allauth/layouts/base.html`) already shows the full notice on every account page, the consent pages included, so it needs no change
- The smaller notice's wording may be a fixed short form, or the same `ANVILLE_DEMO_NOTICE` text set smaller; if it needs its own setting, the chart sets it beside `ANVILLE_DEMO_NOTICE` for staging environments only
