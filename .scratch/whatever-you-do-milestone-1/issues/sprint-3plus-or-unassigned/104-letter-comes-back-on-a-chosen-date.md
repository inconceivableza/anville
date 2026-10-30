# 104: The letter to your future self comes back on a date the participant picks

**What to build:** Section 6 becomes a letter the participant can trust to come back. The page sets it among Joshua's twelve stones and shows where they have got to. The press that finishes the section, made once the closing ratings are answered, seals the letter until a date they pick. Until then the section page says it is sealed. On the date it opens in place, and an email to their own address says it is ready.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 3 or later

**Spec:** Sections 4 and 5, closing; Delivery and hosting; Sprint 3c: the content owner's feedback; Out of Scope; Legalities are parked, not forgotten

- [x] The page opens with Joshua 4:6b–7 (below), then the twelve-stones framing from the original prototype's letter screen. A "Where you have got to" box shows the participant's top strengths, how others see them, and their coach if one was chosen. The box also says to keep Workbooks 1–4 beside them, since they were done on paper. "Things you might want to include" lists prompts fitted to this pathway: what has shifted; what you and others saw; your calling as you would tell a friend; the Workbook 4 steps written as promises; what might knock you off course; what to say to yourself when you open it; a verse or prayer to carry. There are no "Add my…" buttons
- [x] Print and Copy text are offered until the letter is sealed. The press that finishes Section 6 also seals the letter, and its label says so. Before the press, the page makes plain that the five closing ratings must be answered before the letter can be sealed. With that press the participant picks the date: twelve months on by default, anywhere from 3 to 24 months. A refused press follows the messages-after-a-press rule. The letter's message no longer speaks of "at least one part", since the letter is one box. Like a fixed rating, the seal is recorded, so marking Section 6 not complete leaves the letter sealed, with the same date and the same email
- [x] Once sealed, the section page shows "Your letter is sealed until <date>" in its place, and no page or download carries the letter's text before then. On the date the box opens in place to show the letter, and the first time it is opened on or after the date is stored
- [x] A daily job, off unless switched on as reminders are, emails the account's own address that the letter is ready. The email links to the section page through sign-in and never carries the letter's text. If consent stands on the date, the email goes that day, even if the letter was already opened that day. If the date passed with no email sent, whether consent was withdrawn or the job was off, it goes once consent is given again and the job is on, but only if the letter has not been opened since the date. It never goes twice
- [x] "let it find you again when you need it" is replaced with wording that says only what is true. Wording that assumes twelve months, such as the task's "in twelve months' time", fits the date the participant picks. Every new or changed participant-facing sentence is recorded in the content owner's wording-changes document

**Context**

- Joshua 4:6b–7, ESV Anglicised, checked against BibleGateway (ESVUK) on 30 Oct, word for word, LORD in small caps, curly quotes: "When your children ask in time to come, ‘What do those stones mean to you?’ then you shall tell them that the waters of the Jordan were cut off before the ark of the covenant of the LORD. When it passed over the Jordan, the waters of the Jordan were cut off. So these stones shall be to the people of Israel a memorial for ever." The pathway's ESV notice already covers it
- Sealing is chosen over a separate "Seal my letter" press so that the ratings are answered too (developer's call, 30 Oct). A starting point for the label: "Seal my letter and finish Section 6", with a line above it saying the five questions come first. The final wording is the build's, recorded for the content owner
- Nothing before this ticket told a participant their letter was sealed, so a letter finished earlier carries no seal and stays open. Finishing Section 6 again seals it
- If the date passed while the job was off, the email follows the same rule as for withdrawn consent (developer's call, 30 Oct)
- Sealed means the app holds the letter back. It is stored as written, not encrypted, and the operator can still read it, so no wording may suggest otherwise
- Switching the email on waits on 62 (Before real participants: the minimum for data protection), which names the email provider and says how long a letter is kept. The job is built and tested now
- *Whatever You Do* only: the faithful port keeps the prototype's letter
- Out of scope: sending to any other address; the quarterly check-ins (`quarterly-checkin-prototype.html`)
