# 30a: Tie detection and pairs

**What to build:** From a participant's sort, the engine tells whether a framework's top constructs are too close to call and, if so, plans the "Which is more true of you?" pairs that would separate them. Nothing is shown yet; this is the decision and the plan that 30b puts in front of the participant.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** The instrument and scoring; The pathway document and versions

- [ ] A framework is tied when one or more other constructs are within a threshold of its leader (4 percentage points of the rounded percents by default), and at most the top four enter the tie-break. The threshold, the cluster size and the question budget (10 by default) are set in the pathway document
- [ ] Only a participant tied on exactly one framework gets pairs. One tied on both is a generalist and gets none; one tied on neither gets none
- [ ] Pairs are always within the tied framework, never across APEST(d) and PEP. Pairs among the top-ranked constructs survive trimming to the budget first, and a second round with different statements may fill what is left of it
- [ ] Three statements per construct, 36 in all, are authored content in the pathway document, taken from the content owner's prototype and separate from the 36 sort items
- [ ] The tie detection and the planning are pure functions of a result and the document, with no request or database

**Context**

- Prototype reference: `tiebreaker-prototype-v2.html` in Prototypes for reference, the content owner's prototype and the reference for behaviour and statements. Its handling of two tied frameworks (a shared budget, alternating questions) is not built, since a participant tied on both is told they are a generalist
- The faithful port does not take the statements, since the tie-break is not in the original prototype; the drift test sets them aside
