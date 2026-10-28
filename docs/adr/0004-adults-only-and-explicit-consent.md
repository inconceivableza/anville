---
status: accepted
---

# Adults only, no date of birth, and explicit consent before any answer is stored

The workbook collects reflective free text, including accounts of hardship and loss, and it is religious in framing, so any of it may be special category data. Participation is expected to be arranged through churches, which weakens the argument that consent is freely given. We therefore admit adults only, confirmed by an 18+ checkbox with no date of birth stored, and we require an explicit consent step at first login, before any answer is stored.

> ✨ Drafted with AI assistance.

## Considered options

**Collect date of birth, as the prototype does.** Rejected: it is data we do not need once age is only a threshold, and a stored date invites a question about what we do with under-18s.

**Admit under-18s.** Rejected for now. The enrolment reasons ("graduating", "post-secondary") suggest the audience may include 17-year-olds, but serving children brings the UK Children's Code and a parental-consent flow, which is a large obligation for an audience nobody has asked us to serve.

## Consequences

- Consent is a separate act from enrolment, so a church handing out an enrolment code cannot stand in for it. It records the version of the consent text and a timestamp, and can be withdrawn.
- Declining consent stores nothing beyond the account itself.
- The consent text is a versioned artefact; changing its meaning asks participants again.
- Under-18s are excluded. If that becomes unacceptable, revisit this decision together with a Children's Code assessment.
- Retention, deletion on withdrawal, and a data protection impact assessment remain open and are not decided here.

Note, 9 Oct (B1): version 2 of the text says who sees what (the participant, their observers, a coach, group and organisation admins, the operator) and what declining keeps (the account: display name, email address, password stored hashed, and when the account signed up and last signed in). A member who withdraws, or has not agreed to the current version, stays in their groups, and those groups' admins see their display name and that they have not consented, so they know who to follow up. That name is shown without current consent; what it rests on instead is left to the legal review the spec parks, and the text says it plainly in the meantime.

Note, 26 Oct: ADR 0021 moves the 18+ tick and consent to the wizard's first page, after the account is made, and records the tick's time; the group admins paragraph leaves the text while no organisation is set up.

Note, 28 Oct (sprint-3c-r3-fix-7): the entry page's tick now reads "I agree to Whatever You Do storing my answers, including personal things I choose to share, such as my faith or my health, as set out in the privacy notice.", in place of "…including anything about my faith, work or health…". Health and faith stay named, as the participant's choice to share, since the explicit consent this ADR asks for has to say what special category data it covers. The versioned consent text is unchanged, and the tick asks for nothing the text does not already cover, so its version stays at 3 and nobody who has agreed is asked again.
