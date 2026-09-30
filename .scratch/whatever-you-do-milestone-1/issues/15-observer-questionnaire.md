# 15: Observer questionnaire

**What to build:** The observer's questionnaire, working end to end. Following their invitation link, an observer sorts and fine-tunes the same 36 statements about the participant (in the third person), answers seven written questions, and finishes with a thank-you. Their answers are stored in the observer response record from ticket 14. The prototype's version is unreachable in normal use; this is designed fresh.

**Blocked by:** 07 (Sort and fine-tune widget), 13b (The observer's landing page and claiming the link), 14 (Observer responses, aggregation and suppression)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** fourth, together with ticket 13b. If time runs short, the comparison is fed by seeded test observers (ticket 14) and labelled as illustrative (ticket 16).

- [ ] The sort and slider screens address the participant's first name in the third person and reuse the sort widget with observer wording
- [ ] Thirty-two items are shared with the participant verbatim; the four that say "you" or "yours" carry observer wording: outlast them, different from theirs, matters to them, they could explain it
- [ ] The Christian framing is kept; observers see no participant-facing first-person copy
- [ ] Decide before building the written questions: the qualitative strengths work in sprint 2 (`Prototypes for reference/qualitative-strengths-prototype.html`) replaces the seven with six, asked of the participant too, and shows observers' answers back shuffled. Either this ticket builds the sort only and all written questions move to sprint 2, or it collects the six now, stored and not yet shown, or it keeps the seven below and sprint 2 reworks them
- [ ] Seven written questions (what energises them, three best qualities, a new skill, an existing skill, a character area, the biggest change seen, what they struggle with) are stored and never shown to the participant
- [ ] The observer chooses a relationship, stored but never used to slice or filter results
- [ ] One submission per token, then locked
- [ ] Submitted answers are never shown back through any link. The participant copies every link, so a read-back would show them one observer's answers and get round ticket 14's minimum of three
- [ ] The questionnaire, and withdrawal, work only through the observer's claimed secret (ticket 13b), never the participant's copy
- [ ] An observer can withdraw through their claimed link while it is valid, which deletes their answers; how an observer withdraws after the link expires is open (see spec Further Notes)
- [ ] A thank-you screen closes the flow; an observer following their claimed link before submitting reaches the questions, and after submitting sees only the thank-you and withdrawal
- [ ] The participant sees an overall count of answers, never which invited person has answered (ADR 0005)
- [ ] Journey tests cover the full observer path, the lock after submission, withdrawal, that no answer is shown after submission, and that the participant's copy of the link can neither answer nor withdraw once claimed

**Carried from 07**

- [ ] The sort widget's own wording is written into `frontend/src/sort.js`: "Sort your strengths", "Choose the bucket that fits best", "All 36 sorted!", "How strong is each one?", the fine-tune intro, and the slider anchors "Not me" and "Real strength". Observer wording needs it in the third person, so move it into the pathway document, role-keyed like other text, and hand it to the widget through the block type's `widget` entry, which already takes the role (`_sort_widget(document, role)` in `engine/document/blocks.py`)
- The widget's contract: the page gives it `{"items": [{"id", "text"}], "buckets": [{"id", "label", "seed"}]}` (buckets weakest first) in a `json_script` beside a form it fills in. The form posts the whole sort once as `value`, and the server's `HX-Redirect` decides where the browser goes next, so an observer's flow can send them somewhere other than the results

**Carried from 13b**

- [ ] Reissuing or revoking a link deletes its invitation record (a new one is created on reissue). Decide whether submitted answers go with it before binding them to the invitation; a cascading key would let a reissue silently delete what an observer submitted
- The observer's pages know them by the `observer` cookie their claim set, which holds one claim: someone observing for two participants keeps the first through its own link only. A plain visit to an own link sets no cookie, so another site cannot plant a claim

## Comments

- Split of 13 (2026-09-29): the overall count of answers moved here from 13, since there are no answers to count before this ticket and 14.
