# 27: The coach sees the strengths feedback

**What to build:** Once the participant has seen their own strengths feedback, they can tick "I'm happy for my coach to see this", and the coach who accepted through their link (ticket 13c) then sees, through that same link, the participant's results and the comparison, read-only. There is no coach account, no choosing between sections, and no coach answers beyond accepting or declining.

**Blocked by:** 13c (The coach's link)

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Implementation Decisions › Coach; Observers (ADR 0005); Testing Decisions

- [ ] The consent is offered on the results page or the comparison, only once the participant has seen it, and is refused until the coach has accepted
- [ ] With consent given, the coach's link shows the participant's results and the comparison as the participant sees them, read-only; nothing else of the participant's is visible
- [ ] The participant can withdraw consent at any time, and the coach's link stops showing them at once
- [ ] Revoking or reissuing the coach's link, or choosing another coach, ends access through the old link and clears the consent
- [ ] The coach sees the comparison only as far as it is shown to the participant: nothing below the observer minimum

**Context**

- The 2 Oct demo cut this ticket down from sharing chosen sections to one consent for the strengths feedback, the only feedback the pathway has while Sections 2–4 are hidden. Sharing other sections waits for the online journey (17–21)
- The coach preview and briefs (25) are separate, and drop to 2b first if time runs short
