# 41a: A header with sign out, and a pathway sidebar

**What to build:** Every participant page has a header that leads to the hub, opens a sidebar showing where they are in the pathway, and lets them sign out, so nobody has to find their way back through the pages they came by.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress

- [ ] Every participant page has a header with the pathway's name leading to the hub, a button that opens the sidebar, and a way to sign out that leads to the homepage; observers' and the coach's pages have none of these
- [ ] The sidebar lists the same steps as the hub, with the same status and locks, the current one marked; locked steps are shown but not linked
- [ ] Results, the comparison, the invitations page and the coach page are reachable from the sidebar
- [ ] The sidebar opens and closes with or without JavaScript
- [ ] The sidebar can be switched off for the whole site by a setting, leaving the header, its link to the hub and sign out

**Context**

- The Strengths assessment belongs to Section 1 in the participant's eyes, though it is its own section in the document. 41b shows it indented under Section 1 on the hub, and the sidebar follows the hub
- Breadcrumbs were considered and left out for now. If they are added later, they should be switchable by a setting in the same way

**Original criteria (replaced 7 Oct)**

Ticket 41 was "Sidebar navigation". It grew into better navigation overall and was split into 41a (this header and sidebar), 41b (the flow back to the hub and Section 1) and 41c (time estimates). Its original criteria, kept for reference and superseded by those above:

- The sidebar lists the same steps as the hub, with the same status and locks, the current one marked
- It opens and closes from every participant page, and works without JavaScript (falling back to a link to the hub)
- Results, the comparison and the invitations page are reachable from it
- Locked steps are shown but not linked, as on the hub
- Observers' and the coach's pages have no sidebar
