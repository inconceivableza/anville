# 13c: The coach's link

**What to build:** The coach the participant chose in onboarding gets a link of the observer kind, asking them to accept or decline the six commitments from the coach-selection mock-up (its coach half; `Prototypes for reference/coach-selection-prototype.html`). Letting the coach see the results and comparison is ticket 27.

**Blocked by:** 13a (Issuing observer invitations)

**Status:** resolved

**Sprint:** 2a (ends 8 Oct, before FaithTech); carried from sprint 1

**Spec:** Implementation Decisions › Coach; Observers (ADR 0005); Testing Decisions

- [x] A participant with a chosen coach issues, copies, revokes and reissues the coach's link as for observers; saving another coach or removing this one revokes it
- [x] The coach sees the mock-up's invitation and the six commitments (first-person promises with their notes, authored in 10a) as tick-boxes; accepting needs every box ticked, and declining is always offered, worded as a good outcome
- [x] Only accepted or declined is stored, never which boxes were ticked; the coach has no account and writes nothing else
- [x] The participant is told accepted or declined, with no detail; after a decline they are offered to choose someone else (back to the coach checklist) and may still carry on without a coach
- [x] Wrong, expired and revoked coach links are refused

**Carried from 10a**

- The invitation names the participant; ticket 37 adds the display name it should use

## Answer

- The mock-up's "What happens next" on the coach's accepted page, and a pointer from the hub to the coach's answer: carried to 27
- Whether keeping an acceptance, which implies the coach's faith, is lawful: ADR 0010, and the spec's legal list
