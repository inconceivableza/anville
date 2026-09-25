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

**Carried from 06**

- The contract the widget sends: one POST to `/answers/<block_id>/` with `value` holding the whole sort as JSON, `{"<item id>": {"bucket": "<bucket id>", "value": <whole number 0–100>}, …}`, for every item and no others. `50.0` is refused. The server scores it and stores the result in the same transaction, and a second sort is refused with 409, since there is no retake. `engine/templates/engine/blocks/sort_assessment.html` is a placeholder for the widget to replace
- [ ] Land on the results page. After a sort is stored, a non-htmx submit redirects to the section and an htmx one returns the section's save result; neither reaches `/results/<block_id>/`, which the criterion above asks for
- [ ] The prototype gave PEP bars a minimum width of 4% (`Math.max(4, pct)`), which the results page left out. Check by hand, with real sorts, whether a 0% bar needs the stub
