# 07: Sort and fine-tune widget

**What to build:** The interactive sort. A participant sorts the 36 statements into five named buckets one card at a time, then fine-tunes each with a slider seeded by its bucket, and submits one answer that the server validates and scores. This is the only part of the prototype that works for real, so it must feel the same.

**Blocked by:** 06 (Scoring core and results page)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [ ] A Vite module presents one card at a time in a randomised order, with the five named buckets, a per-bucket count, and full undo history
- [ ] All 36 must be sorted before continuing
- [ ] The fine-tune step groups statements under their bucket, seeds each slider from the bucket's seed, skips empty buckets, and leaves untouched sliders at their seeds, so a sort alone gives a complete profile
- [ ] Step labels are consistent (the prototype said "Step 1 of 3" and later "Step 2 of 2")
- [ ] The widget submits exactly one answer; the server validates it and never trusts the widget, then computes and stores the result
- [ ] On completion the participant is taken to the results page
- [ ] The widget is checked by hand (no browser tests this milestone); the answer validator is covered by seams 1 and 2
