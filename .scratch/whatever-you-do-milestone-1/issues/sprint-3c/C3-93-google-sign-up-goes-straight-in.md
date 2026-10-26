# 93: Google sign-up goes straight in

**What to build:** "Continue with Google" stops at a second form before the participant gets in. A Google sign-up now makes the account at once and lands on the wizard's first page, where the name Google gave can be changed (ADR 0021).

**Blocked by:** 92 (The wizard's first page), C2

**Status:** ready-for-agent

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Participants, access and consent (ADR 0004)

- [ ] "Continue with Google" for someone without an account makes it at once, with no form, and lands on the wizard's first page
- [ ] The first name there is Google's given name, else its full name, else the part of the email before the @
- [ ] Where the deployment requires an enrolment code, a Google sign-up shows a form asking only for the code
- [ ] An address that already has a password account is refused as ticket 77 settled, with the same wording and links
- [ ] A participant who already signed up with Google signs straight in, as now
