# 15b: The observer's relationship and withdrawal

**What to build:** Around their observer assessment (ticket 15a), the observer says how they know the participant, finishes with a thank-you, and can withdraw through their claimed link, which deletes their answers.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 2b (12–16 Oct); carried from sprint 1

**Spec:** Observers (ADR 0005); Open content and product items; Testing Decisions

- [ ] The observer chooses a relationship, stored but never used to slice or filter results
- [ ] A thank-you screen closes the flow; an observer following their claimed link after sending sees only the thank-you and withdrawal
- [ ] An observer can withdraw through their claimed link while it is valid, which deletes their answers. Once the link has stopped working they ask the people who run the service, as the privacy notice says (B2B-55)
- [ ] Withdrawal works only through the claimed secret (ticket 13b), never the participant's copy of the link

**Carried from 15a**

- An observer's answers are found by a hash of their claimed secret, never through the contact or invitation (ADR 0009); withdrawing deletes the observer response found that way. ADR 0014 lets the operator link an observer to their answers, but the code still finds them by the hash
- After sending, the observer's page already shows a plain thank-you in place of the observer assessment (the prototype's sentence without "submitted anonymously"), from the cookie and from the own link alike; withdrawal goes beside it

**Context**

- The contact-loop prototype would turn this thank-you into the observer's own answers and an offer of the course. That is not planned, and its first screen conflicts with sent answers never being shown back (spec, Open content and product items, "Prototypes not yet planned"). Build the plain thank-you; keep it simple enough to replace
