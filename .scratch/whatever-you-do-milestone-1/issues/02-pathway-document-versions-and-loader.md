# 02: Pathway document, versions and loader

**What to build:** The pathway document as a validated, versioned artefact. An author-edited document file is checked against a JSON Schema and a cross-reference linter, then loaded by a command into an immutable pathway version. A signed-in participant is shown the single published pathway automatically; with none published, or a pathway with sections but no content, they see the empty state.

**Blocked by:** 01 (Walking skeleton and access)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 1, 25 Sept)

- [ ] A pathway document covers content, instrument, measurement and presentation; identifiers for sections, blocks, items, constructs and buckets are stable and never positional
- [ ] Any text field accepts either a single string or a pair keyed by role (participant, observer); a blank observer text means the same as the participant's
- [ ] Validation is two passes (JSON Schema, then a linter for cross-references such as an item loading onto a construct that does not exist, or a gate clause naming an absent block) and returns errors that carry document paths
- [ ] Duplicate identifiers are rejected by the linter
- [ ] A load command creates an immutable pathway version stored with a content hash; loading the same content again does not create a duplicate
- [ ] An existing pathway version cannot be modified after creation (enforced, not just conventional)
- [ ] A signed-in participant is taken to the one published pathway automatically
- [ ] No published pathway shows the empty state; a pathway with sections but no content also renders as empty
- [ ] Editing one prompt in the document file and loading it again visibly changes the app for a participant who starts after the load; a participant already in progress stays on the version they started (spec default), so demonstrate with a fresh participant
- [ ] Nothing executable exists anywhere in the document format (ADR 0003)
- [ ] Pure-core tests cover validation, the linter, and role-specific text resolution
