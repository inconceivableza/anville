# 30b: The tie-break after the sort

**What to build:** A participant whose sort leaves one framework too close to call answers its pairs straight after sending their sort, before seeing their results. A participant with nothing to break goes straight to their results, as today.

**Blocked by:** E1-30a (Tie detection and pairs)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** The instrument and scoring; The instrument and results

- [ ] Sending a sort that 30a finds tied leads to the tie-break; any other sort leads to the results, as today
- [ ] Each pair shows one statement for each of its two constructs, in random left-right order, with a quiet label naming the framework, and "Neither fits — skip"
- [ ] The answers are stored beside the sort's stored result, which is kept as it is. A participant who leaves part-way comes back to the next unanswered pair
- [ ] Observers are never offered a tie-break: an observer's sort is sent as today
- [ ] Once every pair is answered or skipped, the participant goes on to their results

**Context**

- Prototype reference: `tiebreaker-prototype-v2.html` in Prototypes for reference, for the pair screen
- Observers are left out to keep sending quick for them (B1-42)
