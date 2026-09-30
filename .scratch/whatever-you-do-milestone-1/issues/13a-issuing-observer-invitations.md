# 13a: Issuing observer invitations

**What to build:** From the contacts they entered, a participant issues a unique link per observer, copies it and sends it themselves. A valid link reaches a plain landing page (13b fills it in); expired, revoked and unknown links are refused. No email is sent.

**Blocked by:** 10a (Onboarding completion)

**Status:** claimed

**Sprint:** 1 (ends 2 Oct)

**Spec:** Observers (ADR 0005); Testing Decisions

- [ ] Editing the contact list keeps every contact's link working, the edited contact's included; taking a contact off the list revokes theirs
- [x] A participant can issue, copy, revoke and reissue each contact's link; reissuing kills the previous one
- [ ] A participant who skipped the contact list in onboarding can add contacts here
- [x] A token is 32 random bytes and only its hash is stored; the link expires after the lifetime set in the pathway document (30 days by default; a non-default value works too)
- [x] Wrong, expired and revoked links are refused without revealing anything about the participant
