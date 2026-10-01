# 16a: The comparison, side by side

**What to build:** The distinctive claim, on screen for the 2 Oct demo: the participant's view beside observers' views, using ticket 14a's numbers, reached from the results page. Below the minimum the participant sees an explanation and no numbers. When every contributing observer is test data, the screen says so.

**Blocked by:** 14a (Observer aggregation core), 14b (Observer responses and seeding)

**Status:** resolved

**Sprint:** 1 (ends 2 Oct)

**Spec:** Observers (ADR 0005); Agreed cut order, if time runs short; Testing Decisions

- [x] The comparison shows APEST(d) and PEP for the participant and observers side by side, only when the minimum is met, reached from the participant's results page; a participant with a result but no onboarding or completed sections (as the seeding command makes) reaches it too
- [x] Below the minimum, an explanation and no numbers, in the page or in any other response
- [x] In both states the participant sees an overall count of answers, never which invited person has answered (ADR 0005)
- [x] No single observer's values reach the participant, in either state; only the observers' means are shown
- [x] When every contributing observer is marked as test data, a banner says the comparison is illustrative; the prototype's random, unlabelled fabrication is not reproduced and there is no separate fixture

**Carried from 06**

- The prototype's comparison screen used slightly different hexes for the same constructs (L4110) from its results screen (L4038). The results page kept the results screen's, as the stylesheet's `--tone-*` variables, and a construct's tone is named in the pathway document. Reuse those tones here rather than bringing the second set back

**Carried from 14a**

- The observers' aggregate gives constructs in declaration order, while the participant's own result is ranked, so pair the two by construct id, never by position

**Carried from 14b**

- 14b's guard test covers written answers only, since no page read observer responses before this ticket
- `ObserverResponse.assessments_for(response)` gives the submitted observer assessments and whether every one is test data (False with none), ready for `aggregate()`
