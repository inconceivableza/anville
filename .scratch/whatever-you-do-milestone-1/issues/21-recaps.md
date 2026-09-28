# 21: Recaps

**What to build:** The recap block: a read-only panel that shows earlier answers back through a named view, with limits and an authored message for when there is nothing yet. Wired into the places the prototype used it. Views are implemented in code and chosen by name in the document (ADR 0003).

**Blocked by:** 09 (Section 1 and the Strengths assessment section), 17 (Timeline section), 18 (Calling statement (sentence builder)), 19 (Possibilities (idea generator)), 20 (Role pictures (card builder))

**Status:** ready-for-agent

**Sprint:** 3 or later

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] A recap block names a view, its parameters (caps and ordering) and an authored empty-state message; the document never contains logic
- [ ] Views available: top constructs (top three APEST(d) and top two PEP with personas), marker counts and the fruit and leading markers with their chapters (capped), the calling statement, starred possibilities (capped), and developed role pictures
- [ ] Recaps are placed at the head of the calling-statement section, on the Section 1 page as a compact snapshot, above the role pictures, and at the growth plan and letter reflection sections
- [ ] The prototype's growth-plan-activities view is not built: in this milestone the growth plan is plain text, so it has no activities to recap. The letter's recap uses the calling statement and starred possibilities
- [ ] The prototype's "biggest gap versus observers" view is not included here; it can be added as a follow-up once the comparison exists
- [ ] Each view has an authored empty state and behaves correctly with no data
- [ ] Views read from stored answers, never from hidden page fields (the prototype's DOM mirrors are not ported)
- [ ] Pure-core tests cover each view including empty and capped cases
