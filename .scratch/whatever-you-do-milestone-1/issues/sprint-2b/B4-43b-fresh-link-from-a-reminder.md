# 43b: A fresh link from a reminder

**What to build:** An observer who has lost the link the participant sent can get a fresh one from their reminder email, without going back to the participant.

**Blocked by:** B3-43a (Observer reminders)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Observers (ADR 0005); Legalities are parked, not forgotten

- [ ] The reminder email gains an "Answer for Sam →" button and a "How we handle your details" link, both to a page showing the observers' privacy notice and a button to start. Opening the page changes nothing
- [ ] Pressing it gives the observer a fresh link of their own, already claimed, shown once and kept as a claim keeps it, and takes them into the assessment. Only then do the participant's copy and any link the observer claimed before stop working
- [ ] The fresh link replaces the token on the same invitation: the date it stops working and the participant's page are unchanged
- [ ] The button's address is signed and names the invitation, and is not a link the observer landing accepts. It works again until the person has sent, and is refused, as a dead link is, once the link expires or the participant revokes or reissues it or removes the contact, while answer collection is frozen, and while the participant's consent is withdrawn. A stop to reminders does not refuse it

**Context**

- ADR 0016 records why the fresh link is not a reissue: a new invitation would show the participant a new expiry, telling them the observer had not sent, and each press would extend the link
- The press is for mail filters, which open every link in a message: a fresh link made on opening would stop the observer's own before they read the email, and the filter would hold the new one. It mirrors the observer landing, which claims only on "I'm answering for Sam →"
