# 13d: Removing a contact

**What to build:** A participant takes someone off their list of trusted voices with a button on the section's page, instead of clearing their row by hand. Removing someone stops their link, and they are told so first.

**Blocked by:** A4A-51a (Trusted voices card and page)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Observers (ADR 0005); Testing Decisions

- [ ] Each person on the Five trusted voices page can be removed with one button, with or without JavaScript
- [ ] Before someone whose link is live is removed, the participant is told that link will stop working
- [ ] A removed person is deleted with their link, as taking them off the list already does, but answers they have sent stay (ADR 0007)

**Context**

- Until A4A-51a the list was edited in two places, onboarding and the invitations page; it is one page now
- The autosave bug carried from 13a went to A4A-51a, whose page saves each person on their own
