---
status: accepted
---

# Observers are reminded until they send, and only they can stop it

The participant cannot tell who has answered (ADR 0005), so the system emails each observer who has not sent, once a week while their link works. Whether a person has sent, and whether they have asked not to be reminded, are kept on the participant's contact for them, not on their invitation: both survive a reissue, neither is cleared by a withdrawal or by the participant editing the contact, and both go when the contact is removed. A reminder's button gives the observer a fresh link by replacing the token on the same invitation, so the link keeps its expiry and the participant's page does not change. Since ADR 0014 the operator may know who has sent, so these marks need no hiding from them; the participant never sees either.

> ✨ Drafted with AI assistance.

## Considered options

**Keep whether a person has sent on the invitation.** Rejected: reissuing deletes the invitation, so a person who had sent would be reminded through the new link that they had not, and nudged into the second answer ADR 0007 only tolerates.

**Clear the marks when the participant changes the contact's email.** Rejected: editing the address away and back would undo the observer's request to stop, so the stop would be the participant's to reverse. The cost of keeping them is that a contact edited into a different person inherits the first person's marks.

**Stop reminders to an address across every participant.** Rejected: it keeps the address, or a guessable hash of it, after the contact is gone, with no retention rule, and stops reminders other participants never heard were stopped.

**Make the fresh link a reissue.** Rejected: a new invitation shows the participant a new expiry, which tells them the observer pressed a reminder and so had not sent, and each press would extend the link.

**Put the observer's link in the email, or a new one made when it is sent.** Rejected: a token is stored only as a hash, so the system cannot resend it; and a link made with each email would stop the one the observer already holds, every week.

## Consequences

- ADR 0007 stands: a person may still answer through a reissued link and be counted twice. The system never asks them to.
- Only the observer can stop their reminders, through the email; to be reminded again they ask the participant, who need not know they stopped.
- Opening a reminder's links changes nothing; only pressing the page's button does, as with the observer landing, since mail filters open every link in a message.
- Withdrawing leaves the person marked as having sent, so nobody is reminded after taking their answers back.
- A reminder is the system's first message to the observer, whose details came from the participant, so the email itself says where the details came from, what they are used for and how to stop.
