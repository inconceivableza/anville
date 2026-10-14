# 53: New look for card sorting and beyond

**What to build:** Every page beyond the hub and the wizard is brought into the look D1-48 set, so the whole app reads as one. The `hackathon-ui` branch's stylesheet already restyles every page, so this goes page by page and tidies what looks wrong. No page gets a new layout; the prototype has nothing beyond its homepage, wizard and hub, so each page follows its rules.

**Blocked by:** D5-52 (Workbook and Section 1 gates); D6-46 (The demo notice on every page); B1-42 (Observers skip fine-tuning quickly); A5-55 (Answer collection freezes once results are viewed)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** The instrument and results; Feedback from others; Operating and demonstrating

- [ ] The participant's pages: section pages, the card sort and fine-tuning, results, the comparison and the warning before collection freezes
- [ ] The observer's and coach's pages, and sign-up, sign-in, consent and the other account pages
- [ ] The homepage, keeping the words the branch took from the prototype, and with nothing on it that is not yet true (a newsletter, donations, a contact address that does not exist)
- [ ] Construct colours stay as they are, every page is readable at phone width, and no page is left in the old look

**Context**

- Split into 53a (the participant's pages) and 53b (the rest) if it outgrows one sitting
- B1-42 and A5-55 land on `main`, so the branch takes in `main` before this starts
