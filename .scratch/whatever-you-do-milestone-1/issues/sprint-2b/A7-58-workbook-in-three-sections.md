# 58: The Workbook in three sections

**What to build:** The Workbook becomes Sections 2, 3 and 4, each its own entry on the hub with its own part of the Workbook to download, opened one after another.

**Blocked by:** A6-57 (Strengths results in Section 1)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress; Sections 2 and 3; Sections 4 and 5, closing

- [ ] The hub lists Section 2 "The shape of your life" ("02"), Section 3 "Putting your calling into words" ("03") and Section 4 "Growth plan" ("04"), the faithful port's titles and ids, in place of the Workbook
- [ ] Each section offers its own PDF to download, and refuses it until the section is reached, as the Workbook's PDF is today
- [ ] Section 2 opens as the Workbook does today (Section 1 and both side cards complete); Section 3 is locked until Section 2 is marked complete, Section 4 until Section 3, and the letter until Section 4
- [ ] Each is completed on its own by the participant's own button, and the header counts all three among the sections
- [ ] The drift test sets aside Whatever You Do's three downloads in place of the faithful port's in-app Sections 2–4, and fails if either document's sections change otherwise

**Carried from fix-2**

- Developer's calls, 16 Oct: three PDFs, one per section, made from the content owner's three section documents; a plain lock by order for now; built in sprint 2b
- The PDFs are in `Prototypes for reference/` in the main checkout, beside their `.docx` sources (untracked): "Whatever You Do workbook - Section 2.pdf", "- Section 3.pdf" and "- Section 4.pdf". They go beside the pathway document, and the `.docx` sources into `Prototypes for reference/`, as the whole Workbook's is
- The whole Workbook's PDF and its section leave Whatever You Do; the spec's lines on the Workbook standing in for Sections 2–4 (the Sprints' 2a line, the hub's "02–04" and ticket 52's gate) are brought up to date
- Each section's estimate, its sentence and the hub's next step for it (the Workbook's today) are new wording: listed for the developer's review
