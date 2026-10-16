---
status: accepted
---

# Answer collection freezes once the participant looks

When the participant presses "Compare with how others see you →" with at least the minimum number of observer assessments in, they are first told how many of the people they invited have answered and that once they look no more answers are added. Confirming freezes answer collection. While it is frozen no observer assessment is accepted, and the participant cannot add people to their list or issue or reissue an observer's link; revoking still works, and the coach's link is untouched. Withdrawal always wins: an observer who withdraws while collection is frozen has their answers deleted and the comparison worked out again without them. If that leaves fewer than the minimum, collection unfreezes, and the next such press with the minimum in asks again and freezes again.

Without it, a participant who has seen the comparison could send one more link and see exactly what that person added, since links go out on different days. Below the minimum nothing is shown, so nothing freezes.

This amends ADR 0007: revoking always works, but an observer's link cannot be reissued while collection is frozen.

> ✨ Drafted with AI assistance.

## Considered options

**Freeze against withdrawal too, keeping figures that include a withdrawn observer.** Rejected: keeping them is lawful only if they are no longer that observer's personal data, which cannot be relied on with three observers the participant knows. The cost accepted is that the participant can see the count go down.

**Close collection at a deadline.** Rejected: it would still let a participant look, send one more link before the deadline and see what changed.

**Batch release of answers.** Largely overtaken: once frozen, no new answer can change what the participant has seen. It remains open for a comparison unfrozen by withdrawals and for the written answers (spec, Open content and product items).

## Consequences

- A send that arrives as collection freezes is refused under the same locks as the freeze, so no answer lands between the count and the freeze.
- The withdrawal page stays open while frozen. A withdrawn observer's own link is already dead, so an unfreeze reopens other people's working links, never theirs.
- Where the participant has withdrawn consent, an observer's link is refused as a dead link is, frozen or not, so the frozen page never tells its holder anything about the participant (ADR 0004).
- Reminders stop while collection is frozen and start again if it unfreezes (ADR 0016).
- The observers' privacy notice says that once the participant has looked at the combined results no new answers are added.
