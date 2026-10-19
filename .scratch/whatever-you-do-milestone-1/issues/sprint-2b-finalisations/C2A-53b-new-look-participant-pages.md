# 53b: New look for the participant's pages

**What to build:** Every page a participant sees beyond the hub and the wizard is brought into the look A0-48 set, so the whole app reads as one. The stylesheet merged from the `hackathon-ui` branch already restyles every page, so this goes page by page and tidies what looks wrong. No page gets a new layout; the prototype has nothing beyond its homepage, wizard and hub, so each page follows its rules. The observer's, coach's and account pages are 53c.

**Blocked by:** C1A-53a (One set of styles); C1B-46 (The demo notice on every page); A5A-52 (Workbook and Section 1 gates); B1B-42 (Observers skip fine-tuning quickly); B2B-55 (Answer collection freezes once results are viewed)

**Status:** claimed

**Sprint:** 2b (continued from 19 Oct)

**Spec:** The instrument and results; Operating and demonstrating

- [x] Section pages, the Workbook's page, and the hub's messages for a locked section
- [x] The card sort and fine-tuning, which the observer's sort shares
- [x] Results, the comparison and the warning before answer collection freezes, with the construct colours as they are
- [x] Every one of these pages is readable at phone width, and none is left in the old look
- [x] Every signed-in participant page takes the hub's deep brown frame, as A1-49a gives the hub: the sections, results, the comparison and the assessment

**Context**

- Split from ticket 53 on 15 Oct
- The frame is the developer's call, 19 Oct: the signed-in participant's pages take it; the observer's, coach's and account pages stay plain cream (53c)
- The tie-break's pair screen (D2-30b) is built in this look whichever lands first
