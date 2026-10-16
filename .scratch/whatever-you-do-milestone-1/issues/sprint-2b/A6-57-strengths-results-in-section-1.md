# 57: Strengths results in Section 1

**What to build:** Once the participant has their results, Section 1 shows them in full as a block of their own, right after the Strengths assessment's link, so they can see them again without opening the Strengths assessment. The hub is unchanged.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 2b (12–16 Oct)

**Spec:** The instrument and results; Implementation Decisions › The instrument and scoring; Engine: sections, tracks, gates, progress

- [x] Once the participant has results, Section 1 shows both frameworks in words, drawn exactly as the results page draws them, re-weighted where a tie-break was answered, and with the generalist's or the broken framework's wording where the results page has it
- [x] Before then the block shows nothing of its own, and the Strengths assessment's link stays as it is, including for a participant who has sorted but not yet answered the tie-break
- [x] Under the results, "Compare with how others see you →" does what the results page's button does: it records the visit, so the warning before answer collection freezes still comes first
- [x] Showing it never sends the participant back through the sort or the tie-break, and stores nothing the results page would not
- [x] It is a block in Whatever You Do's Section 1 only: the faithful port keeps the original prototype, which has no such block, and the drift test sets it aside, as it does the next step and photos

**Carried from fix-2**

- Developer's calls, 16 Oct: the full results rather than a summary and a link; built in sprint 2b
- The block draws its own content (CODING_STANDARDS.md, Locality): the results page and the block share one way of drawing the results, rather than the view deciding how the block looks
