# 30: Tie-break

**What to build:** When the sort leaves the top constructs on a framework too close to call, the participant answers a few "Which is more true of you?" pairs, and the close constructs are re-weighted from their choices. Either the result separates, or the participant is told plainly that they are genuinely balanced. Most people sort close to average, and this is what makes the result say something.

**Blocked by:** 09 (Section 1 and the Strengths assessment section)

**See also:** `Prototypes for reference/tiebreaker-prototype-v2.html`, the content owner's prototype, which is the reference for behaviour and statements.

**Status:** ready-for-agent

**Sprint:** 1 (ends 2 Oct)

**Parent:** whatever-you-do-milestone-1 spec (The instrument and scoring)

- [ ] A framework is tied when two or more constructs are within a threshold of its leader (4 points by default); at most the top four enter the tie-break. Threshold, cluster size and question budget are set in the pathway document
- [ ] Pairs are always within one framework, never across APEST(d) and PEP. When both frameworks are tied they share one budget (10 by default), questions alternate between them, and pairs among the top-ranked constructs survive trimming first; when only one is tied it may use a second round with different statements
- [ ] Each pair shows one statement for each construct, in random left-right order, with a quiet label naming the framework, and "Neither fits — skip"
- [ ] Three statements per construct (36 in all) are authored content in the document, migrated from the prototype; they are separate from the 36 sort items
- [ ] Re-weighting is a second named scoring method alongside `compositional_share` (ADR 0003), so the frozen method and its golden fixtures stay as they are. The sort's stored result is kept, and the tie-break answers and the re-weighted result are stored beside it
- [ ] When the choices go in a circle, the result says the constructs are genuinely balanced rather than forcing a winner
- [ ] The results page shows the re-weighted result, with how it changed
- [ ] Decide here, with the content owner: whether someone flat on both frameworks is offered the tie-break or simply told they are a generalist; whether it runs straight after the sort or is offered from the results; whether observers get it and which result the comparison (ticket 16) uses
- [ ] Pure-core tests cover tie detection, pair planning and trimming within the budget, interleaving, re-weighting, skips and circular choices; journey tests cover a tied sort being offered the tie-break, a clear sort not being offered it, and the stored result
