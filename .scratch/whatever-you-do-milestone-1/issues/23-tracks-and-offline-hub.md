# 23: Tracks and offline hub

**What to build:** Tracks. A participant chooses online or offline in onboarding; the offline track is the same pathway worked mostly on paper, with its own hub: the paper workbook to download, the strengths assessment online, a target date, and the closing ratings once the assessment is done. Switching track keeps every answer.

**Blocked by:** 09 (Section 1 and the Strengths assessment section), 10a (Onboarding completion), 22 (Sections 4 and 5 (plain), closing ratings and summary)

**Status:** ready-for-agent

**Sprint:** 3 or later; the workbook step (ticket 40) now gives every participant the offline material, so revisit whether a separate offline track is still wanted

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** third (after the studio content forms). The content owner wants to keep offline, so this ranks below the studio forms.

- [ ] A choice block in onboarding selects the track; the document lists each track as an ordered set of sections, and a section can belong to more than one track
- [ ] The offline hub is derived by the engine like any hub, from the track's sections: a paper-workbook section, the Strengths assessment section (ticket 09, shared with the online track), and the closing ratings, which require the sort to be answered. Section 1's scripture and reflection are not in the offline track, as in the prototype
- [ ] The paper-workbook section holds a download of the workbook (an asset attached to the pathway version, linked from a rich text block) and a target date (a short text block with a date format); if the file is absent the download says plainly that it is coming
- [ ] The target date is stored; the prototype's on-screen promise of a reminder email is removed
- [ ] A participant can switch tracks at any time and every stored answer persists
- [ ] Progress and locks count only the sections in the participant's track
- [ ] Journey tests cover choosing a track, the closing ratings unlocking after the assessment, and switching without loss

**Carried from 06**

- Rich text has no links or emphasis yet, and the workbook download above needs a link. Once rich text can carry one, two things the results page left out can come back: the prototype's "Want to go deeper?" block, with its outbound links to 5Q and Working Genius (`buildResults()`, after the disclaimer), and the bold on "Important:" at the start of the validity disclaimer, which is plain text in `presentation.disclaimer`
- If the closing ratings' "require the sort to be answered" is a gate clause rather than a lock, it names a block in another section, which the linter refuses today. Ticket 09 meets the same rule for Section 1's gate and should settle it first

**Carried from 41b**

- [ ] The Strengths assessment is a part of Section 1 (`part_of`) and opens only once Section 1's reading is confirmed. In a track without Section 1 it opens by its own requirements alone; nothing tests that yet, since tracks do not exist. Add a journey test that the offline track opens it with onboarding
- On the offline hub, with Section 1 absent, the Strengths assessment is listed on its own, and its results page and comparison lead back to its own page rather than to Section 1
