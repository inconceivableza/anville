# 92: The wizard's first page: first name, 18 or over, and consent

**What to build:** Age and consent move out of the sign-up form and the separate consent page into a first page of the wizard, in its style, before Before we begin's own pages: the participant's first name, filled in and changeable, "I am 18 or over", and the consent tick with "What this means" beside it. The engine adds this page; no pathway authors it (ADR 0021).

**Blocked by:** 83 (Messages only after a press, and Before we begin's "Log out"), C1

**Status:** resolved

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Participants, access and consent (ADR 0004); Engine: sections, tracks, gates, progress

- [x] A participant who has not passed the page is taken to it on signing in, before Before we begin: "First name", filled in from their account; "I am 18 or over"; and the consent tick from the wording sheet's "Onboarding › Consent", with "What this means" opening to the consent text
- [x] Continue moves on only with a name and both ticks, any refusal showing only after the press; no answer is stored before the page is passed
- [x] Passing it saves the name, the time 18 or over was ticked, and consent to the current version of the consent text, as the consent page records it
- [x] The consent text, here and on the consent page, follows the wording sheet (no group admins, no enrolment code, the "Draft wording" notice kept), with its version raised; the email-and-password sign-up form keeps "First name" and loses the 18+ tick
- [x] A change to the consent text later asks again on the standalone consent page, not the wizard; withdrawing there works as before
