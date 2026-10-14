# 41b: The flow back to the hub and Section 1

**What to build:** The participant moves through the pathway as in the original prototype: finishing a step returns them to the hub, the Strengths assessment is a part of Section 1 that leads back into it, and Section 1 links to whatever it is still waiting on.

**Blocked by:** 41a (A header with sign out, and a pathway sidebar)

**Status:** resolved

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress

- [x] Completing a section, onboarding included, leads to the hub, where the next step is highlighted
- [x] The Strengths assessment shows on the hub, and so in the sidebar, indented under Section 1, and counts as complete once the sort is in, with no "Mark complete" of its own
- [x] Leaving the Strengths assessment leads back to Section 1: its page and the results page go back to Section 1, and the comparison ends with a way back to Section 1
- [x] The Strengths assessment opens only once Section 1 leads to it, after its reading is confirmed
- [x] Section 1's unmet requirements for the coach's link and the observers' links lead to the coach page and the invitations page

**Context**

- This replaces the ticket 09 call that the results page leads back to the Strengths assessment, where it is completed. The spec's note of that call changes with this ticket

## Answer

- Spec, Engine: sections, tracks, gates, progress: completing leads to the hub; what a part of a section is, when it opens and where it leads back to
- Spec, the ticket 09 notes for the content owner, and Section 1's offline note: replaced as above
- Spec, later items: a gate checklist on a part with a text gate
- 23, Carried from 41b: a test that the offline track opens the Strengths assessment with onboarding
- README (The hub, locks and gates), CONTEXT.md (Part) and `docs/manual-checks.md` (Back to the hub and Section 1)
