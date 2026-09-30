# 13b: The observer's landing page and claiming the link

**What to build:** An observer following their link sees a privacy notice before anything else, and claims the link when they start, so the participant's copy stops working.

**Blocked by:** 13a (Issuing observer invitations)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Spec:** Observers (ADR 0005); Testing Decisions; Agreed cut order, if time runs short; Legalities are parked, not forgotten; Open content and product items

- [ ] Before any question, the landing page shows the privacy notice the spec describes, in observer wording where the document provides it and the participant's otherwise, through ticket 02's role-specific text resolution; it never says "completely anonymous"
- [ ] Opening the link claims nothing. Starting ("I'm answering for Sam") claims it: the observer gets a cookie and a fresh link shown once ("bookmark this, it's yours"), and the participant's copy stops working
- [ ] A second claim is told the link has already been used, so a participant who claimed it first is noticed rather than hidden, and can reissue; a reissued token reaches nothing the old one wrote, claimed or not
- [ ] The observer is the contact bound to the token, held apart from any answers; observers have no account, type no name, and never read or write participant state

**Carried from 09**

- [ ] Remove the "[Not built yet: …]" note from Section 1's two sentences about inviting people, in both pathway documents, leaving the prototype's wording as it is
