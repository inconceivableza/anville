# 13c: The coach's link

**What to build:** The coach the participant chose in onboarding gets a link of the observer kind, asking them to accept or decline the six commitments from the coach-selection mock-up (its coach half; `Prototypes for reference/coach-selection-prototype.html`). Letting the coach see shared sections is ticket 27.

**Blocked by:** 13a (Issuing observer invitations)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Spec:** Implementation Decisions › Coach; Observers (ADR 0005); Testing Decisions

- [ ] A participant with a chosen coach issues, copies, revokes and reissues the coach's link as for observers; saving another coach or removing this one revokes it
- [ ] The coach sees the mock-up's invitation and the six commitments (first-person promises with their notes, authored in 10a) as tick-boxes; accepting needs every box ticked, and declining is always offered, worded as a good outcome
- [ ] Only accepted or declined is stored, never which boxes were ticked; the coach has no account and writes nothing else
- [ ] The participant is told accepted or declined, with no detail; after a decline they are offered to choose someone else (back to the coach checklist) and may still carry on without a coach
- [ ] Wrong, expired and revoked coach links are refused

**Carried from 10a**

- The participant's name is not asked anywhere; the account holds only an email. If the invitation needs it, it belongs on the account, not in a block
