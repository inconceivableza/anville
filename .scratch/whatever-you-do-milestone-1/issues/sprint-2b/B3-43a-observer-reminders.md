# 43a: Observer reminders

**What to build:** Observers who have not yet sent their assessment are reminded by email once a week, because the participant cannot tell who has answered and so cannot chase anyone. An observer can stop the reminders from the email.

**Blocked by:** B2B-55 (Answer collection freezes once results are viewed)

**Status:** resolved

**Sprint:** 2b (12–16 Oct)

**Spec:** Observers (ADR 0005); Delivery and hosting; Legalities are parked, not forgotten; Open content and product items

- [x] Sending marks the person as having sent, on their contact, kept through a reissue, a withdrawal and an edit to the contact (ADR 0016). A person not marked, whose link works, is reminded a week after the link was made and weekly after, never while answer collection is frozen or the participant's consent is withdrawn, and never a coach; a reissue restarts the week, and after an unfreeze an overdue reminder goes the next morning
- [x] A daily scheduled job in the chart, behind a value of its own, sends what is due, never the same reminder twice even if two runs overlap, retries a failed send the next day, and skips addresses at reserved example domains
- [x] The email names the participant and the date the link stops working, asks the observer to use the link the participant sent, and says where their name and email came from, what they are used for, how often and until when, and how to stop. The observers' privacy notice gains that reminders are sent and can be stopped
- [x] The email's stop link, and its `List-Unsubscribe` headers with one-click POST, stop this participant's reminders to that person. The link's page stops them only when its button is pressed, never on opening, and works while the contact exists, whatever has happened to the link. The stop is kept on the contact, through a reissue and an edit, and nothing the participant does undoes it
- [x] Nothing in a reminder, a stop or their absence reaches the participant: their pages are unchanged

**Carried from 55**

- Collection is frozen while the participant's response holds a freeze time, set by the confirmed press and cleared by a withdrawal that leaves fewer than the minimum. An unfreeze keeps no time of its own, so an overdue reminder after one is found from the link's own weekly clock
- The observers' privacy notice, in both documents, now ends with withdrawing at any time and that no new answers are added once the participant has looked; the reminders sentence goes beside them

**Context**

- ADR 0016 records whom to remind, the marks on the contact and the stop; the spec's Observers and Delivery and hosting hold the rest (developer's calls, 15 Oct)
- 43b adds the email's "Answer for Sam →" button and the fresh-link page; until then the email has no button. If time runs short, this ticket alone is a complete reminder
- Draft email copy (for the content owner to reword): subject "How do you see Sam's strengths?"; "Hi Alex, Sam asked how you see Sam's strengths, as part of Whatever You Do. It takes about 10–15 minutes. Your link works until 3 December 2026. Your name is never shown to Sam. Sam gave us your name and email address; we use them only to remind you, once a week until you answer or your link runs out." and "Don't want these reminders? Stop reminders about Sam"
- Draft notice sentence: "If you haven't answered, we'll email you a reminder once a week until your link runs out, and every reminder lets you stop them."
- Email on staging comes from a temporary domain (ticket 26); real observers need the production email provider and its processor agreement first, and the email names no controller until one is named (spec, Legalities)
- The participant shares each link themselves; the system sends no invitation email. A reminder is the first message an observer gets from it
