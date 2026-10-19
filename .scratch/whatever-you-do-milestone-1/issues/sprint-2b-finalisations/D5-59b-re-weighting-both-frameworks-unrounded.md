# 59b: Re-weighting both frameworks, drawn unrounded

**What to build:** A participant who answered pairs on both frameworks sees each framework re-weighted by its own answers, with its own outcome, and every profile is drawn at its exact shares, so two constructs a fraction apart no longer look identical.

**Blocked by:** D4-59a (Too close to call within 5%, and a generalist only when flat)

**Status:** ready-for-agent

**Sprint:** 2b (continued from 19 Oct)

**Spec:** The instrument and scoring; The instrument and results

- [ ] Each framework that had pairs is re-weighted from its own answers, with its own outcome: "Separated", genuinely balanced, or every pair skipped
- [ ] The re-weighted result keeps its unrounded shares beside the whole numbers it stores
- [ ] Every dot and bar sits at its unrounded share: on the results page, Section 1's results, the comparison (observers' averages included) and the coach's view
- [ ] The generalist's wording says the profile is flat on both frameworks, never that its top results are too close to call; drafted from the prototype's balanced verdict, for the developer's review
- [ ] What the results page says of a framework (its standings and any tie-break or generalist wording) never contradicts itself

**Carried from 59a**

- [ ] The observers' standings on the comparison (their mean and each observer's in the spread) are worked out from unrounded shares, as the participant's now are
- Until this ticket, a participant with pairs on both frameworks has only the first framework re-weighted, by its own answers; the other keeps its sort's result
- The participant's standings are read from the stored result's unrounded shares: a sort's are worked out again from the raw values it keeps; any other result's (a re-weighted one) are its whole numbers until it keeps its own

**Context**

- Decided in ADR 0018
- Reported on the sprint 2b review walk: Deacon at 20.17% and Evangelist at 19.60% were drawn at the same place, both from 20
- The prototype's balanced verdict: "That's a real result rather than an error: these sit equally in this person. Better to say so than force a winner."
