# 105: The engine tidy-up from the code review

**What to build:** Nothing a participant sees changes. The code review of 9–12 Nov found the engine's views deciding what belongs to a block type, a line of pathway copy written into the engine twice, two code paths doing one job, and tests that reach past the two seams or assert wording. Each rule moves to the one place the coding standards give it, and the tests go back to the seams, so the tickets after this one change a block in one place.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 3d (end not yet set)

**Spec:** Sprint 3d: the code review and the 30 October feedback; Blocks; Testing Decisions

- [ ] What a block type shows and how it saves (the words on the button that ends it, whether it saves quietly, its anchors, how its question reads inside a sentence) is decided in the block type's own entry or a function beside it, and no view tests a block's type to decide it
- [ ] Copy shown in one pathway's words (the comparison's waiting line, refusals that name the strengths evaluation) comes from the pathway document or the block type's entry, written once
- [ ] Withdrawing through an expired link goes through one path for coaches and observers, and the document's "messages only after a press" setting is read in one place
- [ ] The next step's photos and the retake are tested through the participant journey, without calling the engine's internal helpers or reading the stylesheet, and no test asserts authored wording
- [ ] Docstrings say what the code does, not how it came to be (no "fix-10", "until ticket 87", "where before"); every function in the letter's module has one

**Context**

- Where the review found them: in the views, the comparison's end button chosen by block type, the quiet-save check on the agreement scale, the coach checklist's anchors, the checklist question's first letter lower-cased, and the comparison's waiting sentence, which its template repeats; the expired-link withdrawal in both the coach's and the observer's view; the next-step photo test and the retake test's wording assertions
- Judgement calls from the review, to take where they fall out of the moves above: the back link's title and address built by hand in three places; the wizard's and the welcome's verse, reference and label defined twice in the schema; the coach's "withdrawn" kept as a plain string among their answers, and the letter's "sealed" state likewise; the two "withdrew" flags passed together
- The spec's "Engine tidying without a ticket" (Sprints) names the section signpost spread over three files; it may come with the first point if it falls out of the same move
