# 06: Scoring core and results page

**What to build:** The instrument and its scoring as a pure core, plus the results page a participant sees. The 36 items, both construct sets, named buckets with explicit seeds, and the frozen compositional scoring method are defined in the pathway document; the result is computed once from a stored sort answer, kept against its pathway version, and rendered with the content owner's descriptions and the validity disclaimer.

**Blocked by:** 03 (Response, autosave and first capture blocks)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [ ] The 36 items each load onto exactly one APEST(d) construct (Apostle, Prophet, Evangelist, Shepherd, Teacher, deacon) and exactly one PEP construct (Ponder, Ideate, Assess, Rally, Facilitate, Deliver); the item bank, descriptions, personas and validity disclaimer are migrated verbatim
- [ ] Buckets have named identifiers ordered from weakest to strongest, with seeds 10, 25, 45, 65 and 85 from weakest to strongest; the prototype's inverted integers never enter the new code
- [ ] The scoring method is named and frozen: each construct's raw value is the sum of its six item values, its percentage is its raw value over the grand total, rounded independently; ties fall back to declaration order
- [ ] The sort answer contract is defined and validated: all 36 items present, each with a valid bucket and a 0–100 value
- [ ] A result is computed once when the sort answer is submitted and stored against the pathway version; it is never recomputed by later versions
- [ ] The results page shows ranked APEST(d) and PEP profiles with descriptions and personas, an expandable list of item scores, and the validity disclaimer; PEP bars share a colour between tied scores
- [ ] Golden fixtures reproduce the prototype's output for fixed inputs, with the mapping (prototype bucket 1 is the strongest bucket) encoded once in the fixtures; an all-strongest and an all-weakest sort give the same profile; no test asserts percentages sum to 100
- [ ] The unbalanced APEST×PEP item matrix is ported unchanged and noted as content debt
