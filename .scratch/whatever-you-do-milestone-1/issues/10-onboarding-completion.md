# 10: Onboarding completion

**What to build:** The rest of onboarding as an ordinary section of the pathway: a reason for taking the workbook, a mentor (name, email and confirmation, or skip), and a list of people who know the participant (or skip). Adds the single select, checkbox confirm and contact list blocks.

**Blocked by:** 04 (Hub, locks, gates and explicit completion)

**See also:** `Prototype for reference/coach-selection-prototype.html`, the content owner's mock-up of a mentee checklist and mentor commitments. Not yet in scope; the replanning session decides how it lands here.

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [ ] A single select block captures the reason for taking the workbook with the prototype's options (post-secondary, graduating, job change, redundancy, retirement, exploring, other)
- [ ] The mentor step captures name and email with a confirmation checkbox, or is skipped; a skip stores no mentor and blocks nothing
- [ ] The contact list block captures name and email per row with "add another"; the minimum number of rows is authored content with a default of five, and the step can be skipped
- [ ] Contacts are stored as records that later become observers' invitations (ticket 13); they are held separately from any answers
- [ ] Email is validated properly, not just for an "@"
- [ ] Stored mentor and contacts survive a reload
- [ ] The participant's name and email come from the account, not a form block
