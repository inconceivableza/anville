# 14: Observer responses, aggregation and suppression

**What to build:** The privacy-critical core of the comparison, independent of how observers are invited. Observer responses are stored as their own records, separate from any identity; they are normalised per observer, then averaged; and nothing is shown to the participant until the minimum number of observers has answered. A seeding command creates test observers directly, so the comparison can be built and demonstrated before, or without, the observer questionnaire.

**Blocked by:** 06 (Scoring core and results page)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] An observer response record holds a sort answer and written answers, belongs to one participant's response, and is held separately from observer identity; it carries the server-side test-data marker
- [ ] Each observer's profile is normalised on its own before averaging; per-observer values are kept for the distribution view
- [ ] The output has the shape the comparison needs: mean APEST(d) and PEP percentages, per-observer arrays, and the count of observers
- [ ] The participant's own view is excluded from the observer statistics
- [ ] The minimum number of observers is set in the pathway document and starts at three; below it the participant is shown an explanation and no numbers, never a partial distribution
- [ ] No endpoint or template exposes an aggregate, an individual observer's values, or which invited person has answered; only an overall count of answers is shown (ADR 0005)
- [ ] Observers' written answers are never exposed to the participant
- [ ] A seeding command creates a fake participant with a chosen number of test observers with deterministic values; every seeded record is marked as test data on the server
- [ ] Pure-core tests cover per-observer normalisation before averaging and suppression below, at and above the minimum; a journey test with seeded observers asserts nothing leaks below the minimum
