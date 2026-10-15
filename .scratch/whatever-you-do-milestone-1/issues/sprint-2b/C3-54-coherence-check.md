# 54: Coherence check

**What to build:** A walk through the whole app on staging, by a person, to check it feels like one coherent thing after this sprint's changes, fixing what is small and ticketing what is not.

**Blocked by:** C2A-53b (New look for the participant's pages); C2B-53c (New look for the observer's, coach's and account pages); A5B-13d (Removing a contact); B2A-45 (Withdrawn consent closes observers' and the coach's links); D3-30c (Re-weighted results); E1A-28a (Password reset); E1B-28b (Google sign-in); F1A-47a (Deployment hardening: the admin's sign-in, error pages and a shared cache)

**Status:** ready-for-human

**Sprint:** 2b (12–16 Oct), before the demo on 16 Oct

**Spec:** Operating and demonstrating; Testing Decisions

- [ ] The participant's journey from the homepage and sign-up to the Workbook, the observer's from their link to a sent assessment, and the coach's from their link to seeing the comparison, each walked at desktop and phone width
- [ ] Along the way: the tie-break, password reset, Google sign-in, removing a contact, a withdrawn participant's links, and an error page
- [ ] Small fixes found on the walk go in under this ticket; anything larger becomes a ticket of its own
- [ ] The walk is recorded in the manual checks

**Context**

- Walked by a person, not an agent: `/implement-spec` pointed at this folder stops before it
- Blocked by the last ticket of each chain that changes a page someone sees. Observer reminders (B3-43) are emails and wait on decisions, so the walk does not wait for them
