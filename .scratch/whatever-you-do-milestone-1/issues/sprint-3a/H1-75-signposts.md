# 75: Section and comparison links become signposts

**What to build:** The section link and comparison link block types are renamed to the glossary's section signpost and comparison signpost, in the document, the engine, the tests and the docs. Nothing a participant, observer or coach sees changes, and every pathway version loaded before the rename keeps working without being rewritten.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 3a (from 20 Oct)

**Spec:** The pathway document and versions; Blocks

- [x] Both pathway documents use the new block type names, and the schema and linter accept only those in a document being loaded
- [x] A pathway version stored under the old names still draws, gates, holds back and records "Viewed" exactly as before, and its row is never rewritten
- [x] Code names, templates, styles, docstrings and comments say signpost where they now say section link or comparison link
- [x] Test names and helpers follow the same words, and the suite passes before and after unchanged in what it asserts
- [x] The README and spec use the new words, and the glossary needs no change
