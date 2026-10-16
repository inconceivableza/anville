# 53a: One set of styles

**What to build:** The stylesheet merged from the `hackathon-ui` branch in A0-48 is tidied so the pages restyled after it build on one set of rules: one for buttons, one name for each colour, and class names that say what they are. No page looks any different. The page-by-page look is 53b and 53c.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 2b (12–16 Oct)

**Spec:** Operating and demonstrating

- [x] No page looks any different, at desktop or phone width

**Carried from 48**

- [x] One set of button rules: A0-48 shaped `.btn` like the prototype's pill in the stylesheet alone; each page's markup moves to `.pill` and `.pill.ghost`
- [x] One name per colour: the stylesheet keeps Anville's names beside the prototype's for the same values (`--gold` and `--green-deep`, `--white` and `--paper`, `--deep`, `--footer` and `--brown`, `--ink-muted` and `--muted`)
- [x] Class names from the prototype that say nothing (`.n`, `.ar`, `.l`, `.r`, `.lbl`, `.tr`, `.b`, `.go`) get names that do
- [x] The homepage's tests pin its copy ("Begin your journey" three times, its taglines), which `CODING_STANDARDS.md` rules out; they test behaviour instead: where each "Begin" leads, that nothing points at a placeholder

**Context**

- Split from ticket 53 on 15 Oct, so the clean-up lands before the pages are gone through one by one
