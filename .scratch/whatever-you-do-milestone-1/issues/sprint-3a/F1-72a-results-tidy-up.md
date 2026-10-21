# 72a: Results tidy-up from the code review

**What to build:** The tidy-ups the sprint 2b finalisations code review left as notes in the results code, with nothing a participant sees changing: the tie-break's outcome switches gathered in one place, stored shares read through one helper, and the framework drawing given fewer parameters.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 3a (from 20 Oct)

**Spec:** The instrument and scoring

- [x] Each tie-break outcome is decided once and read from there, not switched on in several places
- [x] Shares stored as text are turned into numbers in one place; what is stored does not change and no stored result is migrated
- [x] Drawing one framework takes a small number of arguments, grouped by what they describe
- [x] Every results page, comparison and golden sort reads exactly as before, and the whole suite passes unchanged
