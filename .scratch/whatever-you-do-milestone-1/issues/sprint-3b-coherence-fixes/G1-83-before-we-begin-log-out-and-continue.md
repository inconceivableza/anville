# 83: Before we begin: "Log out", and "Continue →" ready as soon as a reason is chosen

**What to build:** Before we begin's "Exit" only goes back to the homepage, still signed in; it becomes "Log out" and logs the participant out (carried from 26 through 54). Choosing a reason and pressing "Continue →" straight away moves on, where today the button is greyed out for a moment after the choice and the press fails.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3b (coherence fixes, from 23 Oct)

**Spec:** Participants, access and consent (ADR 0004); Engine: sections, tracks, gates, progress

- [ ] Before we begin's "Exit" reads "Log out", and pressing it signs the participant out and lands on the homepage, signed out
- [ ] Choosing a reason in "What's bringing you to the course?" and pressing "Continue →" at once moves to the next page; the button is never greyed out after a choice
- [ ] Both still work with JavaScript off
