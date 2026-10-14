# 55: Answer collection freezes once results are viewed

**What to build:** Once a participant looks at a comparison showing standings, their observers' answer collection freezes: no more observer assessments are accepted, so the results stop changing under them, and they are told so before they look. Withdrawal still wins: an observer who withdraws afterwards has their answers removed.

**Blocked by:** A4-45 (Withdrawn consent closes observers' and the coach's links)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Observers (ADR 0005); Feedback from others; Open content and product items; Legalities are parked, not forgotten

- [ ] With at least the minimum number of answers in, "Compare with how others see you" first shows a confirmation: how many of the people invited have answered, and that once they look no more answers are added. When everyone invited has answered it still shows, more mildly, saying they can no longer add anyone. Below the minimum the press shows the explanation as today and freezes nothing
- [ ] Once frozen, an observer's page says no more answers are being taken and accepts none, and the participant can no longer add people or issue or reissue observers' links, with the page saying why. The coach's link is untouched
- [ ] An observer who withdraws after the freeze has their answers deleted and the comparison worked out again without them. If that leaves fewer than the minimum, collection unfreezes: links that still work can send again, and the participant may invite someone new
- [ ] The observers' privacy notice says they can withdraw at any time and their answers will be removed, and that once the participant has looked at the combined results no new answers are added
- [ ] An ADR records the freeze: what triggers it, what it refuses, that it unfreezes below the minimum, and that withdrawal always wins over a frozen comparison

**Context**

- Freezing on withdrawal was considered and dropped: keeping figures that include a withdrawn observer is lawful only if they are no longer that observer's personal data, which with three observers known to the participant cannot be relied on. The cost accepted is that the participant can see the count go down
- This settles the spec's "closing collection" item, and most of "batched release": a participant can no longer send one more link and see exactly what that person added
- Reminders end when collection freezes and start again if it unfreezes (A6-43)
