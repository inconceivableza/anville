# 17: Timeline section

**What to build:** Section 2 ("The shape of your life"): a timeline board where a participant creates chapters of their life, drops typed markers into them, and records the recurring threads they see, with a gate that says exactly what is missing.

**Blocked by:** 04 (Hub, locks, gates and explicit completion)

**Status:** ready-for-agent

**Sprint:** 3 or later

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] A Vite module provides the timeline board: chapters (with one-click starter chapters: Childhood, Secondary school, University / training, First job, Current season), markers of five types dropped into chapters, and a threads text
- [ ] The five marker types (open door, hardship and loss, person, lasting fruit, God's leading) carry the prototype's prompts, questions and examples verbatim
- [ ] The board submits one answer that the server validates against its schema
- [ ] The gate has a clause and message for each requirement: at least three chapters, at least five markers, at least three distinct marker types, every marker in a chapter, and threads of at least ten characters
- [ ] The section uses the prototype's scripture passages and hint text
- [ ] The threads text is read from the stored answer only, never from the page (the prototype read it from the DOM and could read stale data after a restore)

**Carried from 09**

- [ ] Section 2's time estimate is "? min" in `pathways/whatever-you-do.json` until the board is built. Once it is, time it by hand and give the section its figure ("About 20 minutes"), agreed with the developer, and ideally the content owner; if the section has several activities, the block starting each one may carry its own (`estimate`, shown as "This part: …"). The faithful port has no estimates, and the drift test sets them aside
