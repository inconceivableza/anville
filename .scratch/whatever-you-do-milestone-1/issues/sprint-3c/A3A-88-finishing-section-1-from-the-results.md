# 88: Finishing Section 1 from the results page

**What to build:** The strengths evaluation is the last thing in Section 1, so its results page finishes the section: its main button reads "I've finished Section 1", completes Section 1 and lands on the hub, in one step instead of going back to Section 1 to press it there. Beside it, a participant without enough answers is sent to invite people rather than to a comparison they cannot see yet.

**Blocked by:** 87 (Six sections), A2

**Status:** ready-for-agent

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Engine: sections, tracks, gates, progress; Blocks

- [ ] Until Section 1 is complete, the results page's main button reads "I've finished Section 1"; pressing it completes Section 1 and lands on the hub. Once Section 1 is complete, the button reads "Back to the hub". Section 1's own page keeps its finish button
- [ ] In any pathway, a part that is the last thing in its section offers that section's finish button at its end, refused through the section's gate as the section's own button is
- [ ] Beside it, as an outline button: below the minimum, "Invite people who know you →", leading to Five trusted voices, with ticket 81's "how many more" phrase beside it; at or above the minimum, "Compare with how others see you →", as now
- [ ] The comparison signpost's button is grey while nobody has answered
- [ ] All of it works without JavaScript and at phone width
