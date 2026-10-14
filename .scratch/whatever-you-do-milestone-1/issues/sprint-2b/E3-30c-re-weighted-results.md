# 30c: Re-weighted results

**What to build:** The tie-break's answers re-weight the close constructs, so the participant's results say something: either the framework now has a clear leader, or they are told plainly that its leaders are genuinely balanced. A participant tied on both frameworks is told they are a generalist.

**Blocked by:** E2-30b (The tie-break after the sort)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** The instrument and scoring; The instrument and results; Open content and product items

- [ ] Re-weighting is a second named scoring method beside the compositional score (ADR 0003), so the frozen method and its fixtures stay as they are. The re-weighted result is stored beside the sort's, never in its place
- [ ] When the choices go in a circle, the result says the constructs are genuinely balanced rather than forcing a winner
- [ ] The results page shows the re-weighted result, and how the tie-break changed it
- [ ] A participant tied on both frameworks sees, on their results, that they are a generalist, in wording authored in the pathway document
- [ ] The comparison sets the participant's re-weighted result beside the observers', so it agrees with their results page. Observers have no tie-break, so theirs are their sorts as sent

**Context**

- Prototype reference: `tiebreaker-prototype-v2.html` in Prototypes for reference, for the re-weighting and the balanced outcome
- On a framework the participant has broken, the re-weighted result replaces the compositional score's fallback to declaration order
