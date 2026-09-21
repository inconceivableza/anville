# 15: Observer questionnaire

**What to build:** The observer's questionnaire, working end to end. Following their invitation link, an observer sorts and fine-tunes the same 36 statements about the participant (in the third person), answers seven written questions, and finishes with a thank-you. Their answers are stored in the observer response record from ticket 14. The prototype's version is unreachable in normal use; this is designed fresh.

**Blocked by:** 07 (Sort and fine-tune widget), 13 (Observer invitations and landing), 14 (Observer responses, aggregation and suppression)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** fourth, together with ticket 13. If time runs short, the comparison is fed by seeded test observers (ticket 14) and labelled as illustrative (ticket 16).

- [ ] The sort and slider screens address the participant's first name in the third person and reuse the sort widget with observer wording
- [ ] Thirty-two items are shared with the participant verbatim; the four that say "you" or "yours" carry observer wording: outlast them, different from theirs, matters to them, they could explain it
- [ ] The Christian framing is kept; observers see no participant-facing first-person copy
- [ ] Seven written questions (what energises them, three best qualities, a new skill, an existing skill, a character area, the biggest change seen, what they struggle with) are stored and never shown to the participant
- [ ] The observer chooses a relationship, stored but never used to slice or filter results
- [ ] One submission per token, then locked
- [ ] An observer can withdraw through their link while it is valid, which deletes their answers; how an observer withdraws after the link expires is open (see spec Further Notes)
- [ ] A thank-you screen closes the flow; an observer can always reach the questions by following their link
- [ ] Journey tests cover the full observer path, the lock after submission, and withdrawal
