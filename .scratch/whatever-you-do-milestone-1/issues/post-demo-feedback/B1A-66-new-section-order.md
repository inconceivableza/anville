# 66: Section 2 opens on the Strengths assessment; Section 3 needs Sections 1 and 2

**What to build:** In *Whatever You Do*, Section 2 opens once the Strengths assessment is done and a coach and three people have links, without waiting for Section 1 to be complete. Section 3 needs both Section 1 and Section 2 complete. This lets Section 1 wait on other people's answers (ticket 68) without holding up Section 2.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3a (from 20 Oct)

**Spec:** Engine: sections, tracks, gates, progress; Blocks

- [ ] Section 2 opens once the sort is in and Walk with a coach and Five trusted voices are complete, whether or not Section 1 is
- [ ] Section 2's lock note names what is unfinished, with the Strengths assessment named as the hub names it
- [ ] Section 3 is locked until both Section 1 and Section 2 are complete, and its lock note names whichever are unfinished
- [ ] A section may require a part of another section, and the linter accepts it
- [ ] The faithful port is unchanged

**Context**

- Ticket 64 also changes Section 3 in the same document; whichever lands second keeps both changes
