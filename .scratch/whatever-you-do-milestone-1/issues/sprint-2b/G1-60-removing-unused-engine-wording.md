# 60: Removing the engine wording no pathway uses

**What to build:** Two ways of wording a page's way on, built for the original prototype's onboarding, are no longer reached by either pathway, so they are removed from the engine: a page break's skip label (the prototype's "I'll sort this later →"), and the way on that names a coach kept on its page ("Continue with Sam →", or "Continue without a coach →" once that coach has declined). Every page's way on reads "Continue →". Nothing a participant sees changes.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2b (continued from 19 Oct)

**Spec:** Blocks; Open content and product items

- [ ] A page break no longer takes a skip label: the schema and the linter refuse one, and the README no longer describes it
- [ ] A page's way on is always "Continue →", whatever its coach checklist holds
- [ ] The coach checklist's own steps are unchanged, its "Continue →" buttons and its "Keep Sam" included
- [ ] Tests that set up a skip label, or the coach-named way on, are removed with them, and no test strips a skip label from a pathway any more
- [ ] Both pathway files and the example still load and pass the linter

**Context**

- Neither pathway file uses a skip label. The coach-named way on shows only on a page before a section's last holding a coach checklist; *Whatever You Do*'s one checklist is on a one-page hub side card (ticket 52), and the faithful port has none, so neither reaches it. Checked on 19 Oct
- Raised in the sprint 2b end report's open questions; the developer's call, 19 Oct
