# 04: Hub, locks, gates and explicit completion

**What to build:** The engine's spine. A hub derived from progress lists a track's sections with status and highlights the next step; sections lock by a per-section `requires` list, enforced by the server on every request; gates are lists of clauses each with its own message; a participant completes a section by an explicit action that the server re-checks. Includes the scripture reading block whose confirmation unlocks the activity beneath it.

**Blocked by:** 03 (Response, autosave and first capture blocks)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 1, 25 Sept)

- [ ] The hub is derived by the engine (status chips, locks, next-step banner); none of it is an authored block
- [ ] A locked section stays locked when its address is entered directly; the server refuses or redirects
- [ ] A gate is a list of clauses from a fixed set (a block has an answer, a count of entries (optionally only those with any content), a count of distinct values, a minimum text length, "every entry has a value for a field", and combinations), each with its own authored message shown when that clause fails
- [ ] A gate is optional on a section; a section with none can be completed
- [ ] Completing a section is an explicit participant action, enabled only when the gate passes, and re-checked by the server when submitted
- [ ] The scripture reading block shows authored passages and a confirm control that opens the activity area beneath it
- [ ] Progress counts only the interactive blocks reachable in the participant's track
- [ ] Pure-core tests cover every clause type, combinations, and per-clause messages; journey tests cover locked-section refusal and refused completion when the gate fails

**Carried from 02**

- [ ] The linter (`engine/document/lint.py`) refuses a gate clause naming a block in another section, and a clause that cannot apply to its block's type (for example `min_text_length` on rich text). Today it checks only that the block exists

**Carried from 03**

- [ ] Decide where a scripture note lives. Ticket 03 gave rich text a `note` variant (rendered with the prototype's `scripture-note` class) so notes could be written before the scripture reading block existed. Once that block has its own note field, remove the variant or keep it for notes that are not attached to scripture, so authors do not have two ways to write the same thing
- [ ] Gather each block type's definition in one place before adding the scripture reading block. Today a new type touches the schema (`pathway.schema.json`), `_TEXT_FIELDS` in `engine/views.py`, `ANSWER_SCHEMAS` and `_REFUSALS` in `engine/document/answers.py` (if it captures an answer), and a template in `engine/templates/engine/blocks/`. One registry per block type would keep these together
