# 15b: The observer's relationship and withdrawal

**What to build:** Around their observer assessment (ticket 15a), the observer says how they know the participant, finishes with a thank-you, and can withdraw through their claimed link, which deletes their answers.

**Blocked by:** 15a (The observer's assessment)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Spec:** Observers (ADR 0005); Agreed cut order, if time runs short; Open content and product items; Testing Decisions

**Cut order:** fourth, together with 13b and 15a.

- [ ] The observer chooses a relationship, stored but never used to slice or filter results
- [ ] A thank-you screen closes the flow; an observer following their claimed link after sending sees only the thank-you and withdrawal
- [ ] An observer can withdraw through their claimed link while it is valid, which deletes their answers; how an observer withdraws once the link has stopped working is open (spec, Open content and product items)
- [ ] Withdrawal works only through the claimed secret (ticket 13b), never the participant's copy of the link
