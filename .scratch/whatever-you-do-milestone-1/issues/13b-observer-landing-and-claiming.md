# 13b: The observer's landing page and claiming the link

**What to build:** An observer following their link sees a privacy notice before anything else, and claims the link when they start, so the participant's copy stops working.

**Blocked by:** 13a (Issuing observer invitations)

**Status:** resolved

**Sprint:** 1 (ends 2 Oct)

**Spec:** Observers (ADR 0005); Testing Decisions; Agreed cut order, if time runs short; Legalities are parked, not forgotten; Open content and product items

- [x] Before any question, the landing page shows the privacy notice the spec describes, in observer wording where the document provides it and the participant's otherwise, through ticket 02's role-specific text resolution; it never says "completely anonymous"
- [x] Opening the link claims nothing. Starting ("I'm answering for Sam") claims it: the observer gets a cookie and a fresh link shown once ("bookmark this, it's yours"), and the participant's copy stops working
- [x] A second claim is told the link has already been used, so a participant who claimed it first is noticed rather than hidden, and can reissue; a reissued token reaches nothing the old one wrote, claimed or not
- [x] The observer is the contact bound to the token, held apart from any answers; observers have no account, type no name, and never read or write participant state

**Carried from 09**

- [x] Remove the "[Not built yet: …]" note from Section 1's two sentences about inviting people, in both pathway documents, leaving the prototype's wording as it is

## Answer

- What reissuing does to submitted answers, and the cookie's one claim: carried to 15
- `SECURE_PROXY_SSL_HEADER`, and keeping links out of access logs: carried to 26
- The welcome's wording and the name used: in the spec, "To show the content owner, from ticket 13b"
