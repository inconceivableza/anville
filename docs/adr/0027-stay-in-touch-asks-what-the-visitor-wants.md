---
status: accepted
---

# "Stay in touch" asks what the visitor wants

"Join the waitlist" led to a box with no waitlist in it (the content owner's feedback of 30 Oct). The one "Stay in touch" box (ADR 0023) now asks what the visitor wants, at least one of three: their church on the waitlist, news by email, or to be contacted. "Join the waitlist" and "Contact us" open it with their own choice ticked, by naming it in the link for the server to tick, so it works without JavaScript too. Each choice is kept with its sign-up, with when it was ticked and the version of the form's wording it was ticked under, so the list can be used for each. A repeat address adds the choices it had not made and never removes one (developer's call). This replaces ADR 0023's "there is no tickbox"; the rest of ADR 0023 stands.

> ✨ Drafted with AI assistance.

## Considered options

**One sentence covering all three, with no tickbox (ADR 0023).** Replaced: the waitlist, news and a request to be contacted are different uses of an address. One sentence cannot say which a visitor wanted, so the list could not be used for each, and someone who wanted only their church on the waitlist would be sent news.

**A repeat press replacing the choices with what it ticked.** Rejected: anyone can type anyone's address, so a stranger could take someone off the waitlist, and a thanks saying so would tell them who had signed up. Taking a choice away is the operator's, when asked.

**Three yes-or-no columns on the sign-up.** Rejected: a choice added by a later press would read as made at the first, under the first press's wording, and a record of consent to email needs to say when, and to what.

## Consequences

- The form's wording is version 2. Sign-ups kept before (version 1, as on staging) have no choices: they agreed to that version's one sentence, of occasional writing and news. The admin lists and exports them with none; nothing infers a choice for them.
- The admin lists each sign-up's choices and filters by them, and its export has a column per choice holding when it was ticked. Each choice's own wording version shows on the sign-up's page.
- Nothing is sent from the app (ADR 0023), so someone asking to be contacted waits on the operator reading the list: the thanks promises an email, not when.
- Taking off one choice alone is not offered in the admin: someone who asks to stop one is deleted from the list, as anyone asking to be removed is, and can sign up again for the rest.
- The privacy page says what each choice leads to, and the thanks says what happens next for each one ticked.
