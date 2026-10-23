# 78: The observer's pages: no placeholder line, and the start address opened again

**What to build:** The observer's assessment no longer shows the "[Not built yet…]" line. Pressing start on an invitation's page leads to an address that takes only the press. Opening that address again, by a reload from the address bar, a bookmark or after withdrawing, shows our page for that invitation instead of the browser's bare "This page isn't working".

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3b (coherence fixes, from 23 Oct)

**Spec:** Observers (ADR 0005)

- [ ] No observer page shows "[Not built yet: the written questions come in a later version.]"
- [ ] Opening the start address of an invitation whose link works shows the invitation's own page, as its plain address does, and starting from there still works
- [ ] Opening the start address of a link that is refused (withdrawn, removed, expired or made up) shows "This link does not work", as its plain address does
