# 107: The letter and the closing questions on two pages

**What to build:** Section 6 holds the task, the letter, the five closing questions, the date and the seal on one long page, and the content owner would have the questions and the letter on two (feedback, "Friday 30th - updates", image 54). The order stays: the task and the letter on the first page, which saves the letter and leads on; "Where are you now?", the date and the seal on the second. The review also found nothing checks that a letter's months make sense, which the schema cannot say.

**Blocked by:** 105 (The engine tidy-up from the code review), A1

**Status:** resolved

**Sprint:** 3d (end not yet set)

**Spec:** Sprint 3d: the code review and the 30 October feedback; Blocks; Engine: sections, tracks, gates, progress

- [x] Section 6's first page holds the task, the verse and the letter, with Print and Copy text; its button saves the letter and opens the second page, holding "Where are you now?", the date and the seal
- [x] The second page's back button returns to the letter, everything kept; sealing is refused, beside the button, until the letter and all five questions are in, and a refusal for a short letter says where to go to fix it
- [x] Without JavaScript both pages work by reload, and a refusal opens at its message
- [x] Once sealed, the participant lands on the sealed letter as now, and the questions show as fixed answers
- [x] The linter refuses a letter whose earliest, default and latest months are not in that order, at the letter's document path, with one message

**Context**

- Ticket 104's sealing, dates and email are unchanged; the new button and any changed line go in the wording changes document
