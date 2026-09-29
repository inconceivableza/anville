# 13b: The observer's landing page and claiming the link

**What to build:** An observer following their link sees a privacy notice before anything else, and claims the link when they start, so the participant's copy stops working (ADR 0005). Split from ticket 13.

**Blocked by:** 13a (Issuing observer invitations)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** fourth, together with ticket 15. If time runs short, the comparison is fed by seeded test observers (ticket 14) and labelled as illustrative (ticket 16).

- [ ] The landing page shows a privacy notice before any question: who asked, what is stored, what the participant will and will not see, that the observer's name is never shown to the participant, and how to withdraw; it never says "completely anonymous". Observer-facing text uses the role-specific text resolution from ticket 02, serving observer wording where the document provides it and falling back to the participant's
- [ ] The observer claims the link on first use. The participant copies every link, so whoever holds it could otherwise read or delete that observer's answers. Opening the link shows only the landing page; starting ("I'm answering for Sam") exchanges the token for a secret only the observer holds, a cookie plus a fresh link shown once ("bookmark this, it's yours"), and the participant's copy stops working. A second attempt to claim is told the link has already been used, so a participant who claims it is noticed rather than hidden, and can reissue. A reissued token reaches nothing the old one wrote, whether or not the old one was claimed
- [ ] The observer's identity is the contact record bound to the token, held separately from any answers; observers have no account and type no name. Observers never read or write participant state (the prototype overwrote it)
- [ ] Known limit, recorded in ADR 0005 or ticket 31's new ADR: the participant's copy behaves differently once claimed, and the answer count rises, so a participant can tell whether a given person has started or answered. The privacy notice promises nothing about that
- [ ] Journey tests cover that opening the link claims nothing, that a claimed link is dead to its original holder, a second claim, and that a reissued token reaches nothing the old one wrote

**Carried from 09**

- [ ] Once invitations work, remove the bracketed "[Not built yet: inviting people you trust comes in a later version.]" from Section 1's two sentences about inviting people, in both `pathways/whatever-you-do.json` and `pathways/whatever-you-do-faithful-port.json`, leaving the prototype's wording as it is
