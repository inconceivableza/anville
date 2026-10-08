# 32b: Homepage from content

**What to build:** The homepage's words, steps and figures come from authored content rather than being written into its template, so the content owner can change them without a developer.

**Blocked by:** 32a (Homepage, copied from the prototype)

**Status:** needs-triage

**Sprint:** 3 or later

**Spec:** The pathway document and versions; Studio; Out of Scope

- [ ] The page renders the same as 32a from the authored content
- [ ] Which How it works steps are greyed, and their labels, come from the content
- [ ] Authored text is shown as plain text, never treated as HTML: anything that looks like markup appears as the characters typed, as with every other authored text

**Carried from 32a**

- Lines copied as they are that promise more than the app does today, for the content owner to change once the words are authored: "answer six questions in your own words" and "20 min Written questions" (31a and 31b are deferred), "Five people who know you well" (onboarding asks for two), "we send them what they need before each conversation" (nothing is sent), and "3 conversations" (the workbook has conversations two to four)
- The forest video and its still frame are served from `frontend/public/`; whether they become authored content too is part of where homepage content lives

**Carried from 38**

- The homepage's results illustration still shows percents (24%, 29% and so on), where the results page and the comparison now show standings in words; redraw it to match when its figures become authored

**Carried from 39**

- [ ] The footer's verse (Colossians 3:23, NIV) becomes authored with its translation declared like a passage's, and the credits page's NIV notice, written into its template today, moves into content with it
- The repository's licence depends on where the scripture lives: keeping it to authored content makes it possible to leave out of an open licence (spec, Legalities are parked, not forgotten)

**Carried from 25a**

- [ ] The coach paragraph promises only what the app does about guidance for the coach: only Section 1's brief is in the app, shown on the coach's link and beside the consent on the comparison, and nothing is sent (spec, Open content and product items, "Coach briefs (ticket 25a)")

**Context**

- Open before building: where homepage content lives (the pathway document, or a document of its own per deployment), and whether How it works takes its time figures from the pathway's own time estimates

