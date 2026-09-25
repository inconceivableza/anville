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

**Carried from 06**

- [ ] Section 1's gate cannot name the sort yet. The criterion above asks for "a block-has-an-answer clause referring to the sort block in the other section", and the linter refuses exactly that: "a gate clause may only name a block in its own section" (`engine/document/lint.py`, from ticket 04, which reasoned that a gate decides whether its own section is finished). Relax that rule for `has_answer`, or add a named clause for "a block in another section is answered" (ADR 0003). Decide before building the section
- Placing the sort is document work: `{"id": "…", "type": "sort_assessment"}` in the Strengths assessment section. `pathways/whatever-you-do.json` already holds the instrument, both frameworks, the scoring method and the results wording, and the linter refuses a sort without them

**Carried from 07**

- The Strengths assessment section needs a gate with a `has_answer` clause for the sort, or the linter refuses the document. The engine shows no completion control while the sort is not in; once it is, completing the section is the usual explicit action
- [ ] Run the rest of `docs/manual-checks.md` for the sort against the real pathway: untouched sliders giving a complete result, no JavaScript, keyboard only, screen reader, reduced motion, phone width, and the second-sort message. Ticket 07 had one happy-path walkthrough only
- [ ] The prototype gave PEP bars a minimum width of 4% (`Math.max(4, pct)`), which the results page left out. Check with real sorts whether a 0% bar needs the stub
- [ ] Decide whether the sort needs the prototype's progress bar. The prototype filled 0–40% of its page-wide bar during the sort (`Math.round(done/36*40)`) and set 45% on fine-tuning; the widget shows only the card counter ("7/36"), and the hub shows progress by section. Judge it during the hand check above, with the developer or the owner
