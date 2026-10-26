# 103: Sign-in sometimes leaves the green page loading

**What to build:** On the coherence walk (22 Oct), signing in on staging sometimes left the green page transition showing, as if still loading, and the server's log showed nothing at the time. Find out why and fix it, or leave the cause written down for the handover.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Sprint 3c: the content owner's feedback

- [ ] The server's response to signing in on staging is timed first, since a slow server is the likely cause; only if it is quick is the browser's page transition looked at, with developer tools open
- [ ] Either the cause is fixed, with a test that would have caught it where one can, or the cause and how to reproduce it are written beside the decision in the spec

**Context**

- For `/diagnosing-bugs`. Outside the build's chains
