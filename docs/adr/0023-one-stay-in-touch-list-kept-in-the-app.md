---
status: accepted, partly superseded by ADR 0027
---

# One "Stay in touch" list, kept in the app

The content owner asked for three sign-ups on the homepage: a newsletter, general contact and churches' interest, the last the most important. They are one email field, "Stay in touch", whose sentence covers all three, and its addresses are kept in the app's database, where the operator sees and exports them in the admin. Nothing is sent from the app: the newsletters go out from whatever tool the list is exported to, and that tool carries the unsubscribe link. Submitting the form is the consent, since the form has no other purpose, so there is no tickbox.

Partly superseded: the box now asks what the visitor wants, at least one of their church on the waitlist, news by email and to be contacted, and keeps each choice with when it was ticked (ADR 0027), so there is a tickbox for each. The one list, kept in the app and sent from nowhere, stands.

> ✨ Drafted with AI assistance.

## Considered options

**Three forms, one per purpose.** Rejected: three boxes for one email address, and the content owner said the newsletter can be the same as the churches' waitlist.

**A newsletter service's own form (such as Beehiiv) in place of storing it.** Rejected for this release: it sends visitors' addresses to another processor from the homepage, and the list is wanted in the app before a service is chosen.

**Showing the form only once a controller is named for the deployment (ticket 74's first rule).** Replaced: the form links to the privacy page, which names the controller, and the release waits on that page being signed off.

## Consequences

- Each sign-up stores the address, when, and the version of the sentence it agreed to. A repeat address gets the same thanks, so the form tells nobody who has signed up.
- There is no unsubscribe in the app. Someone who wants to be removed before any newsletter exists asks, and the operator deletes them in the admin.
- The privacy page must say what the list is for, who keeps it and for how long, before the form goes live with real visitors.
