# 49a: Hub layout and side cards

**What to build:** The hub takes the final prototype's layout: wide, with the next step and the sections on the left and hub side cards beside them, so sections no longer wrap in a thin column. The hub merged from the `hackathon-ui` branch in A0-48 has the layout, but writes its side cards in the template, reads section numbers out of titles and shows a "Where you started" card; this reads which sections are side cards, and their numbers, from the pathway document. The next step's wording and the photos are 49b.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 2b (12–16 Oct)

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress; The pathway document and versions

- [x] The hub is laid out as the prototype's: its width, its two columns in its proportions, one column at phone width, and section rows that do not wrap, each beside its section's number as the document authors it ("01", "02–04"), or none where it has none
- [x] The hub is framed as the prototype's: the cream hub inset within the deep brown page
- [x] A section the pathway document marks as a hub side card is drawn as a card in the second column, from its title, its authored sentence and its status, and is not listed with the other sections. Nothing on a card is written in a template
- [x] The header counts sections complete ("2 of 5 sections complete") in place of answers. The "Where you started" card goes: it showed the strengths baseline, and the before-and-after ratings are ticket 56

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, the hub view
- The branch reads a section's number out of its title ("Section 1: …") and renamed the Workbook "Sections 2–4: The Workbook" so the hub would show where it falls. Both go: the number is authored (Section 1 "01", the Workbook "02–04", Section 5 "05"; Before we begin and the Strengths assessment, a part, none), the Workbook is "The Workbook" again, and the test the branch added for the longer title changes with it
- The prototype's frame: the page is deep brown and the cream hub sits inset 10px within it, on a 1180px wrap. The branch's hub is cream on cream inside the 720px container (found in ticket 48's review)
- Split from ticket 49 on 15 Oct; 49b holds the next step's wording, the photos and their credits
- New fields go into the schema and its linter. The faithful port takes none of them, and the drift test sets them aside
