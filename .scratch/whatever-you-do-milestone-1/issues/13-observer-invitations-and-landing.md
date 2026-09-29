# 13: Observer and coach invitations

**What to build:** Invitations for observers (ADR 0005) and for the coach. From the contacts they entered, a participant issues a unique link per observer, copies it and sends it themselves. An observer following the link reaches a landing page with a privacy notice; expired, revoked or unknown links are refused. No email is sent. The coach the participant chose in onboarding (ticket 10a) gets a link of the same kind, which asks them to accept or decline the six commitments from the content owner's mock-up.

**See also:** `Prototypes for reference/coach-selection-prototype.html`, the content owner's mock-up of choosing a coach. Its participant half is ticket 10a; its coach half is built here. Letting the coach see shared sections is ticket 27.

**Blocked by:** 10a (Onboarding completion)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** fourth, together with ticket 15. If time runs short, the comparison is fed by seeded test observers (ticket 14) and labelled as illustrative (ticket 16).

- [ ] A participant can issue, copy, revoke and reissue a link for each contact; reissuing invalidates the previous link, and the new token reaches nothing the old one wrote
- [ ] A participant who skipped the contact list in onboarding can add contacts here
- [ ] The participant sees an overall count of answers, never which invited person has answered (ADR 0005)
- [ ] The observer claims the link on first use. The participant copies every link, so whoever holds it could otherwise read or delete that observer's answers. Opening the link shows only the landing page; starting ("I'm answering for Sam") exchanges the token for a secret only the observer holds, a cookie plus a fresh link shown once ("bookmark this, it's yours"), and the participant's copy stops working. A second attempt to claim is told the link has already been used, so a participant who claims it is noticed rather than hidden, and can reissue
- [ ] Known limit, recorded in ADR 0005 or ticket 31's new ADR: the participant's copy behaves differently once claimed, and the answer count rises, so a participant can tell whether a given person has started or answered. The privacy notice promises nothing about that
- [ ] A token is 32 random bytes and only its hash is stored; the link lives for a period set in the pathway document (30 days by default) and expires accordingly
- [ ] The observer's identity is the contact record bound to the token, held separately from any answers; observers have no account and type no name
- [ ] The landing page shows a privacy notice before any question: who asked, what is stored, what the participant will and will not see, that the observer's name is never shown to the participant, and how to withdraw; it never says "completely anonymous"
- [ ] Wrong, expired and revoked tokens are refused without revealing anything about the participant
- [ ] Observers never read or write participant state (the prototype overwrote it)
- [ ] Observer-facing text uses the role-specific text resolution from ticket 02, serving observer wording where the document provides it and falling back to the participant's
- [ ] Journey tests cover expiry after the configured lifetime (including a non-default value), revocation, reissue, wrong token, only a hash being stored, that opening the link claims nothing, that a claimed link is dead to its original holder, and that a reissued token reaches nothing the old one wrote

**The coach's link**

- [ ] A participant who chose a coach in onboarding (ticket 10a) issues the coach's link, copies it and sends it themselves, with the same token approach, lifetime, revocation and reissue as observers
- [ ] Following the link, the coach sees the mock-up's invitation and the six commitments, written as first-person promises with their notes (authored in ticket 10a), as tick-boxes. Accepting needs every box ticked; declining is always offered and is worded as a good outcome, not a failure
- [ ] Only whether the coach accepted or declined is stored, not which boxes they ticked. One commitment affirms the coach's own faith, so individual ticks would be special category data about the coach
- [ ] The participant is told whether the coach accepted or declined, with no detail of a decline. The mock-up leaves open whether a declined participant goes back to choose someone else, and whether a partial agreement is shown to them; decide both here
- [ ] A coach has no account and writes nothing beyond accepting or declining
- Known limit, recorded with the observers' one: the participant holds a copy of the coach's link, so they could accept the commitments on the coach's behalf. Nothing private leaks, but the participant could be told their coach agreed when they never did. Claiming doesn't help, since the participant can claim as easily as use; only the application reaching the coach itself (email, or a coach account) would, and neither is in this milestone
- [ ] Journey tests cover accepting, declining, that accepting needs every commitment, and refusal of wrong, expired or revoked coach tokens

**Carried from 09**

- [ ] Once invitations work, remove the bracketed "[Not built yet: inviting people you trust comes in a later version.]" from Section 1's two sentences about inviting people, in both `pathways/whatever-you-do.json` and `pathways/whatever-you-do-faithful-port.json`, leaving the prototype's wording as it is
