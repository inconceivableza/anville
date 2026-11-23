# 118: The coach's view names the participant

**What to build:** The coach's link shows the participant's results and comparison in the participant's own words, so a coach reads "Your Contribution Profile", "You rate higher" and "Questions to sit with" about someone else. Word them for the coach, about the participant by name, as the observer's pages already are, and say so in the line above them.

**Blocked by:** 108 (its hand check found it)

**Status:** resolved

**Sprint:** 3d (end not yet set)

**Spec:** Sprint 3d: the code review and the 30 October feedback, "The coach's view names the participant"; Coach

- [x] A text field may have wording for a third role, `coach`, with `{name}` the participant's name; where it has none, a coach reads the observer's wording, then the participant's, so the item texts already worded for observers serve with no new wording
- [x] The coach's link words the results (the frameworks' headings and subtitles, the disclaimer, the item scores) and the comparison (the gaps' introduction, badges and descriptions, and the questions' heading, introduction and questions) for the coach
- [x] *Whatever You Do* gives the coach wording for each of those that says "you"; the faithful port, which has no coach, is unchanged
- [x] The line above the results says "[name] is happy for you to see this: the results and comparison [name] sees.", not "exactly as [name] sees it"
- [x] The participant's own results and comparison are unchanged
- [x] A participant on a pathway version loaded before keeps that version's wording
- [x] The new wording is in the wording changes document

**Context**

- Found in the hand check of ticket 108 on 17 Nov: the coach Sam's link for Ada read "✨ Your Contribution Profile", "Where your self-perception differs…", "YOU RATE HIGHER (+9)" and "Questions to sit with", under "How others see Ada" and beside "Ada: Leading", which sprint-3d-r1-fix-2 had already named. The developer: "Coach's link should talk about the participant, not "you", like the observer link."
- Built as a third role in the role-keyed wording that already served the participant and the observer (`engine/document/text.py`), threaded through the results and comparison as a `Voice` (`engine/results.py`), so `{name}` is filled in every field a coach reads.
- Manual check: `docs/manual-checks.md`, "Ticket 118: The coach's view names the participant".
