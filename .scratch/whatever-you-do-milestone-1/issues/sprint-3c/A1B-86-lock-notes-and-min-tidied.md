# 86: Lock notes, the minimum and section names, each worked out in one place

**What to build:** A prefactor before the six-section split and the lock-note button. The minimum number of people a section's gate asks for, the "Section N" wording and the lock notes are each worked out by one rule, so ticket 87 and ticket 97 change one place each. Two edge cases the sprint 3b code review found are fixed on the way. Otherwise participants see nothing change.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Engine: sections, tracks, gates, progress

- [x] Every lock note, gate message and phrase for what finishing a section takes reads exactly as before, in both pathways
- [x] The minimum a section's gate asks for people is found and filled in for `{min}` by one rule that the hub, the gate messages and the pathway's loader share, and "Section 1" / "Sections 1 and 2" come from one rule too
- [x] A lock note is always the same kind of thing, built from named plain and italic pieces, never sometimes plain text
- [x] A phrase holding a placeholder the engine does not know (a typo such as `{titel}`) is refused when the pathway is loaded, saying where; the refusal of another number beside `{min}` tells the author to write `{min}` for the minimum and any other number in words
- [x] Sections sharing a phrase are named together in the order of the requirements, never moved ahead of sections between them
- [x] The loader's helper for other numbers has a docstring, as its neighbours do

**Context**

- From the sprint 3b code review, 26 Oct
