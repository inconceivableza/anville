# 119: Section 1 completes as the evaluation ends

**What to build:** Section 1 is complete only once "I've finished Section 1" is pressed after the strengths evaluation, so a participant who has sorted and answered every tie-break pair is still told on the hub to "Start with the strengths evaluation". Complete it as the evaluation ends, and keep "I've finished Section 1" as the way on to the next section, no longer a press.

**Blocked by:** 106 (the shape rules for a section whose work is all in its parts), 108 (its hand check found it)

**Status:** resolved

**Sprint:** 3d (end not yet set)

**Spec:** Sprint 3d: the code review and the 30 October feedback, "Section 1 completes as the evaluation ends"; Engine: sections, tracks, gates, progress, "Finishing a section from the end of its part"

- [x] A section whose work is all in its parts and that ends in its signpost to a part whose last block is a sort completes itself once the sort is in and every tie-break pair is answered or skipped, decided by the document's shape, not a setting
- [x] It is re-checked as the press is (open, reached to its last page, its parts done, its gate met) and stored, so a retake leaves it complete (ADR 0025); the sort with no pairs and the last pair store it at once, and a participant whose evaluation ended before this is caught up on their next page
- [x] Its results offer "I've finished Section 1" as a link on to the hub whenever they show; Section 1's own page offers the same once it is complete, and nothing to press before
- [x] It is never taken back: no "Mark as not complete", and the reopen is refused, since it would complete again at once
- [x] The press still completes it, from a page left open or the demo shortcut
- [x] The faithful port's Section 1, with work of its own, keeps its press
- [x] The changed wording is in the wording changes document

**Context**

- Found in the hand check of ticket 108 on 17 Nov: after Ada's tie-break the hub's next step still read "Start with the strengths evaluation, which takes about 7 minutes." until "I've finished Section 1" was pressed. The developer: "completing the tie-break should mark section 1 as complete and the "I've finished section 1" should just be a process to continue onto the next section."
- Built where a hub side card's completion is stored the first time it is seen (`_store_completions_and_openings`), so every way the evaluation can end is covered; the shape rule is `completes_with_its_evaluation` in `engine/hub.py`, beside `works_through_its_parts` and `finish_waits`.
- Manual check: `docs/manual-checks.md`, "Ticket 119: Section 1 completes as the evaluation ends".
