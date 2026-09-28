# 13: Observer and coach invitations

**What to build:** Invitations for observers (ADR 0005) and for the coach. From the contacts they entered, a participant issues a unique link per observer, copies it and sends it themselves. An observer following the link reaches a landing page with a privacy notice; expired, revoked or unknown links are refused. No email is sent. The coach the participant chose in onboarding (ticket 10) gets a link of the same kind, which asks them to accept or decline the six commitments from the content owner's mock-up.

**See also:** `Prototypes for reference/coach-selection-prototype.html`, the content owner's mock-up of choosing a coach. Its participant half is ticket 10; its coach half is built here. Letting the coach see shared sections is ticket 27.

**Blocked by:** 10 (Onboarding completion)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** fourth, together with ticket 15. If time runs short, the comparison is fed by seeded test observers (ticket 14) and labelled as illustrative (ticket 16).

- [ ] A participant can issue, copy, revoke and reissue a link for each contact; reissuing invalidates the previous link
- [ ] A participant who skipped the contact list in onboarding can add contacts here
- [ ] The participant sees an overall count of answers, never which invited person has answered (ADR 0005)
- [ ] A token is 32 random bytes and only its hash is stored; the link lives for a period set in the pathway document (30 days by default) and expires accordingly
- [ ] The observer's identity is the contact record bound to the token, held separately from any answers; observers have no account and type no name
- [ ] The landing page shows a privacy notice before any question: who asked, what is stored, what the participant will and will not see, that the observer's name is never shown to the participant, and how to withdraw; it never says "completely anonymous"
- [ ] Wrong, expired and revoked tokens are refused without revealing anything about the participant
- [ ] Observers never read or write participant state (the prototype overwrote it)
- [ ] Observer-facing text uses the role-specific text resolution from ticket 02, serving observer wording where the document provides it and falling back to the participant's
- [ ] Journey tests cover expiry after the configured lifetime (including a non-default value), revocation, reissue, wrong token, and only a hash being stored

**The coach's link**

- [ ] A participant who chose a coach in onboarding (ticket 10) issues the coach's link, copies it and sends it themselves, with the same token approach, lifetime, revocation and reissue as observers
- [ ] Following the link, the coach sees the mock-up's invitation and the six commitments, written as first-person promises with their notes (authored in ticket 10), as tick-boxes. Accepting needs every box ticked; declining is always offered and is worded as a good outcome, not a failure
- [ ] Only whether the coach accepted or declined is stored, not which boxes they ticked. One commitment affirms the coach's own faith, so individual ticks would be special category data about the coach
- [ ] The participant is told whether the coach accepted or declined, with no detail of a decline. The mock-up leaves open whether a declined participant goes back to choose someone else, and whether a partial agreement is shown to them; decide both here
- [ ] A coach has no account and writes nothing beyond accepting or declining
- [ ] Journey tests cover accepting, declining, that accepting needs every commitment, and refusal of wrong, expired or revoked coach tokens
