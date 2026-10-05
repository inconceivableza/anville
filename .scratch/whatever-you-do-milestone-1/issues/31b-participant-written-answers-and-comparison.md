# 31b: The participant's written answers and the comparison

**What to build:** The participant answers the same six written questions as their observers, in their own wording, and sees their answer beside the observers' for each question, without names and shuffled per question. Three best qualities get their own comparison: words both sides chose, words only observers chose, and words only the participant chose.

**Blocked by:** 09 (Section 1 and the Strengths assessment section), 16a (The comparison, side by side), 31a (The observer's written questions)

**See also:** `Prototypes for reference/qualitative-strengths-prototype.html`, the content owner's prototype: its participant questions (`P_QS`) and its "Notes for implementation". Its insight boxes ("You said impatience. Three of them said some version of confidence") are hand-written sample text; only the word comparison can be computed.

**Status:** ready-for-agent

**Sprint:** 3 or later, with 31a

**Spec:** Observers (ADR 0005); Open content and product items; Testing Decisions

**Decide before building**

- [ ] Whether the participant's written answers and their comparison are still wanted in the app, or live in the PDF workbook instead (ticket 40)
- [ ] Whether observers' answers are released in batches, covering the comparison's numbers and distribution strip (16a, 16b) too; the batch size and what the participant sees while answers wait are already set (spec, Open content and product items)
- [ ] Whether observers' written answers are ever saved before sending, leaning never (spec, Open content and product items, "Observer autosave")
- [ ] The prototype's open points: whether observers see the participant's answers afterwards, whether "what do they struggle with" needs a softer frame, whether the participant sees how many observers skipped each question, and the synonym list for the word comparison

**Build**

- [ ] The participant answers all six in participant wording, all required, each field autosaving, three best qualities as three single words; this sits with the Strengths assessment work (ticket 09)
- [ ] For each question, the participant sees their answer beside the observers', without names and shuffled per question
- [ ] No observer's written answer appears until at least three observers have sent the written part with at least one answer in it, counted over the whole part, not per question, on the page or through any other request (ADR 0008)
- [ ] The word comparison normalises words (case, simple stemming, an authored synonym map), groups them three ways, and counts how many observers chose each; words chosen only by observers get the most weight

**Carried from 27**

- [ ] The coach's link shows the comparison through the participant's own comparison body once they consent (ADR 0011), so written answers put there reach the coach too. Decide whether the coach sees them; if so, the observers' notice says so, and if not, keep them out of the coach's view
