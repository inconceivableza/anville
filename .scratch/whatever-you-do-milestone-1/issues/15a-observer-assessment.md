# 15a: The observer's assessment

**What to build:** Following their claimed link, an observer places and fine-tunes the same 36 items about the participant, in the third person, and sends their observer assessment, which is stored in the observer response record from ticket 14b and counts on its own. The prototype's version is unreachable in normal use; this is designed fresh.

**Blocked by:** 07 (Sort and fine-tune widget), 13b (The observer's landing page and claiming the link), 14b (Observer responses and seeding)

**Status:** resolved

**Sprint:** 1 (ends 2 Oct)

**Spec:** Observers (ADR 0005); Responses, answers and results; Agreed cut order, if time runs short; Testing Decisions

**Cut order:** fourth, together with 13b and 15b. If time runs short, the comparison is fed by seeded test observers (ticket 14b) and labelled as illustrative (ticket 16).

- [x] Placing and fine-tuning address the participant's first name in the third person through ticket 07's widget with observer wording; the Christian framing is kept, and observers see no participant-facing first-person copy
- [x] Thirty-two items are shared with the participant verbatim; the four that say "you" or "yours" carry observer wording: outlast them, different from theirs, matters to them, they could explain it
- [x] An observer following their claimed link before sending reaches the assessment; it works only through the claimed secret (ticket 13b), never the participant's copy
- [x] The observer assessment is sent once, counts on its own, and is then locked; it is never shown back through any link
- [x] Whatever binds the observer response to the observer leaves a sent assessment in place when the link is revoked or reissued or the contact removed (ADR 0007), and keeps it traceable to the observer, held apart from the participant, so a later way to withdraw stays possible (spec, Open content and product items)

**Carried from 07**

- [x] The widget's own wording is written into `frontend/src/sort.js`: "Sort your strengths", "Choose the bucket that fits best", "All 36 sorted!", "How strong is each one?", the fine-tune intro, and the slider anchors "Not me" and "Real strength". Observer wording needs it in the third person, so move it into the pathway document, keyed by role like other text, and hand it to the widget through the block type's `widget` entry, which already takes the role (`_sort_widget(document, role)` in `engine/document/blocks.py`)
- The widget's contract: the page gives it `{"items": [{"id", "text"}], "buckets": [{"id", "label", "seed"}]}` (buckets weakest first) in a `json_script` beside a form it fills in. The form posts the whole assessment once as `value`, and the server's `HX-Redirect` decides where the browser goes next, so an observer's flow can send them somewhere other than the results

**Carried from 13b**

- Reissuing or revoking a link deletes its invitation record (a new one is created on reissue), and removing a contact deletes it too. `ObserverResponse` has no link to an invitation yet (ticket 14b)
- The observer's pages know them by the `observer` cookie their claim set, which holds one claim: someone observing for two participants keeps the first through its own link only. A plain visit to an own link sets no cookie, so another site cannot plant a claim

## Answer

- The binding to the observer: ADR 0009
- Withdrawing by that binding, and the thank-you built here: carried to 15b
- The written part belonging to the same observer response: carried to 31a
