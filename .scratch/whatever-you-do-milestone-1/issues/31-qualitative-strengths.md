# 31: Qualitative strengths

**What to build:** The written half of the strengths work. The participant and their observers answer the same six written questions, phrased for each side, and the participant sees their own answers beside the observers', shuffled so no observer's answers can be linked across questions. Three best qualities, given as three single words, get their own comparison: words both sides chose, words only observers chose, and words only the participant chose.

**Blocked by:** 09 (Section 1 and the Strengths assessment section), 14b (Observer responses and seeding), 15 (Observer questionnaire), 16 (Comparison screen)

**See also:** `Prototypes for reference/qualitative-strengths-prototype.html`, the content owner's prototype. Its insight boxes ("You said impatience. Three of them said some version of confidence") are hand-written sample text; only the word comparison can be computed.

**Status:** ready-for-agent

**Sprint:** 2 (ends 8 Oct, for the 9 Oct tech showcase)

**Parent:** whatever-you-do-milestone-1 spec (Observers, ADR 0005)

**Decide before building**

- [ ] Supersede ADR 0005's "written answers are stored but never shown to the participant" with a new ADR. The content owner's safeguard is to shuffle the order in which answers are shown, because in the paper trial a participant de-anonymised critical feedback by matching one person's answers across questions. Record the reasoning and what still protects observers
- [ ] How many observers must have answered before any written answer is shown. ADR 0005's minimum of three applies to numbers; decide whether quotes wait for it too
- [ ] Whether observers submit in two stages, as in the prototype (the sort first, then the written part, now or later), which changes "each token accepts one submission" (ADR 0005, spec Observers)
- [ ] What "Send me a link for later" becomes while no email is sent: the observer's own claimed link (ticket 13b) stays valid for its lifetime, and no reminder is sent. A saved draft is reachable only through that claimed link, never the participant's copy, or the participant could read one observer's written answers before the shuffle hides whose they are
- [ ] The new ADR records that the participant holds a copy of every observer's link, what the claim on first use (ticket 13b) protects, and what it doesn't: a participant can tell whether a given person has started or answered, and could answer in their place; likewise the coach's link (ticket 13c), where the participant could accept the commitments on the coach's behalf
- [ ] The prototype's own open points: whether observers see the participant's answers afterwards, whether "what do they struggle with" needs a softer frame, whether the participant sees how many observers skipped each question, and the synonym list for the word comparison
- [ ] What ticket 15 left for this ticket (see its "decide before building" item)

**Build**

- [ ] The six questions (most energised, three best qualities, one skill to grow or add, one area of character, biggest change in recent years, work they struggle with) are authored content, with participant and observer wording
- [ ] The participant answers all six, which are required; this sits with the Strengths assessment work (ticket 09), and each field autosaves
- [ ] Observers may skip any of the six; partial answers are still sent
- [ ] Three best qualities are three single-word inputs
- [ ] The participant sees their answer beside the observers' for each question, with observers' answers shuffled per question and never attributed
- [ ] The word comparison normalises words (case, simple stemming, an authored synonym map) and counts how many observers chose each; words chosen only by observers get the most weight
- [ ] The observer privacy notice (ticket 13b) says what the participant will see of their written answers
- [ ] Journey tests cover shuffling (no stable order across questions), suppression below the agreed minimum, skipped observer answers, and that no answer is attributed
