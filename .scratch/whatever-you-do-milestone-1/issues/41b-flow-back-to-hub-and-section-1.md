# 41b: The flow back to the hub and Section 1

**What to build:** The participant moves through the pathway as in the original prototype: finishing a step returns them to the hub, the Strengths assessment is a part of Section 1 that leads back into it, and Section 1 links to whatever it is still waiting on.

**Blocked by:** 41a (A header with sign out, and a pathway sidebar)

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress

- [ ] Completing a section, onboarding included, leads to the hub, where the next step is highlighted
- [ ] The Strengths assessment shows on the hub, and so in the sidebar, indented under Section 1, and counts as complete once the sort is in, with no "Mark complete" of its own
- [ ] Leaving the Strengths assessment leads back to Section 1: its page and the results page go back to Section 1, and the comparison ends with a way back to Section 1
- [ ] Section 1's unmet requirements for the coach's link and the observers' links lead to the coach page and the invitations page

**Context**

- This replaces the ticket 09 call that the results page leads back to the Strengths assessment, where it is completed. The spec's note of that call changes with this ticket
