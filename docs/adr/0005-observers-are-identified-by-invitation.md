---
status: accepted, partly superseded by ADR-0007 and ADR-0008
---

# Observers are identified by their invitation, not by what they type

An observer's identity is the contact record the participant created and the token, unique to that observer, that binds them to it, held separately from their answers. Each token accepts one submission. Observers type no name. Relationship is asked but never used to slice or filter results. A privacy notice is shown before the first question, aggregates stay hidden until a minimum number of observers has answered (set in the pathway document, starting at three), and written answers are stored but never shown to the participant.

Partly superseded: written answers are now shown to the participant without names, and each token takes the observer assessment once and the written part once (ADR 0008). Sent answers outlive the link (ADR 0007). The rest stands.

> ✨ Drafted with AI assistance.

## Considered options

**The prototype's approach: observers type a first name and choose a relationship, stored with their answers, under the promise that responses are "completely anonymous".** Rejected:

- A stored name makes responses pseudonymous, not anonymous, so the promise cannot be honoured. Observer copy says "your name is never shown to the participant" instead.
- The invitation already identifies the observer, so a typed name adds nothing except a second place identity sits next to answers.
- Breaking results down by relationship identifies people at small numbers: with three observers, a single "mentor" answer identifies its author.

## Consequences

- Observer identity and observer answers live in separate records, so identity can be erased without destroying the contribution, or the contribution withdrawn without touching identity.
- Withdrawing deletes the observer's answers.
- An invitation link lives for a period set in the pathway document, thirty days by default, and can be revoked. The task takes ten to fifteen minutes but observers may take a while to get to it, so the default favours completion; the cost is a longer window in which a leaked link works, which revocation and reissue mitigate. Mentor links, if built, use the same token approach and the same configurable default.
- Below the minimum, the participant sees an explanation and no numbers, never a partial distribution.
- The participant sees only how many observers have answered, never which invited person has. Otherwise, comparing the averages before and after one more answer would reveal that person's exact scores. The cost is that a participant cannot tell which observer to chase.
- That guard has a gap: because a claimed link stops working for the participant, they can tell when a given person has answered (tickets 13b, 15a). The distribution strip then makes the before-and-after comparison exact: the one new value on each construct is that person's. The average alone gives it to within the rounding. The strip is kept for now, since there is no real data yet and the average leaks nearly as much; the gap closes only when the participant can no longer tell who has answered, for example once links are delivered without passing through the participant. Recorded with ticket 16b; closing it is not yet ticketed.
- The observer's written answers are personal data about the participant even while hidden, so they remain subject to access requests. The policy for those requests (Article 15(4)) is still open and is not decided here.
- The prototype's observer flow is unreachable in normal use (see `docs/prototype/`), so nothing is being migrated; this is designed from scratch.
