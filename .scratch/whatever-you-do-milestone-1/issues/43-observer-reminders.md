# 43: Observer reminders

**What to build:** Observers who have not yet sent their assessment are reminded by email, because the participant cannot tell who has answered and so cannot chase anyone.

**Blocked by:** 26 (Staging deployment), for email delivery

**Status:** needs-triage

**Sprint:** 2b (12–16 Oct)

**Spec:** Observers (ADR 0005); Legalities are parked, not forgotten; Open content and product items

- [ ] Decide first, in an ADR: how the system knows whom to remind without matching sent answers to a contact. Today answers are bound to the observer's claimed secret, not the contact (ADR 0009), and ticket 36 removes the times that would link them. Reminding only until a link is claimed is one option; reminding until answers are sent needs that link, which the participant could then read from who stops being reminded
- [ ] Decide first, with the content owner: how many reminders, how far apart, and whether a deadline closes collection ("once it's done, it's done", spec, Open content and product items)
- [ ] Reminders are sent only to contacts whose link is live, and stop on revoke, reissue or removal
- [ ] The email names the participant and links to the observer's own link, and says how to ask not to be reminded
- [ ] Nothing in a reminder or its absence tells the participant who has answered

**Context**

- Email on staging comes from a temporary domain (ticket 26); real observers need the production email provider and its processor agreement first (28a has the same block)
