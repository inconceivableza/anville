---
status: accepted
---

# Participants may sign in with Google

A participant may sign in with their Google account, alongside email and password, and Google then handles that sign-in under its own terms. It is the first place a participant's identity passes through a third party, and it is acceptable because the participant chooses it each time: email and password stays, so nobody has to use Google to take part. Anville asks Google only for `openid`, the email address and the basic profile, and Anville's privacy notice, once written, names Google for anyone who uses the button.

> ✨ Drafted with AI assistance.

## Considered options

**Email and password only.** Rejected: signing in with an account a participant already has is normal and expected, and keeping it off costs them a password to remember for no gain in privacy, since nobody is made to use it.

**Keeping Google out for the reason fonts were kept out (ticket 03).** Not comparable: serving fonts from Google sends every visitor's address there without their choosing, whereas sign-in reaches Google only when a participant presses its button.

## Consequences

- The privacy notice, when it is written, says Google handles sign-in for participants who choose it (spec, Legalities are parked, not forgotten).
- A participant signing up through Google still confirms they are 18 or over, gives the enrolment code where the deployment asks for one, and passes the consent step (ADR 0004). Since ADR 0021 the account is made at once and the age and consent are asked on the wizard's first page.
- Until the app is published in the Google project, only listed test users can sign in with Google. Publishing needs a privacy notice, terms and a verified domain, so it waits for those.
- The Google project is held by one operator for now. Before real use it should belong to an account the church holds, with a second owner.
