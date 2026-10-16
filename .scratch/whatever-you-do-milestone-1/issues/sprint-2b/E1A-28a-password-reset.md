# 28a: Password reset

**What to build:** A participant who has forgotten their password resets it by email. Until now sign-in has offered no reset, and the operator has reset passwords by hand, because there was no email to send. Staging now sends email, so the reset comes back there. Google sign-in, split from the same ticket 28, is 28b.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 2b (12–16 Oct), on staging's email

**Spec:** Participants, access and consent (ADR 0004); Out of Scope; Legalities are parked, not forgotten

- [x] Sign-in offers "Forgot your password?" again, and the reset pages can be reached
- [ ] A participant who asks for a reset is emailed a link, sets a new password through it, and signs in with that password
- [ ] Asking for a reset never reveals whether an address has an account
- [x] On staging, the reset email carries the test-system disclaimer, as every other message does. Already met: the disclaimer wraps every message the site sends
- [ ] The temporary journey test that asserts reset is neither offered nor reachable gives way to tests of the working flow

**Context**

- Real participants need a production email provider with a processor agreement first. That is not this ticket: it belongs with the production environment
