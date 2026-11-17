# 117: Photos tied to a stage of the pathway are named in the pathway

**What to build:** Every photo a participant sees at a stage of the pathway is named in the pathway document, with its credit, and kept in a folder of the pathway's own beside the document, so a pathway carries its own pictures and the engine names only the site's (the homepage, the story, the video). Today they are split three ways: Before we begin's photos are a list in the engine, drawn as static files from the frontend's images; the hub's next-step photos for the side cards and for a section with none of its own are chosen by the engine; and only Section 1's photo is named in *Whatever You Do*'s document, its file in `pathways/files/`, a folder every pathway shares. The same grass photo is both Section 1's and a wizard step's, so it is credited twice and the credits page shows a "Photographs" heading over that one line.

**Blocked by:** None (can start immediately)

**Status:** needs-triage

**Sprint:** 3 or later

**Spec:** The pathway document and versions; Sprint 3c: the content owner's feedback; Sprint 3d: the code review and the 30 October feedback

- [ ] Each photo shown at a stage of the pathway (a page of Before we begin, the hub's next step for a section or a side card, a section's own page) is named in the pathway document with its credit, and no photo of a stage is named in the engine's code
- [ ] A pathway's photos are files in a folder beside its document, named after it (`pathways/whatever-you-do/` beside `pathways/whatever-you-do.json`), so two pathways can each have a photo of the same name; the faithful port keeps the photos it shows today
- [ ] The credits page lists each photo once, whichever list names it, and no heading stands over a single line because one file is used twice
- [ ] A photo shown before consent, as the entry page's is, is served then; every other pathway photo still waits for consent
- [ ] Loading a pathway refuses a document that names a photo whose file is missing, at its document path

**Context**

- Settled with the developer, 17 Nov: photos tied to a stage belong in the pathway; not for sprint 3d, which leaves the duplicate grass credit as it is
- Where the files go: a folder beside the document, named after it, the document's `file` names resolved within it, is the starting point; the shared `pathways/files/` also holds the workbook PDFs, and whether they move with the photos is for triage. So is whether a pathway's files count in its version (today a version is the document's content hash, so a changed photo under an unchanged name makes no new version)
- Before consent: the document's photos are served only after consent today (ticket 49b), but the entry page shows a wizard photo before it (ADR 0021); the document needs a way to say which photo may be shown then
- ADR 0003 binds the schema change (the pathway document is data, not a language)
