# 38: Results and comparison in words

**What to build:** The results page and the comparison draw each construct the way variant F does: a mark on one axis, with a dashed tick marking an even share, saying in words where it sits ("Leading", "Strong", "Present", "Less used") and, on the comparison, how others see it ("Others place this higher", "lower", "much the same"), in place of today's bars and percentages. On the comparison the marks are a single-person icon for the participant and a group icon for the observers. The charts change; nothing else on either page is dropped.

**Blocked by:** None (can start immediately)

**See also:** variant F of the throwaway prototype on branch `prototype/result-bars` (commit `11e3583`), chosen at the 2 Oct demo; view it on `/results/<block>/` and its comparison with `?variant=F` while DEBUG is on. Take its look and wording, not its template or code; never merge the branch.

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** The instrument and scoring; Observers (ADR 0005); Open content and product items

- [ ] Results page: each construct is a dot on F's axis in that construct's colour, with its band in words and no percentage; the ratio F shows in small type ("1.3×") is dropped. Scoring and the stored results are unchanged
- [ ] Comparison: on each construct's axis, the participant's mark is a single-person icon and the observers' a group icon, two colours only, the gap between them shaded, with both bands and the "higher, lower, much the same" words and no percentages. The icons replace the "You / Others (average)" legend; each mark is still named in text for screen readers
- [ ] Nothing is dropped: each construct's description and persona, "Show item scores", the disclaimer, the agreement line, the "See how the people who answered see this" expander (redrawn to match, its text giving each person's band in words), the gaps and their badges, the reflection prompts, the banner, the below-minimum state and the observer counts all stay
- [ ] The bands, their names and the "higher, lower, much the same" wording are authored in the pathway document; the prototype's bands are placeholders until the content owner gives real ones
- [ ] Decide here, with the content owner: whether "Show item scores" keeps its item values, and whether the gap badge keeps its points ("Others see more (+12)") or its words alone. Until decided, both stay as they are

**Context**

- Variant F as prototyped replaces each page's whole per-construct block, so it drops the results page's construct descriptions and the comparison's agreement line and distribution expander; that is the prototype being throwaway, not a decision
- The icons stand in for the circles so the drawing explains itself without a legend; two colours only, so the comparison stays readable
- The scoring method is frozen (spec, The instrument and scoring); this ticket changes only how results are drawn and worded
