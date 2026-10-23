# 81: How many more answers, or people, are needed

**What to build:** Below the minimum, the comparison signpost's status, "Waiting for answers (1 of 3)", reads as either waiting or done and repeats the side card's "Answered" meter. It says how many more answers are needed instead, wherever it shows. The Five trusted voices side card, once complete, still says "Complete" after a removal leaves fewer people with working links than it needs; it asks for another person instead, while staying complete.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 3b (coherence fixes, from 23 Oct)

**Spec:** Blocks; Engine: sections, tracks, gates, progress

- [x] Below the minimum, the comparison signpost's status reads "2 more answers needed" ("1 more answer needed" for one), on Section 1's signpost, the hub's row and the Five trusted voices side card alike
- [x] At and above the minimum, and once viewed, it reads "Ready to view" and "Viewed" as before
- [x] The Five trusted voices side card, once complete, says how many more people are needed whenever fewer have working links than it needs, as it does before it is complete
- [x] The side card still counts as complete after that removal, and what it opened stays open

**Carried from 79**

- [ ] The number of people Five trusted voices needs is written once: its gate message and its phrase for what finishing it takes ("added at least 3 people in …") say it through a `{min}` placeholder, filled from the section's own links-issued clause, and the linter refuses a number written into those texts that differs from that clause's minimum (developer's call, 23 Oct)

**Context**

- Wording settled with the developer on 23 Oct, from the coherence walk (54)
- A hub side card stays complete if its gate later fails (glossary; ADR 0019): only its words change
- The README, spec and manual checks quote "Waiting for answers (2 of 3)" and the card staying "Complete": this ticket updates those quotes
