# 113: Demo shortcuts for observers and the hub, and the demo notice's @example.com

**What to build:** Three of the stubs left at the handover, for showing the app, settled with the developer on 13 Nov. An observer's sort gets the participant's hidden demo profiles. The hub gets a hidden control that completes what a chosen section needs to open, making up the people and answers a real participant would have, for a walk-through. The homepage and sign-up page suggest a made-up @example.com address. All of it only where demo tools are on.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 3d (end not yet set)

**Spec:** Sprint 3d: the code review and the 30 October feedback; Operating and demonstrating; Engine: sections, tracks, gates, progress

- [ ] On a demo system, an observer's sort offers the participant's five demo profiles, revealed as the participant's is; each places the cards, about one in eight of them in "Haven't seen this", and nothing is stored until the observer sends
- [ ] On a demo system, a hidden control on the hub, revealed the same way, offers each section not yet open; pressing it completes what that section needs to open, and only that, then returns to the hub, with no email sent
- [ ] On a participant who has already started, the control only adds what is missing: no answer, observer or coach is changed or removed, and nothing goes backwards
- [ ] On the homepage and the sign-up page, where demo tools are on, a line suggests signing up with a made-up @example.com address, its example a name and two digits chosen afresh on each page
- [ ] Where demo tools are off, none of this is offered and the server refuses it

**Carried from the handover's stubs**

- Stubs 1–3 of the handover, grilled on 13 Nov; the decisions are in the spec's Sprint 3d section, "Demo shortcuts"
- Pointers (stub 1): the participant's reveal is the sort page's `data-demo-reveal` (held Alt, or a long press on the title on a phone); the participant's demo profile places the cards through the scenario loader's prefill. Pointers (stub 2): the journey tests' helpers already walk this path (through to Section 3, the coach accepting, through to the letter), and the tie-break's demo seeding shows how a demo-only write is guarded
- The changed wording goes in the wording changes document
