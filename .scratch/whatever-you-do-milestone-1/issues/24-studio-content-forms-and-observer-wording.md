# 24: Studio content forms and observer wording

**What to build:** A studio face a non-technical author can use unaided: forms, generated from the document's schema, for the text-bearing parts of the pathway (prompts, scripture, item wording, lens prompts, gate messages), including a per-item "for observers" field and a linter warning that catches second-person wording.

**Blocked by:** 12 (Studio: preview)

**Status:** ready-for-agent

**Sprint:** 3 or later

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** second. If time runs short, authors use the raw JSON editor alone.

- [ ] Forms are generated from the document's JSON Schema, so this ticket assumes the schema has stabilised; changes to the document's shape after this point mean regenerating forms, not hand-editing them
- [ ] Authors can edit prompts, scripture passages, item wording, lens prompts and gate messages without touching JSON, and the result is saved into the draft
- [ ] Each item has an optional "for observers" wording field; blank means the same as the participant's
- [ ] The linter warns when text an observer will see says "you", "your" or "yours" and has no observer wording (it would have caught the four affected items)
- [ ] Each gate is shown as its clauses with a message per clause
- [ ] Saved forms preview correctly (ticket 12) and publish through the normal loop (ticket 11)
- [ ] Structural editing (adding, removing, reordering sections and blocks) is out of scope for this milestone
