# 27: The coach sees the results and comparison

**What to build:** Once the participant has seen their own results and comparison, they can tick "I'm happy for my coach to see this", and the coach who accepted through their link (ticket 13c) then sees, through that same link, the participant's results and the comparison, read-only. There is no coach account, no choosing between sections, and no coach answers beyond accepting or declining.

**Blocked by:** 13c (The coach's link)

**Status:** resolved

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Implementation Decisions › Coach; Observers (ADR 0005); Testing Decisions

- [x] The consent is offered on the results page or the comparison, only once the participant has seen it, and is refused until the coach has accepted
- [x] With consent given, the coach's link shows the participant's results and the comparison as the participant sees them, read-only; nothing else of the participant's is visible
- [x] The participant can withdraw consent at any time, and the coach's link stops showing them at once
- [x] Revoking or reissuing the coach's link, or choosing another coach, ends access through the old link and clears the consent
- [x] The coach sees the comparison only as far as it is shown to the participant: nothing below the observer minimum

**Carried from 13c**

- [x] Once a coach can see results, restore the coach-selection mock-up's "What happens next" on the coach's accepted page, worded for what this ticket gives them (13c dropped it, since it promised results and a guide that did not exist)
- [x] The participant sees their coach's answer only on the coach page; point to it from the hub, beside the consent this ticket adds

**Context**

- This ticket was cut down from sharing chosen sections to one consent for the results and comparison, the only feedback the pathway has while Sections 2–4 are hidden. Sharing other sections waits for the online journey (17–21)
- The coach preview and briefs (25, since split into 25a and 25b) are separate

## Answer

- Decisions: ADR 0011; spec, Implementation Decisions › Coach and Observers (ADR 0005)
- Carried to 25a (the guide in "What happens next"), 31a (the notices' open questions and written answers), 31b (whether written answers reach the coach), 38 (the coach's view and the notices' strip wording)
