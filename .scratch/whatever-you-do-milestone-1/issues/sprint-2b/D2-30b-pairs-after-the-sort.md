# 30b: The tie-break's pairs after the sort

**What to build:** A participant whose sort leaves one framework too close to call answers "Which is more true of you?" pairs that would separate its leaders, straight after sending their sort and before seeing their results. A participant with nothing to break goes straight to their results, as today.

**Blocked by:** D1-30a (Tie detection and the generalist)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** The instrument and scoring; The instrument and results; The pathway document and versions

- [ ] Pairs are always within the tied framework, never across APEST(d) and PEP. Pairs among the top-ranked constructs survive trimming to the question budget (10 by default, set in the pathway document) first, and a second round with different statements may fill what is left of it. The planning is a pure function of a result and the document
- [ ] Three statements per construct, 36 in all, are authored content in the pathway document, taken from the content owner's prototype and separate from the 36 sort items
- [ ] Sending a sort that 30a marks for the tie-break leads to it; any other sort leads to the results, as today. Observers are never offered one
- [ ] Each pair shows one statement for each of its two constructs, in random left-right order, with a quiet label naming the framework, and "Neither fits — skip"
- [ ] The answers are stored beside the sort's stored result, which is kept as it is. A participant who leaves part-way comes back to the next unanswered pair, and once every pair is answered or skipped goes on to their results

**Carried from 30a**

- 30a's tie detection gives, from the stored result and the document, each tied framework's constructs that enter the tie-break (leader first, at most the cluster size) and whether the participant is marked, a generalist or neither. Nothing about it is stored
- The threshold and cluster size are the document's tie-break settings, beside which the budget belongs. The drift test already sets those settings and the generalist's wording aside, so the statements can be set aside in the same place

**Context**

- Prototype reference: `tiebreaker-prototype-v2.html` in Prototypes for reference, for the pair screen and the statements
- Observers are left out to keep sending quick for them (B1B-42)
- The faithful port does not take the statements, since the tie-break is not in the original prototype; the drift test sets them aside
- Reshaped on 15 Oct: planning the pairs moved here from 30a
