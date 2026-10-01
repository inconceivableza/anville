# 07: Sort and fine-tune widget

**What to build:** The interactive sort. A participant sorts the 36 statements into five named buckets one card at a time, then fine-tunes each with a slider seeded by its bucket, and submits one answer that the server validates and scores. This is the only part of the prototype that works for real, so it must feel the same.

**Blocked by:** 06 (Scoring core and results page)

**Status:** resolved

**Handed over:** two criteria below are still to check by hand, in 09; see Answer.

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [x] A Vite module presents one card at a time in a randomised order, with the five named buckets, a per-bucket count, and full undo history
- [x] All 36 must be sorted before continuing
- [ ] The fine-tune step groups statements under their bucket, seeds each slider from the bucket's seed, skips empty buckets, and leaves untouched sliders at their seeds, so a sort alone gives a complete profile (built; untouched sliders not yet seen by hand, carried to 09)
- [x] Step labels are consistent (the prototype said "Step 1 of 3" and later "Step 2 of 2")
- [x] The widget submits exactly one answer; the server validates it and never trusts the widget, then computes and stores the result
- [x] On completion the participant is taken to the results page
- [ ] The widget is checked by hand (no browser tests this milestone); the answer validator is covered by seams 1 and 2 (validator covered; one happy-path walkthrough done, the rest of `docs/manual-checks.md` carried to 09)

**Carried from 06**

- The contract the widget sends: one POST to `/answers/<block_id>/` with `value` holding the whole sort as JSON, `{"<item id>": {"bucket": "<bucket id>", "value": <whole number 0–100>}, …}`, for every item and no others. `50.0` is refused. The server scores it and stores the result in the same transaction, and a second sort is refused with 409, since there is no retake. `engine/templates/engine/blocks/sort_assessment.html` is a placeholder for the widget to replace
- [x] Land on the results page. After a sort is stored, a non-htmx submit redirects to the section and an htmx one returns the section's save result; neither reaches `/results/<block_id>/`, which the criterion above asks for
- Carried on to 09, which has the real sorts to check it with: the prototype gave PEP bars a minimum width of 4% (`Math.max(4, pct)`), which the results page left out. Check by hand, with real sorts, whether a 0% bar needs the stub

## Comments

- First step: the server's side of the widget. The section page hands the widget every item in the participant's wording and the buckets weakest first (a `widget` entry on the block type), and a stored sort now goes to `/results/<block_id>/`: a 303 without htmx, `HX-Redirect` with it. A bucket's seed must now be a whole number, since it is the answer an untouched slider gives. That meets the carried "Land on the results page" item; the criterion "On completion the participant is taken to the results page" waits for the widget, which is the next step.
- Second step: the widget, `frontend/src/sort.js`, run by the sort block's form. It sends the whole sort once through htmx, and the server's `HX-Redirect` lands the participant on the results; a 409 now shows its reason instead of a connection error. This step adds `docs/manual-checks.md`, so that what the browser does (no JavaScript, keyboard, screen reader, reduced motion, phone width) is written down for whoever checks it.
- Hand check (2026-09-25): one walkthrough of the happy path, with a copy of the pathway that places the sort, found no issues. It showed the cards, buckets, counts and undo, the step labels, and landing on the results; the criteria it covered are ticked. It did not cover untouched sliders or the rest of `docs/manual-checks.md` (no JavaScript, keyboard, screen reader, reduced motion, phone width, the second-sort message), nor the PEP 0% bar, so those stay open and are carried to 09, where the real pathway first places the sort.
- The walkthrough found a "Mark complete" button beside the sort, which the prototype never had: a participant could complete the section, and open what follows, without sorting or seeing their results. Decided with the developer: while a section's sort is not in, the section shows no completion control, and the linter refuses a sort whose section's gate has no `has_answer` clause for it, so the server refuses completion too. 09 gives the real Strengths assessment section that gate.
- Review (`/code-review` over both commits): keyboard focus was lost when undo emptied the history (focus went to a now-disabled button), and now falls back to the heading; `docs/manual-checks.md` says "items" as the glossary does; the codes htmx shows a reason for are listed once. Carried on: the prototype's progress bar during the sort, to 09 to decide at its hand check; the widget's hard-coded wording, which 15 needs in the third person.

## Answer

Resolved with handovers. Everything is built and covered by tests where a test can reach it. What is left is checking by hand in the browser, which 09 does against the real pathway, since 09 is where Whatever You Do first places the sort.

Built in `frontend/src/sort.js` (the widget, mounted from `main.js`) and `engine/templates/engine/blocks/sort_assessment.html` (its form and data). The block type's `widget` entry in `engine/document/blocks.py` gives the widget its items and buckets. `engine/views.py` sends a stored sort to its results, and hides a section's completion control while its sort is not in. `engine/document/lint.py` requires a sort's section to gate on it. The README's "Scoring and results" section describes the behaviour, and `docs/manual-checks.md` lists what to check by hand.

Decisions made along the way, with the developer:

- The step labels read "Step 1 of 2 — Sort" and "Step 2 of 2 — Fine-tune".
- Undo also works on the "All 36 sorted!" screen, so a slip on the last card can be taken back. The prototype had no undo there.
- A section offers no way to complete it while its sort is not in, as in the prototype, and its gate must require the sort, so the server refuses completion too.
- A bucket's seed must be a whole number, since an untouched slider sends it as the answer.
- Keyboard focus, a screen-reader announcement per card, and skipping the fly animation under reduced motion were added beyond the prototype.
- Browser behaviour is checked by hand against `docs/manual-checks.md`, which is to grow with each change a test cannot see.

Handed over:

- 09: the rest of `docs/manual-checks.md` for the sort (including untouched sliders, which leaves criteria 3 and 7 above open until then), the PEP 0% bar, whether the sort needs the prototype's progress bar, and the gate its Strengths assessment section needs
- 15a: the widget's hard-coded wording, needed in the third person for observers, and the widget's contract
