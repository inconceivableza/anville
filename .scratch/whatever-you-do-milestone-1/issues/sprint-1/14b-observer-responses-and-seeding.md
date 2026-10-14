# 14b: Observer responses and seeding

**What to build:** Observers' answers are stored as their own records, and a seeding command creates test observers directly, so the comparison (16a) can be built and shown before, or without, the observer's own flow (15a, 15b).

**Blocked by:** 06 (Scoring core and results page)

**Status:** resolved

**Sprint:** 1 (ends 2 Oct)

**Spec:** Observers (ADR 0005); Responses, answers and results; Delivery and hosting; Testing Decisions

- [x] An observer response holds a sort answer and written answers, belongs to one participant's response, is held separately from observer identity, and carries the server-side test-data marker. It has no link to an invitation; binding one is ticket 15a's call
- [x] A participant's observer sorts can be read for aggregation from submitted responses only, together with whether every one of them is test data
- [x] A seeding command creates a fake participant, with a submitted sort and result of their own, and a chosen number of test observers with deterministic values; every record is marked as test data on the server
- [x] No endpoint or template exposes an individual observer's values or written answers to the participant
