# 04: Hub, locks, gates and explicit completion

**What to build:** The engine's spine. A hub derived from progress lists a track's sections with status and highlights the next step; sections lock by a per-section `requires` list, enforced by the server on every request; gates are lists of clauses each with its own message; a participant completes a section by an explicit action that the server re-checks. Includes the scripture reading block whose confirmation unlocks the activity beneath it.

**Blocked by:** 03 (Response, autosave and first capture blocks)

**Status:** resolved

**Parent:** whatever-you-do-milestone-1 spec (Demo 1, 25 Sept)

- [x] The hub is derived by the engine (status chips, locks, next-step banner); none of it is an authored block
- [x] A locked section stays locked when its address is entered directly; the server refuses or redirects
- [x] A gate is a list of clauses from a fixed set (a block has an answer, a count of entries (optionally only those with any content), a count of distinct values, a minimum text length, "every entry has a value for a field", and combinations), each with its own authored message shown when that clause fails
- [x] A gate is optional on a section; a section with none can be completed
- [x] Completing a section is an explicit participant action, enabled only when the gate passes, and re-checked by the server when submitted
- [x] The scripture reading block shows authored passages and a confirm control that opens the activity area beneath it
- [x] Progress counts only the interactive blocks reachable in the participant's track
- [x] Pure-core tests cover every clause type, combinations, and per-clause messages; journey tests cover locked-section refusal and refused completion when the gate fails

**Carried from 02**

- [x] The linter (`engine/document/lint.py`) refuses a gate clause naming a block in another section, and a clause that cannot apply to its block's type (for example `min_text_length` on rich text). Today it checks only that the block exists

**Carried from 03**

- [x] Decide where a scripture note lives. Ticket 03 gave rich text a `note` variant (rendered with the prototype's `scripture-note` class) so notes could be written before the scripture reading block existed. Once that block has its own note field, remove the variant or keep it for notes that are not attached to scripture, so authors do not have two ways to write the same thing
- [x] Gather each block type's definition in one place before adding the scripture reading block. Today a new type touches the schema (`pathway.schema.json`), `_TEXT_FIELDS` in `engine/views.py`, `ANSWER_SCHEMAS` and `_REFUSALS` in `engine/document/answers.py` (if it captures an answer), and a template in `engine/templates/engine/blocks/`. One registry per block type would keep these together

**Decisions taken while building**

- The `note` variant was removed from rich text rather than kept. Its only purpose was writing scripture notes before this block existed, and keeping both would be the two-ways-to-do-it the item warns about. The `.scripture-note` class stays, now used by the scripture reading block.
- A gate's clauses combine conjunctively, and every failing clause shows its message at once. The prototype showed one message at a time in a priority cascade (`timelineGateMessage`, docs/prototype/02-sections.md); showing all of them tells the participant what is actually left.
- A block in a locked section refuses an answer as well (403), not only the section page. Without it a participant could fill a section in by POSTing without ever opening it, which is the prototype's cosmetic lock in a new form.
- `entry_count`, `distinct_value_count` and `every_entry_has` are implemented and covered in the pure core, but no block type captures a list of entries yet, so the linter refuses them against every block that exists today. They become authorable with the contact list and timeline board (tickets 09 and 17).
- Completing is reversible, added beyond the ticket at Ryan's call. A completed section offers "Reopen this section", which removes that one completion record and touches no answer. Nothing cascades, and a section the participant completed is never locked again, whatever happens to what it required — otherwise the hub would call it complete, link to it and bounce them back. Changing an answer still never un-completes a section: with autosave, a gate re-evaluated on every keystroke would make the hub flicker and could re-lock a later section mid-sentence.

**Carried to a later ticket**

- Tracks. `engine/hub.py` has `track_sections()`, which is every section until a participant can choose (ticket 23). Everything that counts sections or blocks goes through it, so tracks change that one function.
