---
status: accepted
---

# Observers' written answers are shown to the participant without names

The participant and their observers answer the same six written questions, from the content owner's qualitative-strengths prototype, and the participant sees their own answer beside the observers'. This replaces ADR 0005's "written answers are stored but never shown to the participant". Observers' answers are shown without names and shuffled per question, so no observer's answers can be linked across questions: in the paper trial, a participant de-anonymised critical feedback by matching one person's answers across questions. No written answer appears until at least three observers have sent the written part with at least one answer in it, counted over the part as a whole, not per question.

> ✨ Drafted with AI assistance.

## Considered options

**Keep written answers hidden, as ADR 0005 had it.** Rejected: matching answers on both sides is what the content owner's written questions are for.

**Count the minimum per question.** Rejected. Observers may leave any question blank, so three may send the written part while only one answers a given question, and that one quote would stand alone. But a lone answer still came from one of the three who sent, the same "one of three" the observer average's distribution strip already allows, and counting per question would hide answers to the questions most often skipped, which are often the most useful ones, until more observers answer them.

**One submission for the observer assessment and the written part together.** Rejected, as in the prototype: the observer assessment is never held up by the written part. It is sent and counts on its own, then the written part is offered as a second part. Each is sent once, which replaces ADR 0005's "each token accepts one submission".

## Consequences

- What protects observers: their name is never shown, the claim on first use keeps the participant's copy of the link from reading anything back, the shuffle stops answers being linked across questions, and the minimum means any answer came from one of at least three people.
- What doesn't: the participant can tell whether a given person has started or answered, and could answer in their place. A participant who sends one more link and notes what changed sees what that person added; batching releases would stop that happening by accident, and is left undecided (spec, Open content and product items). A participant who sets out to identify someone can add contacts they answer for themselves, which defeats both batching and the minimum, and nothing in this milestone prevents it. A question with only one answer can't be shuffled, so where two questions each have one answer, the participant may guess they share an author; that is likeliest for the hardest questions (character, struggles), which observers skip most. A reader may also recognise a voice.
- So observer copy never says the participant "won't know who wrote this", although the prototype's hint for the struggles question does.
- The observer privacy notices say "{name} never sees your written answers" until the written part is built, and change with it, not before.
- Whether an observer's unsent written answers are saved as they type is open, and its reasoning lives in one place (spec, Open content and product items).
- Written answers are personal data about the participant, so ADR 0005's open access-request policy (Article 15(4)) covers them as before.
