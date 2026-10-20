# 67a: "How others see you" card in Section 1

**What to build:** Under Section 1's Strengths assessment card, a card leads to the comparison and says where it stands: waiting for answers, ready to view, or viewed. Its button is the results page's "Compare with how others see you →" press, warning before collection freezes exactly as that one does. "Viewed" means seen with enough answers in, which ticket 68 relies on.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 3a (from 20 Oct)

**Spec:** Blocks; Observers (ADR 0005)

- [x] Once there is a result, Section 1 shows the card under the Strengths assessment card; before then it shows nothing
- [x] Its status reads "Waiting for answers ({answered} of {minimum})" below the minimum, "Ready to view" at or above it, and "Viewed" once the participant has pressed it with the minimum in
- [x] A press below the minimum shows the explanation as now and leaves the status unchanged
- [x] The press is a POST through the same freeze warning as the results page's, and works without JavaScript
- [x] The card is an authored block, placed in *Whatever You Do* only; the linter refuses one naming anything but a sort

**Context**

- Settles the comparison card the developer deferred on 19 Oct (`.claude/findings.md`), so ticket 41's navigation work no longer waits on it
