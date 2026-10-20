# 71: No-JavaScript refusals as pages

**What to build:** Without JavaScript, a refused save or contact action shows the participant a page in their frame saying why, with a way back, as a refused answer has since fix-7, never a bare status line. This covers a page left open after answer collection froze and the "This is not open yet." refusals.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3a (from 20 Oct)

**Spec:** Engine: sections, tracks, gates, progress

- [ ] Adding a person or issuing a link while collection is frozen, without JavaScript, shows the list's page with "You've seen your results, so no more answers are added."
- [ ] An answer or coach checklist step to a section not open yet, without JavaScript, shows a page in the participant's frame with "This is not open yet." and a link to the hub
- [ ] The same requests with htmx still get the short status they get now
- [ ] Each refusal keeps its status code, and nothing is stored
