# 37: Username

**What to build:** A participant chooses the name they are known by, and observers, the coach and every page use it, in place of the part of their email before the @.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Participants, access and consent (ADR 0004); Observers (ADR 0005); Open content and product items

- [ ] Decide here, with the senior developer: whether sign-in stays by email with the name only for display, and whether the enrolment code stays, goes, or becomes optional per deployment. The 2 Oct demo raised both and settled neither
- [ ] Sign-up asks for the name; it is stored on the account, never in a block
- [ ] Accounts made before this ticket are asked for a name once, and until then keep today's fallback
- [ ] Every place that names the participant to an observer or the coach (the observer's welcome and assessment wording, the coach's invitation) uses the name
- [ ] Two participants may share a name; nothing relies on it being unique

**Carried from 10a**

- The participant's name is not asked anywhere today; the account holds only an email
