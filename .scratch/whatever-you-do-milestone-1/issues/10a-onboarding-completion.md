# 10a: Onboarding completion

**What to build:** The rest of onboarding as an ordinary section of the pathway: a reason for taking the workbook, choosing a coach as in the content owner's mock-up (or skip), and a list of people who know the participant (or skip). Adds the single select, checkbox confirm, coach checklist and contact list blocks.

**Blocked by:** 04 (Hub, locks, gates and explicit completion)

**See also:** `Prototypes for reference/coach-selection-prototype.html`, the content owner's mock-up of choosing a coach. Its participant half is built here. Its coach half (the coach accepting or declining the six commitments through a link) is ticket 13.

**Status:** claimed

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [x] A single select block captures the reason for taking the workbook with the prototype's options (post-secondary, graduating, job change, redundancy, retirement, exploring, other)
- [ ] The coach step follows the mock-up: the intro on why the choice matters (and why "coach", not "mentor"), the candidate's first name, then the six "Do you think …" questions, each answered Yes, Not sure or No
- [ ] The outcome follows the mock-up's rules: any critical No, two or more Nos, or three or more answers that are not Yes stop ("Try someone else"); one soft No, or one or two Not sures, ask for a second thought, with an "I'm still confident" way on; all Yes proceeds. The stop and second-thought screens name each answer that caused them, with its reason
- [ ] The questions, their notes and reasons, which are critical, and the coach's first-person commitments (for 13) are authored content in the document; the outcome rule is engine code (ADR 0003)
- [ ] On proceeding, the participant records the coach's name and email with a confirmation checkbox, and the coach is stored. Ticket 13 issues the coach's link
- [ ] "Try someone else" starts again with a new candidate
- [ ] Nothing from the checklist is stored: not the six answers, not the outcome, and nothing about a candidate who is not chosen. Only the chosen coach's name and email are kept. The answers would record opinions about another person's faith, which is special category data, and no later step reads them. The server may evaluate the outcome from submitted answers but does not persist them
- [ ] The checklist is the one block that does not autosave; a participant who leaves partway starts the six questions again. A journey test pins that a completed checklist leaves no stored answer
- [ ] The coach step can still be skipped, unlike in the mock-up; a skip stores no coach and blocks nothing
- [ ] The contact list block captures name and email per row with "add another"; the minimum number of rows is authored content with a default of five, and the step can be skipped
- [ ] Contacts are stored as records that later become observers' invitations (ticket 13); they are held separately from any answers
- [ ] Email is validated properly, not just for an "@"
- [ ] Stored coach and contacts survive a reload
- [ ] The participant's name and email come from the account, not a form block

**Carried from 29**

- The baseline ratings in onboarding are marked `fixed_once_complete`, so completing onboarding fixes them for good, even if it is reopened. Leave the reason, coach and contact blocks unmarked so a participant can reopen onboarding and correct them. The flag is only defined on `agreement_scale`, so the schema refuses it on the new block types anyway.
- Both `pathways/whatever-you-do.json` and `pathways/whatever-you-do-faithful-port.json` take the new onboarding blocks; the drift test in `tests/journeys/test_whatever_you_do.py` fails if only one does. Narrowed (the developer's call, 2026-09-29): both take the reason and the contact list, which the original prototype has; only `whatever-you-do.json` takes the coach step, and the drift test sets it aside. The faithful port's own coach step, the original prototype's "Walking with a mentor" screen, is ticket 10b

## Comments

- Decided with the developer (2026-09-29): the contact list's gate passes with no contacts (skipped) or at least the authored minimum, which defaults to five; `whatever-you-do.json` sets it to 2 for testing. The coach's confirmation box is part of the coach's details form, saved with the name and email, not a block of its own. The reason is required to complete onboarding, as in the prototype.
- Split (2026-09-29): this ticket was 10; the faithful port's coach step moved to 10b.
- First step: a `single_select` block (a drop-down of authored options, saved as the option's identifier). The reason is asked first in onboarding in both pathway documents, as on the prototype's account screen, and onboarding's gate requires it with "Choose what's bringing you to the course to continue." (the prototype said only "– please choose" beside the question). It is not fixed on completion, so it can be corrected.
- Decided with the developer (2026-09-29): the reason comes straight after consent, not on the sign-up form as in the prototype. Sign-up keeps nothing but the login, and asking there would store personal data before consent and fix the question in code rather than the document. Agreeing to consent now leads a participant with nothing saved to the hub's next step (onboarding, whose first block is the reason), through `/start/`; anyone who has begun goes to the hub. The drop-down takes the prototype's look: its caret, and its amber "needs-choice" highlight until something is chosen. The prototype's "– please choose" beside the label is not carried over.
- Decided with the developer (2026-09-29): going back to "Select..." takes the reason back, as in the prototype, rather than being refused. The completion button is full width in every section, a section may word it with `complete_label` (onboarding's is the prototype's "Continue →"), and completing leads on to the hub's next step rather than back to the hub, as the prototype moves from screen to screen.
