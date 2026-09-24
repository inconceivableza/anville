# 06: Scoring core and results page

**What to build:** The instrument and its scoring as a pure core, plus the results page a participant sees. The 36 items, both construct sets, named buckets with explicit seeds, and the frozen compositional scoring method are defined in the pathway document; the result is computed once from a stored sort answer, kept against its pathway version, and rendered with the content owner's descriptions and the validity disclaimer.

**Blocked by:** 03 (Response, autosave and first capture blocks)

**Status:** claimed

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [ ] The 36 items each load onto exactly one APEST(d) construct (Apostle, Prophet, Evangelist, Shepherd, Teacher, deacon) and exactly one PEP construct (Ponder, Ideate, Assess, Rally, Facilitate, Deliver); the item bank, descriptions, personas and validity disclaimer are migrated verbatim
- [x] Buckets have named identifiers ordered from weakest to strongest, with seeds 10, 25, 45, 65 and 85 from weakest to strongest; the prototype's inverted integers never enter the new code
- [x] The scoring method is named and frozen: each construct's raw value is the sum of its six item values, its percentage is its raw value over the grand total, rounded independently; ties fall back to declaration order
- [x] The sort answer contract is defined and validated: all 36 items present, each with a valid bucket and a 0–100 value
- [x] A result is computed once when the sort answer is submitted and stored against the pathway version; it is never recomputed by later versions
- [ ] The results page shows ranked APEST(d) and PEP profiles with descriptions and personas, an expandable list of item scores, and the validity disclaimer; PEP bars share a colour between tied scores
- [x] Golden fixtures reproduce the prototype's output for fixed inputs, with the mapping (prototype bucket 1 is the strongest bucket) encoded once in the fixtures; an all-strongest and an all-weakest sort give the same profile; no test asserts percentages sum to 100
- [x] The unbalanced APEST×PEP item matrix is ported unchanged and noted as content debt

## Comments

- First step: the scoring method (`compositional_share`), golden fixtures generated from the prototype's own `computeAll()`, and the 36 items, buckets and frameworks in `pathways/whatever-you-do.json`. The first criterion is only partly met: items and loadings are in, while descriptions, personas and the disclaimer arrive with the results page. The content debt is pinned by `test_the_unbalanced_item_matrix_is_ported_unchanged`.
- Second step: the sort answer contract. `answer_from_form` now takes the document, since a sort is valid only against its own pathway version's items and buckets. A `sort_assessment` block has no template yet; the next step adds one.
- Third step: `Result`, one per sort block per response, stored with the answer in one transaction. A second sort is refused with 409 and the database constraint backs that up. The sort block renders a plain placeholder until ticket 07's widget.
