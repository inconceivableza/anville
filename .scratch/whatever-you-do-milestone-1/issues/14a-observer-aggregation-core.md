# 14a: Observer aggregation core

**What to build:** Given several observers' sorts of one participant, work out what others see in them: each observer's profile on its own, then the average across observers, and nothing at all below the minimum number of observers. This is the pure core the comparison (16) reads, with no storage or screens.

**Blocked by:** 06 (Scoring core and results page)

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Spec:** Observers (ADR 0005); The instrument and scoring; Testing Decisions

- [ ] Each observer's sort is normalised on its own, with the frozen scoring method, before any averaging; per-observer values are kept for the distribution strip
- [ ] The output gives mean APEST(d) and PEP percentages, each construct's per-observer values, and the count of observers
- [ ] Only observers' sorts go in; the participant's own view never counts towards the observer statistics
- [ ] The minimum number of observers is set in the pathway document and starts at three; below it the output holds the count and no numbers, never a partial distribution
