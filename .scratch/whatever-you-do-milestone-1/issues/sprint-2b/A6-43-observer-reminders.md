# 43: Observer reminders

**What to build:** Observers who have not yet sent their assessment are reminded by email, because the participant cannot tell who has answered and so cannot chase anyone.

**Blocked by:** A1-36 (Observer timestamps); A5-55 (Lock results once viewed)

**Status:** needs-triage

**Sprint:** 2b (12–16 Oct)

**Spec:** Observers (ADR 0005); Legalities are parked, not forgotten; Open content and product items

- [ ] An ADR records how the system knows whom to remind: the invitation is marked as sent when its observer sends, with no time and nothing pointing at the answers. With one answer in, someone reading the database can tell whose it is; the participant still sees only how many have answered
- [ ] An observer whose link is live and who has not sent is reminded once a week. Reminders end when they send, when the link expires, and when the participant's results are locked
- [ ] Reminders stop on revoke, reissue or removal, and when the participant withdraws consent
- [ ] The email names the participant, gives the observer their way back to the assessment, and says how to ask not to be reminded
- [ ] Nothing in a reminder or its absence tells the participant who has answered

**To settle before this is ready**

- How the email gives the observer their way back. The system keeps only a hash of each link, and of the secret an observer claims, so it cannot send the same link again. A reminder needs either a new link, which lets the observer send a second time (ADR 0009), or some other way in
- Whether the content owner agrees to weekly, ending when the link expires, with no separate deadline

**Context**

- Email on staging comes from a temporary domain (ticket 26); real observers need the production email provider and its processor agreement first
- The participant shares each link themselves; the system sends no invitation email. A reminder is the first message an observer gets from it
