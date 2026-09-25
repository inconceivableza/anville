# 08: Age confirmation and consent

**What to build:** Adults-only access and explicit consent (ADR 0004). A participant confirms they are 18 or over with a checkbox (no date of birth is stored) and gives explicit consent before any answer is stored, separately from enrolment. Declining stores nothing beyond the account, and consent can be withdrawn later.

**Blocked by:** 04 (Hub, locks, gates and explicit completion)

**Status:** claimed

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [x] An 18+ checkbox is required and no date of birth is collected or stored
- [ ] A consent step precedes any pathway access; it records the version of the consent text and a timestamp, and is separate from the enrolment code
- [ ] Declining consent stores nothing beyond the account and prevents answering
- [ ] Consent can be withdrawn later from the participant's account
- [ ] A change in the meaning of the consent text (a new version) asks participants again
- [ ] Journey tests: declining stores no answers; enrolment alone never counts as consent; the 18+ confirmation is enforced
- [ ] Note: until this ticket lands, earlier tickets store fake-data answers with no consent step. That is acceptable only on fake data; no real participant's data goes into any instance before consent, a named controller and a retention rule exist. The consent text itself needs writing before real use (see spec Further Notes)

## Comments

- First step: the 18+ checkbox is on the sign-up form, beside the enrolment code, and is not stored. Asking at sign-up rather than at the consent step means an under-18 never gets an account, so nothing about them is kept, not even an email. Google sign-up (ticket 28) goes through the same form. The journey test for enforcing it is in; the other journey tests follow with consent. The box sits just above the button, without Django's colon; the sign-in "Remember me" lost its colon and title case to match.
