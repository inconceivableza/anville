# 52: Workbook and Section 1 gates

**What to build:** Section 1 can be completed on the participant's own work, without viewing the comparison. The Workbook opens once Section 1 is complete and a coach and three people have links, never waiting for any observer to answer.

**Blocked by:** D4-51 (Trusted voices and coach cards)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress; Observers (ADR 0005)

- [ ] Section 1's gate no longer asks for the comparison to have been visited, nor for anyone's link
- [ ] Walk with a coach is complete once the coach has a link, and Five trusted voices once three people have links. Neither has anything to press, and each stays complete after that: links that later expire or are revoked, or people taken off the list, never lock the Workbook again
- [ ] The Workbook requires Section 1 and both hub side cards, and while it is locked the hub names the sections still open, for example "Opens once you've finished Walk with a coach and Five trusted voices."
- [ ] The comparison still needs three answers, and nothing a participant must do to reach the Workbook waits on an observer

**Context**

- This reverses Section 1's gate as ticket 16c built it. The clause for a visited comparison stays available to authors
- The faithful port keeps the original prototype's gates
- Why the side cards stay complete: links expire after 30 days, and once answer collection freezes (A5-55) none can be reissued, so a completion worked out afresh from working links would lock the Workbook for good a month in
