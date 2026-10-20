# 59a: Too close to call within 5%, and a generalist only when flat

**What to build:** The tie-break asks only when a framework's leaders really are too close to call, and on every framework that is, as the content owner's prototype does. A participant is told they are a generalist only when both frameworks are flat, with every construct "Present" or "Strong", so a participant whose results show a clear leader is never told it.

**Blocked by:** D3-30c (Re-weighted results)

**Status:** resolved

**Handed over:** the observers' standings on the comparison, to 59b

**Sprint:** 2b (continued from 19 Oct)

**Spec:** The instrument and scoring; The instrument and results

- [x] A framework is too close to call when its leader's unrounded share is at most the document's percentage (5% in *Whatever You Do*) more than another construct's, up to the document's cluster size, leader first; a share of 0 is never too close to call
- [x] Standings are worked out from unrounded shares, wherever a standing is shown (the participant's here; the observers' mean and each observer's on the comparison finished by 59b)
- [x] A participant flat on both frameworks is told they are a generalist and gets no pairs; one too close to call on both but not flat is never told it, and gets pairs on both
- [x] With both frameworks too close to call, the pairs alternate between them, every pair in two rounds while the budget allows; past it, second rounds go first, then the least important pairs (3rd against 4th before 1st against 2nd)
- [x] With one framework too close to call, its pairs are planned as today

**Context**

- Decided in ADR 0018, which explains how the tie-break works with a worked example
- Reported on the sprint 2b review walk: a profile with Deacon "Strong" at 20.17% and Evangelist at 19.60% was shown the generalist box, because the 4-point rule on rounded percents tied four roles
- The pair plan is worked out afresh from the stored result, so a staging participant told "generalist" under the old rule meets the pairs when they next open their results; staging holds fake data, so this is accepted
- Prototype reference: `Prototypes for reference/tiebreaker-prototype-v2.html`, its notes' "Shared budget" (followed here) and its `planTieBreak` (which always drops second rounds when both are tied)
