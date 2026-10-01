# 31b: The participant's written answers and the comparison

**What to build:** The participant answers the same six written questions as their observers, in their own wording, and sees their answer beside the observers' for each question, without names and shuffled per question. Three best qualities get their own comparison: words both sides chose, words only observers chose, and words only the participant chose.

**Blocked by:** 09 (Section 1 and the Strengths assessment section), 16 (Comparison screen), 31a (The observer's written questions)

**See also:** `Prototypes for reference/qualitative-strengths-prototype.html`, the content owner's prototype: its participant questions (`P_QS`) and its "Notes for implementation". Its insight boxes ("You said impatience. Three of them said some version of confidence") are hand-written sample text; only the word comparison can be computed.

**Status:** ready-for-agent

**Sprint:** 2 (ends 8 Oct, for the 9 Oct tech showcase)

**Spec:** Observers (ADR 0005); Open content and product items; Testing Decisions

**Decide before building**

- [ ] Whether observers' answers are released in batches, covering the comparison's numbers (16) too (spec, Open content and product items)
- [ ] Whether observers' written answers are ever saved before sending, leaning never (spec, Open content and product items, "Observer autosave")
- [ ] The prototype's open points: whether observers see the participant's answers afterwards, whether "what do they struggle with" needs a softer frame, whether the participant sees how many observers skipped each question, and the synonym list for the word comparison

**Build**

- [ ] The participant answers all six in participant wording, all required, each field autosaving, three best qualities as three single words; this sits with the Strengths assessment work (ticket 09)
- [ ] For each question, the participant sees their answer beside the observers', without names and shuffled per question
- [ ] No observer's written answer appears until at least three observers have sent the written part with at least one answer in it, counted over the whole part, not per question, on the page or through any other request (ADR 0008)
- [ ] The word comparison normalises words (case, simple stemming, an authored synonym map), groups them three ways, and counts how many observers chose each; words chosen only by observers get the most weight
