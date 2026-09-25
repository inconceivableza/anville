# 16: Comparison screen

**What to build:** The distinctive claim, on screen: the participant's view beside observers' views, the biggest gaps, and how much observers agree, using ticket 14's numbers. When every contributing observer is test data, the screen says so. Section 1 gains its "comparison viewed" requirement, designed so a participant is never locked out while waiting for observers.

**Blocked by:** 14 (Observer responses, aggregation and suppression)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] The comparison shows APEST(d) and PEP for the participant and observers side by side, only when the minimum is met; below it, the explanation from ticket 14
- [ ] The five largest gaps across both frameworks are listed, with "Others rate higher" or "You rate higher"; a gap of five percentage points or more is significant and less is a modest gap (both values set in the pathway document)
- [ ] Agreement is banded by observer range: up to 6 strong agreement, up to 14 some variation, above that divided views; a distribution strip shows each observer's value
- [ ] The four reflection prompts (hidden strengths, blind spots, confirmed strengths, the surprise) are authored content
- [ ] When every contributing observer is marked as test data, a banner says the comparison is illustrative; the prototype's random, unlabelled fabrication is not reproduced and there is no separate fixture
- [ ] Section 1's gate gains a "comparison visited" clause (a new named clause type, ADR 0003), satisfied by visiting the comparison in either state, including the below-minimum explanation. The prototype never sets its flag in the empty state, which would lock every later section until three observers had answered
- [ ] Journey tests cover the shown state, the suppressed state, the illustrative banner, and that visiting the suppressed state satisfies the clause

**Carried from 06**

- The prototype's comparison screen used slightly different hexes for the same constructs (L4110) from its results screen (L4038). The results page kept the results screen's, as the stylesheet's `--tone-*` variables, and a construct's tone is named in the pathway document. Reuse those tones here rather than bringing the second set back
