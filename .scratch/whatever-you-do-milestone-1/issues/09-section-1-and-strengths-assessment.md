# 09: Section 1 and the Strengths assessment section

**What to build:** Section 1 ("How you have been designed") and a separate "Strengths assessment" section holding the sort and its results. The sort is its own section so the offline track can include it without the rest of Section 1 (ticket 23). Section 1 keeps the scripture read-confirm and the written reflection, links to the Strengths assessment, and completes once the sort is answered and the reflection written. Together with tickets 06 and 07, this is the spine of the 2 Oct demo.

**Blocked by:** 04 (Hub, locks, gates and explicit completion), 07 (Sort and fine-tune widget)

**Status:** claimed

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [x] A "Strengths assessment" section contains the sort block and the results, requires only onboarding, and appears on the hub as its own entry
- [x] Section 1 uses the prototype's scripture passages and hint text; after the read-confirm it shows a link to the Strengths assessment section with its status, then a written reflection prompt
- [x] Section 1's gate has a clause and message for each unmet requirement: the sort not answered (a block-has-an-answer clause referring to the sort block in the other section), and the reflection empty
- [x] Completing either section is an explicit action, refused by the server if its gate fails
- [x] Known consequence, accepted: a participant can reach the sort from the hub before reading Section 1's scripture
- [x] The prototype's "comparison viewed" requirement is not present yet; it joins in ticket 16
- [x] Retake is not offered in this milestone
- [ ] Content is migrated verbatim from the prototype reference
- [ ] Each section can carry an authored time estimate ("About 15 minutes"), shown on its hub entry and at the top of the section; add one to every section with content, and one per activity where a section has several
- [ ] Every minimum-length gate message says how much is needed, for example "Write at least 10 characters…", including the existing ones such as the letter's "Write at least one part of your letter before sealing it." (`pathways/whatever-you-do.json`). The faithful port keeps the prototype's wording, so the drift test in `tests/journeys/test_whatever_you_do.py`, which compares the two documents whole, must expect the new messages the way it already expects the fifth rating

**Carried from 06**

- [x] Section 1's gate cannot name the sort yet. The criterion above asks for "a block-has-an-answer clause referring to the sort block in the other section", and the linter refuses exactly that: "a gate clause may only name a block in its own section" (`engine/document/lint.py`, from ticket 04, which reasoned that a gate decides whether its own section is finished). Relax that rule for `has_answer`, or add a named clause for "a block in another section is answered" (ADR 0003). Decide before building the section
- Placing the sort is document work: `{"id": "…", "type": "sort_assessment"}` in the Strengths assessment section. `pathways/whatever-you-do.json` already holds the instrument, both frameworks, the scoring method and the results wording, and the linter refuses a sort without them

**Carried from 07**

- The Strengths assessment section needs a gate with a `has_answer` clause for the sort, or the linter refuses the document. The engine shows no completion control while the sort is not in; once it is, completing the section is the usual explicit action
- [ ] Run the rest of `docs/manual-checks.md` for the sort against the real pathway: untouched sliders giving a complete result, no JavaScript, keyboard only, screen reader, reduced motion, phone width, and the second-sort message. Ticket 07 had one happy-path walkthrough only
- [ ] The prototype gave PEP bars a minimum width of 4% (`Math.max(4, pct)`), which the results page left out. Check with real sorts whether a 0% bar needs the stub
- [ ] Decide whether the sort needs the prototype's progress bar. The prototype filled 0–40% of its page-wide bar during the sort (`Math.round(done/36*40)`) and set 45% on fine-tuning; the widget shows only the card counter ("7/36"), and the hub shows progress by section. Judge it during the hand check above, with the developer or the owner

## Comments

- Sort as its own section confirmed with the developer (2026-09-28), as the spec has it.
- First step: the linter lets a `has_answer` clause name a block in another section; the other clauses stay in their own section (decided with the developer, 2026-09-28). Ticket 23's closing ratings can wait on the sort the same way.
- Second step: a `section_link` block shows another section's title and status as the hub does, and names a locked section without linking it. Section 1 uses it for the Strengths assessment in the next step.
- Third step: Section 1 and the Strengths assessment are in both pathway documents, the Strengths assessment straight after Section 1 on the hub. Content is verbatim except: the two sentences about inviting people keep the prototype's wording and add "[Not built yet: inviting people you trust comes in a later version.]" (the developer's call; remove when ticket 13 lands), verse numbers are dropped as in the calling section, the reflection's italic "not" is plain, and the reflection's placeholder waits for the next step. The prototype's reflection appears only once the sort is done; here it appears after the read-confirm, and the gate still needs the sort. Prototype's "Open Strengths Assessment →" button is the linked title instead.
- Fourth step: `long_text` takes an optional `placeholder` (ghost text, escaped, never saved). Section 1's reflection has the prototype's "Draw on the scripture, your assessment results, and what others have told you..." and the letter has "Dear me,", which ticket 05 had left out.

**Remaining plan** (agreed with the developer, 2026-09-28; each step red, then green, then a commit when the developer says so)

- [ ] Step 5: the prototype shows the reflection only once the sort is done. Give `section_link` an option to hold the rest of its section shut until the linked section's gate passes (as a scripture reading does until confirmed), enforced by `open_blocks` so the answer endpoint refuses too. Also an optional authored button label on the link, for the prototype's "Open Strengths Assessment →" (and "Complete — view your results" once done)
- [ ] Step 6: minimum-length gate messages say how much is needed (criterion above)
- [ ] Step 7: time estimates (criterion above). First ask the developer how "one per activity where a section has several" is authored: on a block, or some other way
- [ ] Then `/code-review` against `aa840a5`, fix what it finds, and run the hand checks carried from 07 and those added to `docs/manual-checks.md` (the section link card, ghost text)
- [ ] On resolving: carry "remove the bracketed '[Not built yet: …]' note from Section 1's two invitation sentences" to ticket 13
- Not in this ticket: inline formatting (the italic *not* in the reflection prompt, bold phrases, lists in hints) is on the spec's later list
