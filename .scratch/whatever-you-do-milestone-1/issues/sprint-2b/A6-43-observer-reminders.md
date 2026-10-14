# 43: Observer reminders

**What to build:** Observers who have not yet sent their assessment are reminded by email, because the participant cannot tell who has answered and so cannot chase anyone. A reminder lets an observer who lost their link get a fresh one.

**Blocked by:** A5-55 (Answer collection freezes once results are viewed)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Observers (ADR 0005); Legalities are parked, not forgotten; Open content and product items

- [ ] The system knows whom to remind from whether each invitation's observer has sent, which the operator may know (ADR 0014). The participant still sees only how many have answered
- [ ] An observer whose link is live and who has not sent is reminded once a week. Reminders end when they send, when the link expires and when answer collection freezes, and start again if it unfreezes
- [ ] Reminders stop on revoke, reissue or removal, and when the participant withdraws consent
- [ ] The email names the participant, says how to ask not to be reminded, and carries a button to a page that makes a fresh link when pressed and takes the observer into the assessment. The old link stops working only then. The button's address is signed, names the invitation without being a way in, and is refused once the observer has sent, once the link expires or changes, and once collection freezes
- [ ] Nothing in a reminder or its absence tells the participant who has answered

**Context**

- Weekly, ending when the link expires, with no separate deadline (developer's call, 14 Oct)

- The button leads to a page with a press rather than making the link on opening, because mail filters open every address in a message. ADR 0009 records the button as the one way an observer gets a fresh link without the participant
- Email on staging comes from a temporary domain (ticket 26); real observers need the production email provider and its processor agreement first
- The participant shares each link themselves; the system sends no invitation email. A reminder is the first message an observer gets from it
