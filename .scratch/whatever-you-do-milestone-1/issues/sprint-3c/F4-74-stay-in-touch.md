# 74: "Stay in touch" on the homepage

**What to build:** A visitor can leave their email address in one "Stay in touch" field that serves the newsletter, contact and the churches' waitlist. The address is kept in the app, with nothing sent from it, and the operator sees and exports the list in the admin (ADR 0023). Wording is in the sprint 3c wording sheet's "Stay in touch".

**Blocked by:** 100 (A privacy page, with placeholders for what the content owner has to answer), F3

**Status:** ready-for-agent

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Sprint 3c: the content owner's feedback; Legalities are parked, not forgotten

- [ ] The homepage has "Stay in touch" as the wording sheet gives it: its heading and line, an email field labelled for screen readers, "Subscribe", and the line under the form linking to the privacy page
- [ ] Subscribing stores the address, the time and the version of the wording, and shows the thanks in place of the form, with no new page, with or without JavaScript; a repeat address gets the same thanks and stores nothing new
- [ ] A hidden field turns away bots, and an address that is not one is refused only after the press
- [ ] The admin lists the sign-ups and exports them as CSV
- [ ] "Join the waitlist" and the footer's "Contact us" lead to the form

**Context**

- Rewritten 26 Oct to ADR 0023, which replaces the rules it was parked with on 20 Oct
- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, "Stay in touch"
