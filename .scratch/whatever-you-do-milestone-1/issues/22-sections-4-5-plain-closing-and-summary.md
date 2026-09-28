# 22: Sections 4 and 5 (plain), closing ratings and summary

**What to build:** The rest of the pathway, plainly. The growth plan as a reflection section (no planning board), then the closing: the four after-ratings from Section 5 (ticket 05) shown beside the first set, and a summary of the participant's work.

**Blocked by:** 10 (Onboarding completion)

**Status:** ready-for-agent

**Sprint:** 3 or later

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] Section 4 (growth plan) presents the five categories (steps of faith, grow gifting, character, mentorship, disciple others) as reflection prompts with their questions, reasons and suggestions, captured as text; there is no quarter board
- [ ] Section 5 (letter and after-ratings) comes from ticket 05; nothing here promises delivery on a future date or schedules anything
- [ ] The closing shows the after-ratings from Section 5 beside the first set
- [ ] A closing summary shows the participant's work from stored answers, and a congratulations screen ends the pathway
- [ ] Section 4 has no gate; this is deliberate and carried from the prototype, so the section can be completed with no activities. Record it as a choice an author can change
- [ ] Copy makes no promise the system cannot keep

**Carried from 29**

- [ ] The closing's comparison pairs every `bl-*` rating with its `pl-*` rating rather than assuming four: `pathways/whatever-you-do.json` has five (with `bl-peace`/`pl-peace`), while the faithful port keeps the prototype's four
- Both sets of ratings are fixed once their section is complete (`fixed_once_complete`), so the comparison shows answers that can no longer change
- Section 4 and the closing go into both pathway documents; the drift test fails if only one takes them
