# 40: The workbook step

**What to build:** Sections 2–4 leave the hub, and in their place a Workbook step offers the content owner's static PDF workbook. It opens once the participant has done their own strengths assessment and invited their coach and observers, never waiting on observers' answers, and the letter follows it.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Engine: sections, tracks, gates, progress; Hub, progress and gates; Open content and product items

- [ ] Sections 2–4 no longer appear on the hub or in any link; their content stays in the faithful port, and the drift test sets the difference aside on purpose
- [ ] The Workbook step links to the PDF, served by the app, and is completed by the participant when they are ready
- [ ] It opens once the participant's own assessment is in and they have invited their coach and observers; decide here what counts as invited (links issued, how many) and what a participant who skipped choosing a coach needs
- [ ] The letter and its closing ratings (ticket 05) open after the Workbook step, in place of after Section 3
- [ ] A placeholder PDF stands in until the content owner's arrives

**Context**

- Section 1's "comparison visited" clause (16c) already lets a participant on before any observer answers
- The workbook exists as `Prototypes for reference/Whatever You Do workbook - Oct ‘26.docx`, still to be made a PDF. It covers Sections 2–4 ("THIS BOOKLET") and sends the participant online for Sections 1 and 5
- For the content owner: the workbook expects the written questions online (Section One lists them, and Section Three asks for "Words used about you, especially by others"), which 31a and 31b defer; it promises the letter is "sealed until then", which the app does not do (ticket 22); its contents page says "Four closing questions" where its last page and the app have five; and it says "three conversations" but contains conversations two to four
