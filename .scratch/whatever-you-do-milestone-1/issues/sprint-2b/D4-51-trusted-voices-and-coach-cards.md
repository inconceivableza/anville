# 51: Trusted voices and coach cards

**What to build:** The two hub side cards say where things stand, and each leads to one place where the participant adds a person and gets their link in the same act, so nobody misses the step of making links.

**Blocked by:** D3-50 (Before we begin as a wizard)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Feedback from others; Observers (ADR 0005); Implementation Decisions › Coach

- [ ] The Five trusted voices card shows a tag and a line for where things stand, and two meters, invited (people with a working link) and answered (assessments sent), never a name beside an answer. Its "Manage" leads to the section's own page
- [ ] On that page adding a person makes their link in the same act and shows it there to copy, so nobody is listed without having had one. Reissue stays for a lost or expired link. The invitations page is this page
- [ ] The contact list shows three rows marked as needed and two more as optional, both numbers set on the block. An observer needs a name and an email address
- [ ] The Walk with a coach card's tag comes from its section's status and then the coach's answer (waiting, accepted, declined), and its sentence is authored. Inviting leads through the checklist to the coach's name, and then their link, in one act. The coach's email is optional
- [ ] People can still be added and changed once Before we begin is complete

**Context**

- Wording agreed for the trusted voices card (copy, open to change): "Not started"; "2 more needed", with "You'll see how others see you once 3 people have answered."; "Waiting for answers"; once collection freezes (A5-55), "Complete", with "You've seen your results, so no more answers are added."
- The coach card's sentence says only what is true: the system sends the coach nothing, so not the prototype's "We'll send them a short briefing pack"
- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3-nc-copy-copy.zip`, the hub's two cards. Its name box on the card itself is not kept: links are made on the section's page
- On the `hackathon-ui` branch the trusted voices card counts a claimed link as a reply, and its coach card says "Invite a mentor". Answered counts assessments sent, and the glossary says coach
