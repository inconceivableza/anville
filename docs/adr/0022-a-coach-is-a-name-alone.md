---
status: accepted
---

# A coach is a name alone, with no email address

The participant sends the coach's link themselves, and the coach is never reminded (ADR 0016), so the coach's optional email address was used for nothing: it was data about a third party, who never gave it to us, kept to no end. The content owner asked why it was there at all. The field is removed and only the coach's name is kept.

> ✨ Drafted with AI assistance.

## Considered options

**Keep it optional, for a later coach reminder or coach account.** Rejected: neither is planned, and either can ask the coach for an address themselves when it exists.

## Consequences

- The coach's link page no longer says an email address is kept.
- Observers' email addresses stay as they are for now, since the weekly reminder (ADR 0016) uses them. Asking for them only where a deployment turns reminders on was considered and left for later.
