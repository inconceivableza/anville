# 64: Opening conditions and the coach's acceptance

**What to build:** In *Whatever You Do*, Section 3 stays locked until the participant's coach has accepted, and the hub says so under it. A section can now wait on something other than a section: an authored opening condition, the first being that the coach has accepted. Once Section 3 has opened, it stays open.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3a (from 20 Oct)

**Spec:** Engine: sections, tracks, gates, progress; Implementation Decisions › Coach

- [ ] Section 3 is locked, on the hub, the sidebar and its own address, until the coach has accepted, as well as until the sections it requires are complete; a decline, no link, or a link revoked or reissued keeps it locked
- [ ] An acceptance on the coach's current link still counts after that link expires
- [ ] The hub's lock note under Section 3 reads "Opens once you've finished {sections} and your coach has accepted." while sections it requires are unfinished, and "Opens once your coach has accepted. If they decline, choose someone else." once they are done
- [ ] Once Section 3 has opened it stays open, even if the coach's link is later revoked or reissued or the coach changed
- [ ] The schema and linter accept an opening condition only from the gate's fixed set, naming a block it can read (the coach acceptance naming a coach checklist), with a message; the faithful port is unchanged

**Context**

- ADR 0019 records why, and the reversal of ticket 40's "never held back waiting on someone else"
- Section 3's requirement on Section 1 (as well as Section 2) is ticket 66, which this does not need
