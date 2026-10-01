---
status: accepted
---

# Observers' answers outlive their link

An observer's sent answers stay when the participant revokes or reissues their link, or takes them off the contact list, and revoking and reissuing always work, whether or not anyone has answered. The participant holds a copy of every link and sees how many observers have answered and, once there are enough, the observer average. If revoking deleted the answers, they could note the averages, revoke one person's link, and read that person's observer assessment from the difference: the comparison ADR 0005 guards against.

> ✨ Drafted with AI assistance.

## Considered options

**Delete the answers with the link.** Rejected: it hands the participant the before-and-after comparison above, and a reissue would silently throw away what an observer sent.

**Refuse revoking or reissuing once someone has answered.** Rejected: the refusal itself tells the participant who has answered, which ADR 0005 keeps from them.

## Consequences

- Someone can be counted twice: a reissued link is a fresh token, and the person may answer again through it. This is the accepted cost, since any guard against it would reveal who answered.
- Whatever binds an observer's answers to their invitation must not delete them with it. Today reissuing, revoking and removing a contact each delete the invitation record, so a cascading key would break this decision.
- Sent answers are deleted only when the observer withdraws, or with the participant's response (they are personal data about the participant).
- Once the link is revoked, reissued or removed, the observer's claimed link stops working, so they can no longer withdraw through it. This is the same open question as withdrawing after the link expires (spec, Open content and product items).
