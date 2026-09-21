---
status: accepted
---

# Observers are identified by their invitation, not by what they type

An observer's identity is the contact record the participant created and the single-use token that binds the observer to it, held separately from their answers. Observers type no name. Relationship is asked but never used to slice or filter results. A privacy notice is shown before the first question, aggregates stay hidden until a minimum number of observers has answered (set in the pathway document, starting at three), and written answers are stored but never shown to the participant.

> ✨ Drafted with AI assistance; the decision was reviewed and agreed by the team.

## Considered options

**The prototype's approach: observers type a first name and choose a relationship, stored with their answers, under the promise that responses are "completely anonymous".** Rejected:

- A stored name makes responses pseudonymous, not anonymous, so the promise cannot be honoured. Observer copy says "your name is never shown to the participant" instead.
- The invitation already identifies the observer, so a typed name adds nothing except a second place identity sits next to answers.
- Breaking results down by relationship identifies people at small numbers: with three observers, a single "mentor" answer identifies its author.

## Consequences

- Observer identity and observer answers live in separate records, so identity can be erased without destroying the contribution, or the contribution withdrawn without touching identity.
- Withdrawing deletes the observer's answers.
- Below the minimum, the participant sees an explanation and no numbers, never a partial distribution.
- The observer's written answers are personal data about the participant even while hidden, so they remain subject to access requests. The policy for those requests (Article 15(4)) is still open and is not decided here.
- The prototype's observer flow is unreachable in normal use (see `docs/prototype/`), so nothing is being migrated; this is designed from scratch.
