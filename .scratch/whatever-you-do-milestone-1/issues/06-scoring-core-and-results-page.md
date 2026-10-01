# 06: Scoring core and results page

**What to build:** The instrument and its scoring as a pure core, plus the results page a participant sees. The 36 items, both construct sets, named buckets with explicit seeds, and the frozen compositional scoring method are defined in the pathway document; the result is computed once from a stored sort answer, kept against its pathway version, and rendered with the content owner's descriptions and the validity disclaimer.

**Blocked by:** 03 (Response, autosave and first capture blocks)

**Status:** resolved

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [x] The 36 items each load onto exactly one APEST(d) construct (Apostle, Prophet, Evangelist, Shepherd, Teacher, deacon) and exactly one PEP construct (Ponder, Ideate, Assess, Rally, Facilitate, Deliver); the item bank, descriptions, personas and validity disclaimer are migrated verbatim
- [x] Buckets have named identifiers ordered from weakest to strongest, with seeds 10, 25, 45, 65 and 85 from weakest to strongest; the prototype's inverted integers never enter the new code
- [x] The scoring method is named and frozen: each construct's raw value is the sum of its six item values, its percentage is its raw value over the grand total, rounded independently; ties fall back to declaration order
- [x] The sort answer contract is defined and validated: all 36 items present, each with a valid bucket and a 0–100 value
- [x] A result is computed once when the sort answer is submitted and stored against the pathway version; it is never recomputed by later versions
- [x] The results page shows ranked APEST(d) and PEP profiles with descriptions and personas, an expandable list of item scores, and the validity disclaimer; PEP bars share a colour between tied scores
- [x] Golden fixtures reproduce the prototype's output for fixed inputs, with the mapping (prototype bucket 1 is the strongest bucket) encoded once in the fixtures; an all-strongest and an all-weakest sort give the same profile; no test asserts percentages sum to 100
- [x] The unbalanced APEST×PEP item matrix is ported unchanged and noted as content debt

## Comments

- First step: the scoring method (`compositional_share`), golden fixtures generated from the prototype's own `computeAll()`, and the 36 items, buckets and frameworks in `pathways/whatever-you-do.json`. The first criterion is only partly met: items and loadings are in, while descriptions, personas and the disclaimer arrive with the results page. The content debt is pinned by `test_the_unbalanced_item_matrix_is_ported_unchanged`.
- Second step: the sort answer contract. `answer_from_form` now takes the document, since a sort is valid only against its own pathway version's items and buckets. A `sort_assessment` block has no template yet; the next step adds one.
- Third step: `Result`, one per sort block per response, stored with the answer in one transaction. A second sort is refused with 409 and the database constraint backs that up. The sort block renders a plain placeholder until ticket 07's widget.
- Fourth step: the results page at `/results/<block_id>/`, with descriptions, personas and the disclaimer now in the document (so the first criterion is met in full). Colours stay in the stylesheet: the document names a tone per construct, PEP bars are coloured by rank, and bars are SVG so no template needs an inline style.
- Review (`/code-review` over the four commits): a pathway with a sort but no buckets, items, frameworks or scoring method passed validation and then failed on the participant's page; the linter now refuses it. The refusal wording now says "item" and "bucket" as the glossary does. Test helpers shared with the prototype moved to `tests/prototype.py`.

## Answer

Built in `engine/document/scoring.py` (the frozen `compositional_share` method), `engine/document/blocks.py` (the `sort_assessment` block and its answer contract), `engine/models.py` (`Result`, migration `engine/0006`) and `engine/results.py` with `engine/templates/engine/results.html` (the page at `/results/<block_id>/`). `pathways/whatever-you-do.json` now holds the instrument, both frameworks, the scoring method and the results wording; it does not place the sort, which is ticket 09. The README's "Scoring and results" section describes the behaviour.

The golden fixtures are the prototype's own output: `tests/core/golden/prototype_scoring.mjs` reads its item bank and `computeAll()` out of the prototype file and runs them in Node. They caught two things a port by eye would miss: rounding is JavaScript's half-up, and ranking is by rounded percent, so Rally (raw 215) ranks above Deliver (raw 225) when both round to 13.

Decisions made along the way, with the developer:

- The headings keep the prototype's emoji word for word, "✨ Your APEST(d) Profile" and "⚡ Your Professional Energy Profile (PEP)". Here ✨ is content, not a provenance mark.
- The title is "{name}, here’s your profile", and `{name}` is the Django username, which allauth takes from the part of the email before the @. Accounts hold no name yet.
- Colours live in the stylesheet, because templates may hold no raw colour and no inline style (`tests/core/test_styles.py`). A construct names a tone from a fixed list, and a framework's bars are coloured by tone or by rank. Bars are SVG sized by attribute.
- The content debt (the unbalanced APEST×PEP matrix and the compositional score) is recorded for the content owner in the spec's Further Notes, "Open content and product items", and pinned by `test_the_unbalanced_item_matrix_is_ported_unchanged`.

Notes for a particular ticket are carried into it, under "Carried from 06":

- 07: the contract the widget sends, landing on the results page after a sort, and the PEP bar minimum
- 09: Section 1's gate cannot yet name a block in another section; decide how before building it
- 11: the results page reads the newest response, which matters if publishing ever moves a participant to a later version
- 16a: the prototype's second colour set
- 23: the "Want to go deeper?" links and the bold "Important:", once rich text can carry them

Retake is out of scope for this milestone, so its note (the unique constraint it must replace) is in the spec, beside the retake decision under "Responses, answers and results".
