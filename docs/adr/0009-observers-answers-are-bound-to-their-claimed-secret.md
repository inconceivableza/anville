---
status: accepted
---

# Observers' answers are bound to the secret they claimed

What ties an observer's sent answers to the observer is a hash of the secret they claimed (ADR 0005, ticket 13b), stored with the answers and nowhere else. It is made with a prefix of its own, so it never equals the invitation's hash of the same secret: the database alone cannot join answers to a contact or an invitation. Nothing about the answers points at either, so revoking or reissuing the link, or taking the contact off the list, leaves them in place (ADR 0007). Someone holding the secret can find their answers again, which is what a later way to withdraw needs. The participant holds only the link they sent, never the secret, so they cannot.

> ✨ Drafted with AI assistance.

## Considered options

**A key from the answers to the invitation or the contact.** Rejected: reissuing, revoking and taking the contact off the list each delete those records, so the key would either delete the answers with them, against ADR 0007, or be cleared and leave the answers traceable to no one. It would also put identity next to answers in one join.

**A hash of the observer's email address.** Rejected: the participant typed every email address, so they could match it, and anyone with the list could guess it. It would not be held apart from the participant.

## Consequences

- Each claim sends one observer assessment: the hash is unique, so a second send with the same secret is refused, however close together the two arrive.
- A reissued link is a new claim with a new secret, so its observer can send again and both count. This is ADR 0007's accepted cost.
- An observer who loses their own link cannot be traced to their answers, by anyone, including the deployment's operator. How to withdraw once the link has stopped working stays open (spec, Open content and product items); whatever is chosen has to start from the observer's secret.
- Seeded test observers claimed nothing, so their answers are bound to no one.
