# 120: An observer who saw nothing has declined

**What to build:** An observer who sends with every card in "Haven't seen this" is stored and counted for nothing, so the participant's warning before the comparison still counts them among "anyone who hasn't answered yet", although they sent. Ask the observer before they send, and treat such a send as that observer declining to answer: keep only the decline, and stop waiting on them.

**Blocked by:** 108 (its "Haven't seen this", and its hand check found it)

**Status:** resolved

**Sprint:** 3d (end not yet set)

**Spec:** Sprint 3d: the code review and the 30 October feedback, "An observer who saw nothing has declined"; Observers, "Haven't seen this"; "Answer collection freezes"

- [x] Once every card is in "Haven't seen this", the observer's sort says what sending means in place of its other presses, with "Send that I couldn't answer →" and undo to go back
- [x] Such a send, however it comes, is kept as a decline: when, and nothing else, no assessment and no relationship, kept apart from who sent it as answers are, so it counts toward no minimum and is no part of the comparison
- [x] The observer is thanked for it, never reminded again, offered no way to withdraw (as a coach's decline has none), and a second send is refused
- [x] The participant is told how many declined, naming nobody, as withdrawals are told: on Five trusted voices' page and beside its card's Answered count
- [x] The freeze warning counts the declines as replies and says "replied"; Five trusted voices' card has "All answers received" once the answers and declines reach everyone with a link
- [x] A retake deletes the declines with the answers, so those people are asked again
- [x] Sends already made with nothing seen become declines as the migration runs
- [x] The observers' note says what such a send keeps, and the changed wording is in the wording changes document

**Context**

- Found in the hand check of ticket 108 on 17 Nov: Quin put every card in "Haven't seen this" and sent, so Ada's warning read "3 of the 4 people you invited have answered… anyone who hasn't answered yet won't be able to", although all four had sent. Of the options offered (word the warning from who has sent; say one answer couldn't be used; ask the observer before they send; leave it), the developer chose to ask first: "if they choose not to give any answers other than Haven't seen this it should be equivalent to that observer declining to answer the questionnaire."
- The developer's calls, 17 Nov: keep only the decline, not the sort marked declined; and count decliners as replied, said as a count, rather than leave them out silently.
- Kept on `ObserverResponse` as `declined_at`, found by the observer's secret as a send is, since nothing ties answers to a contact (ADR 0005, 0009); a decline kept on the observer's link, as a coach's is, could not have taken in sends already made. So a reissued link asks again, and if that person then answers, both count, as ADR 0007 has it for two sends.
- Manual check: `docs/manual-checks.md`, "Ticket 120: An observer who saw nothing has declined".
