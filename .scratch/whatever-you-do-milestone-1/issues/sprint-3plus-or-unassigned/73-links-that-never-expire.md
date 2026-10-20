# 73: Observer and coach links that never expire

**What to build:** From the content owner's 20 Oct demo feedback: observer and coach links no longer run out after 30 days. Parked by the developer on 20 Oct, to be settled (with an ADR, under UK and EU data protection law) before it is built.

**Blocked by:** None (can start immediately)

**Status:** needs-triage

**Sprint:** 3 or later; parked 20 Oct

**Spec:** Observers (ADR 0005); Implementation Decisions › Coach

- [ ] Observer and coach links work until revoked, reissued or closed by withdrawn consent, with no end date
- [ ] Every place that relies on an end date is settled and changed to match (see below)
- [ ] The decision is recorded in an ADR

**To settle before this is ready**

- How long the coach can see the participant's results, once shared, with no end date
- How an observer withdraws once a link has stopped working (ADR 0007's open question; spec, Open content and product items)
- Weekly reminders need a cap if links never end; today the 30-day lifetime caps them at four (ADR 0016)
- The reminder email's "works until {until}" and the observers' privacy notice's "until your link runs out"
- The hub's and the comparison's "expired" coach state
- Ticket 64 counts a coach's acceptance after their link expires; with no expiry that distinction goes
