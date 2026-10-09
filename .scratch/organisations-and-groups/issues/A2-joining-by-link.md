# A2: Joining by link

**What to build:** A person opens a group's join link. Without an account they sign up without an enrolment code, consent, see a page naming the organisation and group and what its admins see, join, and land on their hub. With an account they confirm and join. A participant already in the group, or holding a dead link, is told so plainly.

**Blocked by:** A1 (Organisations, groups, membership and permissions, with can_see); B1 (Consent v2)

**Status:** claimed

**Spec:** Joining by link; Models; User Stories › Joining

- [ ] A new person who opens a join link signs up without being asked for an enrolment code, consents, confirms on a page naming the organisation and group and saying what its admins see, and lands on their hub as a member
- [ ] A signed-in participant who opens a join link confirms and joins; their pathway carries on where it was
- [ ] Opening the link for a group already joined says "You're already in this group" and offers the hub; leaving the join page without joining records nothing
- [x] An unknown or replaced link says the link no longer works and to ask whoever sent it for a new one, revealing nothing about any group
- [ ] Signing up without a join link still needs the enrolment code, unless the deployment has turned it off

**Carried from B1**

- The join page's sentence on what the group's admins and its organisation's admins see says what the consent text's group line says: your display name, how far through you are and when you were last active, and the whole group's self-assessment results averaged, never yours on their own; never your answers
