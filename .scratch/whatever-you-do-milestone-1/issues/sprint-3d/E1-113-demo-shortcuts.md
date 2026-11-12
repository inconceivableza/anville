# 113: Demo shortcuts for observers and the hub, and the demo notice's @example.com

**What to build:** Three of the stubs left at the handover, for showing the app. An observer's sort gets the participant's hidden "Load a demo profile". The hub gets a hidden control that completes every section up to a chosen one, making up what each gate needs, for a walk-through. The demo notice asks for an @example.com address. All of it only where demo tools are on.

**Blocked by:** None (can start immediately)

**Status:** needs-triage

**Sprint:** 3d (end not yet set)

**Spec:** Operating and demonstrating; Engine: sections, tracks, gates, progress

- [ ] On a demo system, an observer's sort offers a hidden choice of demo profile, revealed as the participant's is, which places the cards and stores nothing until the observer sends
- [ ] On a demo system, a hidden control on the hub completes every section before a chosen one, making up the wizard's answers, a sort, an accepted coach and three observers with links, and sends no email
- [ ] The demo strip and the demo notice ask people to sign up with an @example.com address; the notice's own wording changes in the deployment's values, not in code
- [ ] Where demo tools are off, none of this is offered and the server refuses it

**Carried from the handover's stubs**

- Stubs 1–3 of the handover, not grilled, with no agreed tests: grill this ticket with the developer before building
- Open (stub 2): whether the made-up observers also send evaluations, and whether the control may run on a participant who has already started
- Pointers (stub 1): the participant's reveal is the sort page's `data-demo-reveal` (held Alt, or a long press on the title on a phone); the participant's demo profile places the cards through the scenario loader's prefill. Pointers (stub 2): the journey tests' helpers already walk this path (through to Section 3, the coach accepting, through to the letter), and the tie-break's demo seeding shows how a demo-only write is guarded
- The changed wording goes in the wording changes document
