# 27: Real mentor flow

**What to build:** A simple, real mentor experience if time allows. The participant chooses which sections to share; the mentor opens a tokenised, read-only link that shows exactly those sections. It reuses the observer token machinery, with no mentor account and no mentor answers.

**Blocked by:** 13 (Observer invitations and landing), 25 (Mentor preview and briefs)

**See also:** `Prototype for reference/coach-selection-prototype.html`, the content owner's mock-up of a mentee checklist and mentor commitments. Not yet in scope; the replanning session decides how it lands here.

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** first. If time runs short, the mentor stays a stored contact plus the printable and copyable preview from ticket 25.

- [ ] A participant can mark individual sections as shared with their mentor and can unshare them
- [ ] The mentor opens a unique link, valid without an account, that shows only the shared sections read-only; unshared sections are never visible
- [ ] Links use the same token approach as observers (random, stored hashed, revocable) and the same configurable lifetime, 30 days by default, set in the pathway document
- [ ] A participant can revoke and reissue the link
- [ ] A mentor cannot write anything and has no account
- [ ] Journey tests cover sharing, unsharing, revocation, and refusal of wrong or revoked tokens
