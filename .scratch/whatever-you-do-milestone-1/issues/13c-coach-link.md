# 13c: The coach's link

**What to build:** The coach the participant chose in onboarding (ticket 10a) gets a link of the same kind as an observer's, which asks them to accept or decline the six commitments from the content owner's mock-up. Letting the coach see shared sections is ticket 27. Split from ticket 13.

**See also:** `Prototypes for reference/coach-selection-prototype.html`, the content owner's mock-up of choosing a coach. Its participant half is ticket 10a; its coach half is built here.

**Blocked by:** 13a (Issuing observer invitations), 13b (The observer's landing page and claiming the link)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] A participant who chose a coach in onboarding issues the coach's link, copies it and sends it themselves, with the same token approach, lifetime, revocation and reissue as observers (13a)
- [ ] Following the link, the coach sees the mock-up's invitation and the six commitments, written as first-person promises with their notes (authored in ticket 10a), as tick-boxes. Accepting needs every box ticked; declining is always offered and is worded as a good outcome, not a failure
- [ ] Only whether the coach accepted or declined is stored, not which boxes they ticked. One commitment affirms the coach's own faith, so individual ticks would be special category data about the coach. A coach has no account and writes nothing else
- [ ] The participant is told whether the coach accepted or declined, with no detail of a decline. After a decline they are offered to choose someone else, which leads back to the coach checklist; carrying on without a coach stays allowed
- Known limit, recorded with the observers' one (13b): the participant holds a copy of the coach's link, so they could accept the commitments on the coach's behalf. Nothing private leaks, but the participant could be told their coach agreed when they never did. Claiming doesn't help, since the participant can claim as easily as use; only the application reaching the coach itself (email, or a coach account) would, and neither is in this milestone
- [ ] Journey tests cover accepting, declining, that accepting needs every commitment, and refusal of wrong, expired or revoked coach tokens

**Carried from 10a**

- The chosen coach is one `Contact` with the coach role, under the coach checklist's block id (`coach` in `whatever-you-do.json`), read into the answers under that id. Saving another coach replaces the row and "Remove" deletes it, so its id does not last: bind the coach's link to it with that in mind, as 13a must for contacts, and decide whether choosing someone else or removing revokes a link already issued
- The coach page's "Choose someone else" already leads back to the checklist, so the way back after a decline can lead there
- The participant's name is not asked anywhere; the account holds only an email. If the coach's invitation needs it, it belongs on the account, not in a block

## Comments

- Decided with the developer (2026-09-29), the two points the mock-up left open: after a decline the participant is offered to choose someone else, back through the coach checklist, and may still carry on without a coach; a partial agreement is never shown, only "declined", since which boxes were ticked is never stored. The coach can explain in person if they want to. Blocked by 13b as well as 13a, so the coach's known limit is recorded beside the observers'.
