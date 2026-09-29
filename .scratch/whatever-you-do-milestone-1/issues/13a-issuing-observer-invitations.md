# 13a: Issuing observer invitations

**What to build:** Invitations for observers (ADR 0005). From the contacts they entered, a participant issues a unique link per observer, copies it and sends it themselves. Following a valid link reaches a plain landing page (its privacy notice and claiming are 13b); expired, revoked or unknown links are refused. No email is sent. Split from ticket 13.

**Blocked by:** 10a (Onboarding completion)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] Saving the contact list keeps each contact's record in place rather than replacing the list, so an invitation bound to a contact survives the participant editing the list; a contact taken off the list takes its invitation with it
- [ ] A participant can issue, copy, revoke and reissue a link for each contact; reissuing invalidates the previous link
- [ ] A participant who skipped the contact list in onboarding can add contacts here
- [ ] A token is 32 random bytes and only its hash is stored; the link lives for a period set in the pathway document (30 days by default) and expires accordingly
- [ ] Following a valid link reaches a plain landing page for that invitation; wrong, expired and revoked tokens are refused without revealing anything about the participant
- [ ] Journey tests cover expiry after the configured lifetime (including a non-default value), revocation, reissue, wrong token, only a hash being stored, and that editing the contact list keeps the other contacts' links working

**Carried from 10a**

- Saving replaces a list's `Contact` rows, so their ids do not last between saves. Binding an invitation to a contact will need the rows updated in place, or the invitation keyed some other way (the first criterion above)
