# 27: Real coach flow

**What to build:** A simple, real coach experience if time allows. The participant chooses which sections to share; the coach opens a tokenised, read-only link that shows exactly those sections. It reuses the observer token machinery, with no coach account and no coach answers.

**Blocked by:** 13 (Observer invitations and landing), 25 (Coach preview and briefs)

**See also:** `Prototype for reference/coach-selection-prototype.html`, the content owner's mock-up of a participant checklist and coach commitments. Not yet in scope; the replanning session decides how it lands here.

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** first. If time runs short, the coach stays a stored contact plus the printable and copyable preview from ticket 25.

- [ ] A participant can mark individual sections as shared with their coach and can unshare them
- [ ] The coach opens a unique link, valid without an account, that shows only the shared sections read-only; unshared sections are never visible
- [ ] Links use the same token approach as observers (random, stored hashed, revocable) and the same configurable lifetime, 30 days by default, set in the pathway document
- [ ] A participant can revoke and reissue the link
- [ ] A coach cannot write anything and has no account
- [ ] Journey tests cover sharing, unsharing, revocation, and refusal of wrong or revoked tokens
