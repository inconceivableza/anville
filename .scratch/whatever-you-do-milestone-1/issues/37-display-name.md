# 37: Display name, email as username, optional enrolment code

**What to build:** A participant gives a display name at sign-up, and every page that names them uses it, in place of the part of their email before the @. Behind it, the account's username is the email address, emails are unique, and the enrolment code becomes a per-deployment setting, switched off everywhere for now.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Participants, access and consent (ADR 0004); Observers (ADR 0005); Open content and product items

- [ ] New accounts take the email address as their username, and an email already in use is refused; sign-in stays by email
- [ ] Sign-up asks for a display name, stored on the account, never in a block
- [ ] Every page that names the participant uses the display name, never the email: their own results title, the observer's welcome and assessment wording, and the coach's invitation; an account without one falls back to the part of its email before the @, taken from the email, never from the username
- [ ] The enrolment code is asked for only when the deployment turns it on from the environment; it is on by default, so a deployment that leaves it unset admits nobody without a code, and it is turned off in every environment for now
- [ ] Two participants may share a display name; nothing relies on it being unique

**Context**

- No data migration: there is only test data, so existing accounts keep their usernames and have no display name; the fallback covers them, including any made on staging before this lands. Adding the field is still a schema migration
- With the code off, anyone who reaches sign-up can create an account; staging's demo notice is ticket 26's
- Google sign-up (28b) asks for the enrolment code only when it is on
