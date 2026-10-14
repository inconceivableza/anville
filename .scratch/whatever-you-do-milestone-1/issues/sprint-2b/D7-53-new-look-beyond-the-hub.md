# 53: New look for card sorting and beyond

**What to build:** Every page beyond the hub and the wizard is brought into the look D1-48 set, so the whole app reads as one. The stylesheet merged from the `hackathon-ui` branch in D1-48 already restyles every page, so this goes page by page and tidies what looks wrong. No page gets a new layout; the prototype has nothing beyond its homepage, wizard and hub, so each page follows its rules.

**Blocked by:** D6-46 (The demo notice on every page); B1-42 (Observers skip fine-tuning quickly); A5-55 (Answer collection freezes once results are viewed)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** The instrument and results; Feedback from others; Operating and demonstrating

- [ ] The participant's pages: section pages, the card sort and fine-tuning, results, the comparison and the warning before answer collection freezes
- [ ] The observer's and coach's pages, and sign-up, sign-in, consent and the other account pages
- [ ] The homepage, keeping the words the hackathon took from the prototype, v3's where its earlier copy differs, and with nothing on it that is not yet true (a newsletter, donations, a contact address that does not exist)
- [ ] Construct colours stay as they are, every page is readable at phone width, and no page is left in the old look

**Carried from 48**

- [ ] One set of button rules: D1-48 shaped `.btn` like the prototype's pill in the stylesheet alone; each page's markup moves to `.pill` and `.pill.ghost`
- [ ] One name per colour: the stylesheet keeps Anville's names beside the prototype's for the same values (`--gold` and `--green-deep`, `--white` and `--paper`, `--deep`, `--footer` and `--brown`, `--ink-muted` and `--muted`)
- [ ] Class names from the prototype that say nothing (`.n`, `.ar`, `.l`, `.r`, `.lbl`, `.tr`, `.b`, `.go`) get names that do
- [ ] The homepage's tests pin its copy ("Begin your journey" three times, its taglines), which `CODING_STANDARDS.md` rules out; once its words are settled they test behaviour instead: where each "Begin" leads, that nothing points at a placeholder
- Whether pages beyond the prototype's three take its deep brown frame, as D2-49 gives the hub, is this ticket's call

**Context**

- Split into 53a (the participant's pages) and 53b (the rest) if it outgrows one sitting
