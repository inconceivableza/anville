# 51a: Trusted voices card and page

**What to build:** The Five trusted voices card says where things stand, and leads to one page where the participant adds a person and gets their link in the same act, so nobody misses the step of making links. The coach's card is 51b.

**Blocked by:** A3-50 (Before we begin as a wizard)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Feedback from others; Observers (ADR 0005)

- [ ] The Five trusted voices card shows a tag and a line for where things stand, taken first from its section's status, so once complete it never goes back to asking for more people. Two meters show invited (people with a working link) and answered (assessments sent), and no names. Its "Manage" leads to the section's own page
- [ ] On that page adding a person makes their link in the same act and shows it there to copy, so nobody is listed without having had one. Reissue stays for a lost or expired link. The invitations page is this page
- [ ] The list shows three rows marked as needed and two more as optional, both numbers set on the block. An observer needs a name and an email address
- [ ] Saving one person never removes or changes anyone else on the list, even from the page left open in another tab
- [ ] People can still be added and changed once Before we begin is complete

**Context**

- Wording agreed for the card (copy, open to change): "Not started"; "2 more needed", with "You'll see how others see you once 3 people have answered."; "Waiting for answers". The frozen state is B2B-55's
- The card's authored sentence keeps the prototype's, less "anonymous", which is no longer true (ADR 0014, and the participant can tell who has answered): "Invite people who know you well. Their answers sit beside your own in Section 1, combined so you never see whose is whose."
- No names on the card: the branch lists them, and the prototype ticks one, which comes close to showing who has answered. The section's own page lists everyone
- The fourth criterion comes from ticket 13a: today, with onboarding open in one tab and someone added on the invitations page in another, the next autosave from onboarding deletes them and stops their link. Saving each person on their own, rather than the whole list at once, removes it
- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, the hub's trusted voices card. Its name box on the card itself is not kept: links are made on the section's page
- As merged from the `hackathon-ui` branch in A0-48, the card counts a claimed link as a reply. Answered counts assessments sent
- Split from ticket 51 on 15 Oct; 51b holds the coach's card
