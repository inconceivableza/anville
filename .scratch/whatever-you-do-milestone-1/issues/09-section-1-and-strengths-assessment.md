# 09: Section 1 and the Strengths assessment section

**What to build:** Section 1 ("How you have been designed") and a separate "Strengths assessment" section holding the sort and its results. The sort is its own section so the offline track can include it without the rest of Section 1 (ticket 23). Section 1 keeps the scripture read-confirm and the written reflection, links to the Strengths assessment, and completes once the sort is answered and the reflection written. Together with tickets 06 and 07, this is the spine of the 2 Oct demo.

**Blocked by:** 04 (Hub, locks, gates and explicit completion), 07 (Sort and fine-tune widget)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [ ] A "Strengths assessment" section contains the sort block and the results, requires only onboarding, and appears on the hub as its own entry
- [ ] Section 1 uses the prototype's scripture passages and hint text; after the read-confirm it shows a link to the Strengths assessment section with its status, then a written reflection prompt
- [ ] Section 1's gate has a clause and message for each unmet requirement: the sort not answered (a block-has-an-answer clause referring to the sort block in the other section), and the reflection empty
- [ ] Completing either section is an explicit action, refused by the server if its gate fails
- [ ] Known consequence, accepted: a participant can reach the sort from the hub before reading Section 1's scripture
- [ ] The prototype's "comparison viewed" requirement is not present yet; it joins in ticket 16
- [ ] Retake is not offered in this milestone
- [ ] Content is migrated verbatim from the prototype reference
