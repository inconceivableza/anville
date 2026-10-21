# 54: Coherence check

**What to build:** A walk through the whole app on staging, by a person, to check it feels like one coherent thing after this sprint's changes, fixing what is small and ticketing what is not.

**Blocked by:** C2A-53b (New look for the participant's pages); C2B-53c (New look for the observer's, coach's and account pages); A5B-13d (Removing a contact); B2A-45 (Withdrawn consent closes observers' and the coach's links); D3-30c (Re-weighted results); D5-59b (Re-weighting both frameworks, drawn unrounded); E1A-28a (Password reset); E1B-28b (Google sign-in); F1A-47a (Deployment hardening: the admin's sign-in, error pages and a shared cache); H1-61 ("View my results →" once the assessment is done)

**Status:** ready-for-human

**Sprint:** 2b (continued from 19 Oct), after the build

**Spec:** Operating and demonstrating; Testing Decisions

- [ ] The participant's journey from the homepage and sign-up to the Workbook, the observer's from their link to a sent assessment, and the coach's from their link to seeing the comparison, each walked at desktop and phone width
- [ ] Along the way: the tie-break, password reset, Google sign-in, removing a contact, a withdrawn participant's links, and an error page
- [ ] Google sign-in with a second test-user address; an address that already has a password account is refused; and deleting an account to repeat the demo
- [x] A password reset sent to the developer's own address arrives, as ticket 26's send-and-receive test of real email
- [ ] Small fixes found on the walk go in under this ticket; anything larger becomes a ticket of its own
- [ ] The walk is recorded in the manual checks

**Carried from 26**

- [ ] Onboarding has no way to log out: its "Exit" only goes back to the homepage, still signed in. It should probably read "Log out" and log the participant out

**Context**

- Walked by a person, not an agent: `/implement-spec` pointed at this folder stops before it
- Blocked by the last ticket of each chain that changes a page someone sees. Observer reminders (B3-43a, B4-43b) are emails and a page reached only from one, so the walk does not wait for them
- While Google's OAuth app is in Testing, only the test users listed on it can sign in with Google
- Staging sends real email through Mailjet: say before any step that sends one. Observer reminders are off on staging
