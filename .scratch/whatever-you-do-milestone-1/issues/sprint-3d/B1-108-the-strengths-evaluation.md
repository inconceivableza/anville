# 108: The strengths evaluation's sort, tie-break and names

**What to build:** Four things the content owner asked for that the evaluation doesn't yet do. The "How you used the buckets" summary at halfway and at the end anchors people's answers, so it goes, for participants and observers alike (feedback, "Friday 30th - updates", image 48). Red and green alone carry meaning in the sort and the results. The tie-break has "Neither is more true of me" but not the "Both are right" the checklist ticks. And the two-round prototype gives the people asked to rate someone an eighth choice, "Haven't seen this", which the build left out. Image 37 also asks for more consistent naming of the gifts.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 3d (end not yet set)

**Spec:** Sprint 3d: the code review and the 30 October feedback; The instrument and scoring; Observers (ADR 0005)

- [ ] Neither the participant's nor an observer's sort shows how the buckets were used, at halfway or at the end
- [ ] An observer can place a card in "Haven't seen this", which leaves it out of that observer's scores; the participant's sort has no such choice
- [ ] The tie-break offers "Both are right" beside "Neither is more true of me"; either keeps the pair tied, and the answer is stored as given
- [ ] Wherever the sort or the results use colour to mean something, a second cue carries it too, so it reads the same in greyscale
- [ ] Each gift has one name wherever a participant, coach or observer sees it: the results, the note on a gift that moved, the comparison, the tie-break and the coach's view

**Context**

- Prototype reference: "Haven't seen this" in `Prototypes for reference/two-round-strengths-prototype/index.html` (grep it)
- Image 37 predates the everyday names (Pioneer, Awakener…); check what still differs, such as a lower-case engine id reaching a page
- Each changed line goes in the wording changes document
