---
status: accepted
---

# The operator may link an observer to their answers; the participant may not

The privacy an observer is owed is from the participant: the participant must not be able to tell which answers are whose. That is met by what the participant is shown, which is how many have answered, an observer average hidden below the minimum, each construct's values in ascending order, and written answers without names (ADRs 0005 and 0008). It does not need the database to keep an observer's identity apart from their answers. The deployment's operator, who can already read everything a deployment holds, may link an observer to what they sent, and nothing is built to stop them.

> ✨ Drafted with AI assistance.

## Considered options

**Keep the operator unable to link them, as ADR 0009's consequences put it.** Rejected. It guards against a party who already holds every observer's name and email address and every answer, and whom observers must trust with both anyway. It is not required by UK or EU data protection law, which asks that the link be secured and that observers are told of it truthfully. And it costs: claim and send times would have to go (ticket 36), an observer whose link has stopped working could not be found to withdraw, an observer's own access or erasure request could not be answered, and reminders would need a separate mark to know who has sent.

## Consequences

- ADR 0009's binding stands for what it does: each claim sends once, and answers outlive the link, the invitation and the contact (ADR 0007). Its consequence that nobody, the operator included, can trace an observer to their answers no longer holds, and is not to be preserved.
- Ticket 36, which would have removed the claim and send times so the operator could not line them up, is dropped. The participant never sees either time.
- An observer whose link has stopped working can withdraw by asking the operator, who can find their answers. How observers are told of this is still to be written (spec, Open content and product items).
- Reminders can tell whom to remind from whether that observer's answers have been sent (ticket 43).
- The observers' privacy notice must not say that nobody can connect them to their answers. It says the participant never sees which answers are whose, and that the people who run the service can.
- A breach of the database would expose more: named observers' views of a named participant. The data protection impact assessment weighs this, along with access control and encryption at rest.
- A participant's access request can no longer be answered with "we cannot tell who said what". Withholding it is a choice the operator makes under Article 15(4), whose policy is still open (ADR 0005).
