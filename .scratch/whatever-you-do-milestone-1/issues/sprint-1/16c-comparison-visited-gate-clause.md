# 16c: Section 1's "comparison visited" clause

**What to build:** Section 1 can be completed only once the participant has visited the comparison (ticket 16a), in either state, so a participant is never locked out while waiting for observers.

**Blocked by:** 16a (The comparison, side by side)

**Status:** resolved

**Sprint:** 1 (ends 2 Oct)

**Spec:** Engine: sections, tracks, gates, progress; Observers (ADR 0005); Testing Decisions

- [x] Section 1's gate gains a "comparison visited" clause (a new named clause type, ADR 0003), satisfied by visiting the comparison in either state, including the below-minimum explanation. The prototype never sets its flag in the empty state, which would lock every later section until three observers had answered
- [x] Journey tests cover that visiting the suppressed state satisfies the clause, and that Section 1 cannot be completed before a visit

**Carried from 29 and 09**

- The data clump these reviews found is gone: what the views read from a participant's response is already one value, `ParticipantState`, with the track's sections worked out once. Add the visit there rather than threading it through the views

**Carried from 09**

- Section 1's gate is shown as a checklist beneath "Mark complete", every clause's message listed and ticked once met, so the "comparison visited" clause appears there like any other, unticked until the comparison is visited. Section 1's reflection is held behind the Strengths assessment link until the sort is in (`holds_what_follows`), so while it is held the page shows no checklist at all
