# 38: Results and comparison in words

**What to build:** The results page and the comparison show each construct as a mark on one axis with an even share marked, and say in words where it sits ("Leading", "Strong", "Present", "Less used") and how others see it ("others place this higher", "much the same"), with no percentages. This is variant F from the prototype branch `prototype/result-bars`, chosen at the 2 Oct demo.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** The instrument and scoring; Observers (ADR 0005); Open content and product items

- [ ] Neither page shows a percentage or points; scoring and the stored results are unchanged (`compositional_share` stays frozen), only what is drawn and said
- [ ] The bands, their names and the comparison's "higher, lower, much the same" wording are authored in the pathway document; the prototype's bands are placeholders until the content owner gives real ones
- [ ] On the comparison, the participant is one colour with a single-person icon and the observers another colour with a group icon, two colours only; the results page may keep its colour per construct
- [ ] Nothing below the observer minimum shows, as before (16a), and the comparison's gaps, agreement and prompts (16b) still read correctly in words
- [ ] Decide here: whether the results page's item-level "show scores" expander stays now that the page has no numbers

**Context**

- The demo's reason: participants in the paper trial felt "crap at everything" from the numbers, since few people are strongly skewed, and the percents are a share of a total rather than a measure
- The prototype branch is throwaway; take the drawing and wording from it, not its code
