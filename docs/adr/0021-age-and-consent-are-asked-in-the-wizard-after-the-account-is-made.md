---
status: accepted
---

# Age and consent are asked in the wizard, after the account is made

Signing up used to take three stops before the first question: the sign-up form with its 18+ tick (for Google, allauth's second form asking for the name and the tick again), then the consent page, then Before we begin. The content owner found that Google sign-in "doesn't take you straight in". So a Google sign-up now makes the account at once, and the 18+ tick and consent move to a first page of the wizard that the engine adds before the pathway's own: the participant's first name (filled in from the account, and changeable), "I am 18 or over" and the consent tick, all required, with the consent text's details beside them. Nothing is answered before that page is passed, so ADR 0004's rule that consent comes before any stored answer still holds.

> ✨ Drafted with AI assistance.

## Considered options

**Keep the tick on the sign-up forms, and only move consent.** Rejected: Google sign-up would still stop at a form for one tick, which is the stop the content owner wanted gone.

**Let the pathway author the age and consent page.** Rejected: a pathway could then leave it out. The engine owns age and consent (spec, Engine: sections, tracks, gates, progress), so the page is the engine's, drawn in the wizard's style.

**Offer an "I'm under 18" button that deletes the account.** Rejected for now: there is no account deletion yet, and stopping at the page already stores no answer.

## Consequences

- An account (email address and first name) exists before its holder has said they are 18 or over. Someone under 18 who stops at the page leaves what a declined consent leaves: the account itself. ADR 0004's "no date of birth" stands, but its tick is now recorded, as the time it was ticked, since the wizard has to know it was given.
- A Google sign-up takes its first name from Google's given name, else its full name, else the part of the email before the @, the fallback the spec already uses. The participant can change it on the first page. The email-and-password form still asks for the first name and loses only the tick. Where a deployment requires an enrolment code, a Google sign-up falls back to the form, asking only for the code. This amends ADR 0015's consequence that a Google sign-up confirms its age there.
- A change to the consent text asks again on the standalone consent page, as before, since the wizard is once-only.
- The consent text no longer mentions group admins or enrolment codes. That is true only while the deployment has no organisations, so none is set up in this release; before one is, the group admins paragraph goes back into the text and its version goes up, so everyone is asked again.
