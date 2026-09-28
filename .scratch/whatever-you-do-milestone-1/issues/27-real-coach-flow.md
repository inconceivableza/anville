# 27: Real coach flow

**What to build:** A simple, real coach experience if time allows. Once the coach has accepted through their link (ticket 13), the participant chooses which sections to share, and the same tokenised, read-only link shows exactly those sections. There is no coach account and no coach answers beyond accepting or declining.

**Blocked by:** 13 (Observer and coach invitations), 25 (Coach preview and briefs)

**Status:** ready-for-agent

**Sprint:** 3 or later

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

**Cut order:** first. If time runs short, the coach stays a stored contact plus the printable and copyable preview from ticket 25.

- [ ] Nothing is shared until the coach has accepted (ticket 13)
- [ ] A participant can mark individual sections as shared with their coach and can unshare them
- [ ] The coach's link from ticket 13, valid without an account, shows only the shared sections read-only; unshared sections are never visible
- [ ] Revoking or reissuing the coach's link (ticket 13) also ends access to the shared sections through the old link
- [ ] The coach cannot write anything in the shared sections
- [ ] Journey tests cover sharing, unsharing, sharing before acceptance being refused, revocation, and refusal of wrong or revoked tokens
