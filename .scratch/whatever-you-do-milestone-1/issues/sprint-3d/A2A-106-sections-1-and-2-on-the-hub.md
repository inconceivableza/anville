# 106: Sections 1 and 2 on the hub and their pages

**What to build:** On 30 Oct the content owner found the way from Section 1 into Section 2 confusing (feedback, "Friday 30th - updates", images 36, 38, 41, 49, 51 and 52). Section 1 shows two "Not started" pills for one piece of work and a finish button before there is anything to finish. Section 2 is open to someone who can do nothing in it yet, its "Still need answers…" pill runs over its row's title, its finish button sits right under the workbook's download, and "Before you look" is a page holding one sentence. Section 2 now waits for the comparison, the hub points past it to Section 3, and the warning before the comparison moves onto its button.

**Blocked by:** 105 (The engine tidy-up from the code review), A1

**Status:** claimed

**Sprint:** 3d (end not yet set)

**Spec:** Sprint 3d: the code review and the 30 October feedback; Engine: sections, tracks, gates, progress; Sprint 3c: the content owner's feedback

- [x] Section 1's hub row shows one status pill, the section's, and its "I've finished Section 1" shows only once the strengths evaluation is in
- [x] Until enough of the people invited have answered, Section 2 is "Locked" on the hub and in the sidebar, its note saying it opens then, and the next step and Section 1's end lead to Section 3; once they have, Section 2 opens as now
- [x] Wherever the comparison is offered, the sentence that no answers are added once you look sits beside its "Compare" button, and pressing it shows the comparison with no page between
- [ ] On Section 2's page, "I've finished Section 2" stands apart from the workbook's download, with a line saying to come back to it once the workbook is done
- [ ] No status pill runs over its row's title, at any width
- [x] A new pathway version, which a participant starting afterwards gets; the faithful port is unchanged

**Context**

- ADR 0019 already lets a section wait on other people's answers; ADR 0017's freeze is unchanged, only where its warning sits
- Every changed line goes in the wording changes document
