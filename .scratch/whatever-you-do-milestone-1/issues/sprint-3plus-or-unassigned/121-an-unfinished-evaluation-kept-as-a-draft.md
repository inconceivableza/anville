# 121: An unfinished strengths evaluation is kept as a draft (for consideration)

**What to build (if it is taken up):** The cards a participant, or someone rating them, has placed in the strengths evaluation are kept on the server as they go, as a draft, so a reload, a closed tab, a dropped connection or a second device picks up where they left off rather than dealing card 1 again. Nothing is scored, and nothing counts, until "Send my evaluation", as today. This is written up for consideration, not decided: the developer asked for it to be weighed after sprint 3d (hand check of 18 Nov).

**Blocked by:** None (can start immediately)

**Status:** needs-triage

**Sprint:** 3 or later

**Spec:** The slice 1 goal "progress that survives a reload and a second device"; Strengths evaluation (Two rounds); Open content and product items ("Sort card order is randomised per participant…")

- [ ] Each card placed, and each undo, is kept as a draft beside the response (or the observer's link), in the background, without holding up the next card; a failed save is retried and never blocks the sort
- [ ] Opening the evaluation again, on this device or another, restores the draft: the round, the cards placed and their buckets, the order still to come, the halfway screen if reached, and "↩ Undo last" back through what was placed
- [ ] Without JavaScript nothing changes: the sort needs it, as today
- [ ] "Send my evaluation" scores and stores the sort as today, from what was sent, and removes the draft; the server never scores or counts a draft, and nothing (the hub, the comparison, a coach's view) reads one
- [ ] A retake, a withdrawal, an observer's decline and a reissued link each remove any draft as they remove what was sent; an expired observer link keeps no draft
- [ ] The privacy page says that unsent answers are kept until sent or removed, if they are

**Context**

- Today (`frontend/src/sort.js`, top comment): "Nothing is kept before then, so a reload starts the sort again, as in the prototype." The widget's only output is the whole sort as one hidden value; `Response.submit_sort` stores it and the scored result together (`engine/models.py`). The "Which is more true of you?" pairs after it are already stored one at a time.
- Raised at the hand check of 18 Nov: other forms on the site save as they go, and the evaluation's two rounds of 72 cards take about 7 minutes, all lost to a reload. Whether that loss is worth the work is the question for triage.
- To weigh:
  - Card order is shuffled per visit and not recorded. A draft needs its order kept, so the spec's open item on recording the order is settled by this, at least for the draft.
  - The observer's sort keeps no answers on the server until sent, only the link; a draft of what someone thinks of the participant, kept before they choose to send it, is personal data the privacy page would need to cover, and may be left to the participant's own sort alone.
  - Saving per card, or every few cards, or at the halfway screen only (the cheapest: round 1 kept once done).
  - The demo profiles (fix-23) already open a sort with every card placed (`placed` in `sort.js`), so restoring a draft can build on that.
