# 19: Possibilities (idea generator)

**What to build:** Section 3b ("Make a long list"): an idea generator with four lenses and rotating prompts where a participant captures many possibilities, stars the ones that draw them, and is gated on volume and range.

**Blocked by:** 18 (Calling statement (sentence builder))

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] A Vite module provides four lens tabs (who it serves, your part in it, what carries it, what if...), each with rotating prompts, free-text capture, star and unstar, and a "shake two lenses" prompt that mashes two lenses together
- [ ] The 25 prompts and the lens labels, blurbs, icons and colours are migrated verbatim into the pathway document
- [ ] Each idea references its lens by stable identifier; a lens no longer in the document is an explicit orphan case handled by policy (kept and visible), never silently reassigned to the first lens as the prototype did
- [ ] The gate requires at least six ideas across at least two lenses, with a separate message for each failing clause ("try at least one more lens: range matters more than volume")
- [ ] Starring is never required
- [ ] The section requires the calling statement to be complete
- [ ] The block submits one answer that the server validates
