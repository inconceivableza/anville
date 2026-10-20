# 69: Before we begin once only

**What to build:** Once Before we begin is complete, the participant never sees it again: it is gone from the hub and the sidebar, and its pages and saves send them to the hub, so neither the reason nor the opening ratings can be seen or changed. A section-level setting, so the whole section is fixed rather than block by block.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3a (from 20 Oct)

**Spec:** Engine: sections, tracks, gates, progress

- [ ] Once a once-only section is complete, it is not listed on the hub or in the sidebar, and not counted in "x of y sections complete"
- [ ] Opening any of its pages, saving an answer to it, or completing it again sends the participant to the hub, with or without JavaScript, and changes nothing stored
- [ ] Before it is complete it behaves as now, as a wizard
- [ ] The linter refuses a once-only section that is not a wizard
- [ ] Before we begin is once-only in *Whatever You Do*; the faithful port keeps it listed
