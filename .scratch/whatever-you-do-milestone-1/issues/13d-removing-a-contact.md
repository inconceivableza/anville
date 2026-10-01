# 13d: Removing a contact

**What to build:** A participant takes someone off their contact list with a button, on the invitations page and in the list itself, instead of clearing both fields of their row by hand. Removing someone stops their link, and they are told so first.

**Blocked by:** 13a (Issuing observer invitations)

**Status:** ready-for-agent

**Sprint:** not yet placed

**Spec:** Observers (ADR 0005); Testing Decisions

- [ ] Each person on the invitations page can be removed with one button, with or without JavaScript
- [ ] Each row of the contact list, in onboarding and on the invitations page, can be removed without emptying its fields by hand
- [ ] Before someone whose link is live is removed, the participant is told that link will stop working
- [ ] A removed person is deleted with their link, as taking them off the list already does, but answers they have sent stay (ADR 0007)

**Carried from 13a**

- [ ] A contact list saved from a page left open no longer deletes people added elsewhere since. Today, with onboarding open in one tab and someone added on the invitations page in another, the next autosave from onboarding deletes them and stops their link
