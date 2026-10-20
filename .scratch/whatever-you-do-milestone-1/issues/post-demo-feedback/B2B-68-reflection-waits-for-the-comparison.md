# 68: Section 1's reflection waits for the comparison

**What to build:** Section 1's reflection is shown but cannot be written until the participant has seen their comparison with enough answers in, with a message saying so. While that is all Section 1 waits on, the hub's next step passes over it to whatever else is open, and with nothing else open says it is waiting on answers.

**Blocked by:** B1B-67a ("How others see you" card in Section 1); B1A-66 (Section 2 opens on the Strengths assessment)

**Status:** ready-for-agent

**Sprint:** 3a (from 20 Oct)

**Spec:** Blocks; Engine: sections, tracks, gates, progress

- [ ] Until the comparison is "Viewed" (67a), the reflection is shown disabled with "This opens once you've seen how others see you. That needs at least 3 of the people you invited to answer.", and a save to it is refused, with or without JavaScript
- [ ] Once viewed it can be written, and stays so even if withdrawals later unfreeze collection
- [ ] While Section 1's only unmet requirements wait on the comparison, the hub's next step is the next open section instead
- [ ] With nothing else open, the panel reads "Waiting on answers" / "{section}'s reflection opens once at least {minimum} of the people you invited have answered and you've seen how others see you.", with a button to Section 1
- [ ] The waiting is authored on the block in *Whatever You Do* only; the faithful port shows the reflection once the sort is done, as the original prototype does

**Carried from 67a**

- "Viewed" is kept on the response per sort, beside the visits; either "Compare with how others see you →" (the results page's or the card's) records it when pressed with the minimum in, and only the demo retake takes it back

**Context**

- ADR 0019 records why, and that the press that unlocks the reflection is the one that freezes collection
