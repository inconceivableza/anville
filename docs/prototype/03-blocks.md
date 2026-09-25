## Content Block Taxonomy

> ✨ Extracted from the prototype source with AI assistance; line references verified against the file.

Extracted from `Prototypes for reference/original-prototype.html` (7,881 lines). This section covers **what can be authored and rendered**. Scoring maths, gate predicates and persistence are covered by sibling documents.

### Two surfaces, one file

The file contains two unrelated products sharing a stylesheet.

| Surface | Lines | Milestone 1? | Notes |
|---|---|---|---|
| **Marketing site** | L1247–1766 | **No** | Homepage, churches page, blog |
| **Participant app** | L1767–2760 | **Yes** | 34 `.screen` divs, one visible at a time |
| Demo/tester tooling | L6445–6526 | No | Explicitly "not part of the product" (L6446) |

The marketing surface is: hamburger nav, video hero, About, "How it works" (5 numbered features + 3 "companion" items), Impact (3 stat bars: 71%/86%/100%, plus a testimonial), Churches CTA, 3 article cards, newsletter capture ("Demo only – not connected", L1434), 5 team members + 3 advisory board members (all named "An Other", placeholder), spiritual direction, donate, contact, footer. A standalone churches page (L1590) and blog index/post pages (L1684). **None of this is participant content** — it is a brochure. Treat it as a separate CMS concern or a static site; do not model it in the pathway engine.

### Screen inventory (participant app)

Screen IDs are **legacy and misleading** — they do not match the section numbers users see. This is the single biggest trap when reading the file.

| Screen id | Line | User-facing name | Real section |
|---|---|---|---|
| `screen-wb-welcome` | L1873 | Calling Workbook (account setup) | Onboarding |
| `screen-baseline` | L1911 | Before we begin | Onboarding |
| `screen-mentor` | L1960 | Walking with a mentor | Onboarding |
| `screen-contacts` | L2044 | Who knows you best? | Onboarding |
| `screen-journey-choice` | L2111 | Choose your path | Onboarding |
| `screen-offline-hub` | L2141 | *(JS-rendered)* | Offline branch |
| `screen-hub` | L2146 | Workbook hub | Hub |
| `screen-gifts` | L2307 | Gifts & Talents | **Section 1** |
| `screen-timeline` | L2388 | Your life timeline | **Section 2** |
| `screen-section2a` | L2442 | Expressing your calling | **Section 3a** |
| `screen-section2b` | L2489 | Make a long list | **Section 3b** |
| `screen-section2c` | L2556 | Make three of them real | **Section 3c** |
| `screen-section3` | L2509 | My Growth Plan | **Section 4** |
| `screen-letter` | L2583 | A letter to your future self | **Section 5** |
| `screen-closing-video` | L2656 | You've reached the end | Closing |
| `screen-postbaseline` | L2676 | Before we wrap up | Closing |
| `screen-complete` | L2725 | Workbook Complete | Closing |
| `screen-congrats` | L2744 | Congratulations | Closing |
| `screen-sort` / `-score` / `-sa-results` / `-comparison` | L1772–1791 | Strengths assessment | Sub-flow off Section 1 |
| `screen-resp-*`, `screen-respondent-welcome` | L1793–1851 | Observer journey | Separate audience |
| `screen-invite` | L1853 | Invite others to assess you | Sub-flow |
| `screen-mentor-preview` | L2565 | Send to Mentor | Cross-cutting |

Note `screen-section3` (Growth Plan, Section 4) sits **between** `section2b` and `section2c` in source order. Ordering is entirely runtime-driven, not document order — which is exactly what a configurable engine needs anyway.

### Pathway outline

```
Onboarding
  1. Account setup        name, email, DOB, reason-for-taking (select)
  2. Baseline ratings     4 × 1–10 agreement scale
  3. Mentor setup         name, email, confirmation checkbox, copy-link  [skippable]
  4. Trusted contacts     ≥5 × (name, email), add-more                   [skippable]
  5. Journey choice       online | offline  → branches to a different hub
Hub  (all 5 sections listed; 2–5 locked behind predecessors)
  S1 How you've been designed     → Gifts & Talents
  S2 The shape of your life       → Life timeline
  S3 Putting your calling into words → 3a sentence, 3b long list, 3c pictures
  S4 Growth plan                  → quarters board
  S5 A letter to your future self → letter
Closing
  closing video → post-baseline (same 4 questions) → summary → congratulations
```

Each hub section carries: a `guide-slot` (dynamic next-step bar), title, subtitle, an intro video placeholder, and either a lock card or its pillar cards. The hub also carries a save/restore panel (L2149) and a Resource Library of 4 cards (L2249).

---

### The block taxonomy

Sections 1, 2, 3a and 4 share one repeating **pillar template**:

```
section-header-bar  (icon + title)
hint-box            ("The big question" / "The task")
scripture-full      (N passages + note + read-confirm gate)
pillar-activity-area[locked]   ← unlocked by the read-confirm
  activity-section  (activity-specific body)
  question-card(s)  (label + textarea)
  pillar-gate       (message explaining what is still missing)
  nav-buttons       (back to hub + mark complete)
```

That template is itself the strongest hint at the schema: a **section** is an ordered list of blocks, some of which gate the ones after them.

| # | Proposed type | Renders | Authorable fields | Response shape | Instances |
|---|---|---|---|---|---|
| 1 | `rich_text` | Heading + prose, optional emphasis | `heading?`, `body` (rich), `variant` (hint-box / note / plain) | — | "The big question" (L2313), "What does a mentor do?" (L1966) |
| 2 | `hint_box` | Tinted callout, bold lead-in + body | `label`, `body` | — | L2313, L2396, L2453, L2496 |
| 3 | `scripture_reading` | Passage list + reflection note + "I've read these" confirm bar | `heading`, `passages[]{reference, text, verse_markers}`, `note`, `confirm_label` | `{confirmed: bool}` | `gifts-reading` L2318 (3 passages), `tl-reading` L2399 (5), `s2a-reading` L2458 (5), `s3-reading` L2518 (4) |
| 4 | `video` | 16:9 placeholder, play button, title, duration | `title`, `duration`, `src` | `{watched?}` (not tracked) | Section intros L2164–2240, closing L2661. **All placeholders** — onclick sets text to "Coming soon..." |
| 5 | `agreement_scale` | 1–10 button row with two anchor labels | `statement`, `min_label`, `max_label`, `points` (=10) | `{value: 1..10}` | 4 baseline (L1913) + same 4 post (L2678). Rendered by `renderBaselineButtons` L2978 |
| 6 | `short_text` | Single-line input | `label`, `placeholder`, `format` (text/email/date) | `{value: string}` | `wbUserName`, `wbUserEmail`, `mentor-name`, role `title` |
| 7 | `long_text` | Labelled textarea in a `question-card` | `label` (rich), `placeholder`, `rows` | `{value: string}` | `gifts-summary` L2372, `cl-glory` L4364, all 7 observer questions L1806–1812 |
| 8 | `single_select` | Dropdown | `label`, `options[]{value,label}`, `required_highlight` | `{value: string}` | `wbUserReason` L1899 (7 options), `respondentRelationship` L1836 (6 options) |
| 9 | `checkbox_confirm` | Checkbox + inline statement | `statement` | `{checked: bool}` | `mentor-confirmed` L1988 |
| 10 | `contact_collector` | Numbered repeatable name+email rows, "+ Add another" | `min_rows`, `label`, `row_fields` | `[{name, email}]` | `contacts-list` L2065, 5 seeded rows, `addContactRow()` |
| 11 | `email_preview` | Collapsible `<details>` showing the email a third party receives | `subject`, `body` (rich), `attachment_block?` | — | Mentor invite L2004, contacts survey L2093. **Display-only; nothing is sent** |
| 12 | `share_link` | Read-only input + Copy button | `label`, `help_text`, `link_template` | — | `inviteLink` L1866, `mentorLink` L2001 |
| 13 | `choice_cards` | Large clickable option cards that branch the pathway | `options[]{icon,title,body,detail,target}` | `{chosen: id}` | Journey choice L2117 (online / offline) |
| 14 | `assessment_launcher` | Card linking into the assessment sub-flow + status chip | `title`, `body`, `cta`, `assessment_ref` | `{status}` | L2362 |
| 15 | `sentence_builder` | Fixed template with fillable slots, live preview, then a free-text override | `template` (with named slots), `parts[]{key,label,hint}`, `override_label` | `{contribution, who, outcome, statement}` | L4335–4360. Template: *"God seems to have designed me to **[contribution]** among **[who]**, so that **[outcome]**."* Plus `useBuiltStatement()` to seed the override |
| 16 | `timeline_board` | Phased builder: create chapters → drop typed markers into chapters → record threads | `starter_chapters[]`, `marker_types[]{id,label,icon,color,prompt,question,ask,examples[]}`, `threads_prompt` | `{chapters[], markers[]{text,type,chapterId}, threads}` | `timeline-area` L2434, config L5290–5316 |
| 17 | `idea_generator` | 4 lens tabs, rotating prompts, free-text idea capture, star/unstar, "shake two lenses" | `lenses[]{id,icon,label,color,blurb,prompts[]}` | `[{id,text,lens,starred}]` | `expressions-area` L2500, config L4384–4425 |
| 18 | `card_builder` | Repeatable rich cards with a title + fixed sub-fields, plus a collapsible worked example | `max_cards`, `min_cards`, `title_placeholder`, `fields[]{key,label,placeholder,rows}`, `worked_example` | `[{title, who, daily, needs, tuesday}]` | `roles-area` L2558, fields L4576–4581 |
| 19 | `planning_board` | Category-grouped activity picker (suggestions + custom) assigned across a quarter grid, reorderable, with "suggest an order" | `categories[]{id,label,color,icon,question,why,suggestions[]}`, `periods[]`, `category_timing{}` | `[{id,text,category,quarter}]` | `growth-plan-area` L2549, config L6017–6048 |
| 20 | `derived_recap` | Read-only summary computed from earlier responses | `sources[]`, `empty_state_text`, `limits` | — | See table below |
| 21 | `checklist_prompt` | "Things you might want to include" bulleted guidance | `heading`, `items[]{lead, body}` | — | `letter-considerations` L2599 (7 items) |
| 22 | `long_form_compose` | Large textarea with buttons that **inject** prior answers into the draft | `label`, `hint`, `rows`, `insert_actions[]{label, source}` | `{value}` | `lt-message` L2620 + `fillFromCalling()` / `fillFromRoadmap()` L2623 |
| 23 | `scheduled_delivery` | Email + date pair, "we'll send it back to you then" | `heading`, `note`, `email_label`, `date_label` | `{email, date}` | L2628–2641. **Nothing is scheduled** |
| 24 | `export_actions` | Save / Print / Copy button row + confirmation | `actions[]` | — | L2637 (`downloadLetter`, `printLetter`, `copyLetter`) |
| 25 | `completion_gate` | Disabled CTA + a message naming what is still missing | `cta_label`, `unmet_message`, `predicate` | `{completed_at}` | `gifts-gate` L2376, `calling-gate` L4366, `expr-gate` L4559, `roles-gate` L4700 |
| 26 | `lock_card` | Padlock panel replacing a section's content | `message` | — | `section2-locked` L2188 … `section5-locked` L2243 |
| 27 | `status_card` | Live progress chip (Not started / In progress / Complete) | `target_ref` | — | `status-gifts` L2174, `assessment-status` L2367 |
| 28 | `next_step_banner` | Dynamic "Your next step" bar with step pips, relocating to the active section | *(derived, not authored)* | — | `guide-slot-1..5` L2160–2233, logic `hubNextAction()` L5199 |
| 29 | `resource_library` | Grid of typed resource cards | `resources[]{type,title,author,description,thumb,url}` | — | L2249; types: Article / Video / Book / Podcast. All `alert('… coming soon!')` |
| 30 | `mentor_brief` | Collapsible guidance panel attached to a section handoff | `title`, `purpose`, `duration`, `ask[]`, `watch[]`, `avoid` | — | `mentorBriefs` L5028–5093 |
| 31 | `send_to_mentor` | Button producing a printable preview of a section or the whole workbook | `scope` (section id \| `all`) | — | L2176, L2192, …, L2739 |

**Not anticipated but present:** `email_preview` (11), `checklist_prompt` (21), `long_form_compose` with insert-actions (22), `next_step_banner` (28), `resource_library` (29), `choice_cards` that branch the pathway (13), and the `worked_example` sub-object inside `card_builder` (18) — a collapsible fully-worked exemplar, which is real editorial content an author would need to write per-block.

**Absent, despite being obvious:** no multiple-choice/radio question type anywhere in the participant journey (only the two `<select>`s), no file upload, no rich-text editing by the participant, and **no Section 5 mentor brief** (`mentorBriefs` stops at 4).

---

### Derived / recap blocks — the reference system

These compute content from earlier responses. Each one is an argument for an expression/reference layer in the configurator.

| Block | Line | Reads from | Produces |
|---|---|---|---|
| `renderCallingRecap` | L4890 | `saState` (top 3 APEST + top 2 PEP + persona names), observer comparison (largest gap, signed), `timelineState.markers` (counts per type; then `fruit` + `leading` items with their chapter labels, capped 4), `timelineState.threads` | "Everything you have found so far" panel at the head of Section 3a |
| `renderGiftsSnapshot` | L5127 | `saState` results + comparison | Compact recap on the Gifts page |
| `renderLetterRecap` | L7155 | `callingState.statement`, `callingState.ideas[].starred` (cap 4), `roadmapState.activities[]` with quarter (cap 5) | "Where you have got to" panel above the letter |
| `renderGrowthPlanAnchor` | L6057 | `callingState.statement`, `callingState.expressions` (filtered by `roleHasContent`) | Anchor card at the top of the growth plan |
| `cl-anchor` in `renderRoles` | L4624 | `callingState.statement` | Calling sentence pinned above the picture cards, with an Edit link |
| `dv-shortlist` in `renderRoles` | L4671 | `callingState.ideas[].starred` + lens colour/icon | Starred possibilities listed as raw material |
| `hubNextAction` | L5199 | `wbState.pillars`, `saState.completed`, `saState.comparisonViewed`, `callingState.statementDone`, `wbState.section2Done`, `wbState.section3Done` | Next-step banner target, CTA label, and **its own sub-messaging** (three different subtitles for the gifts step alone) |
| `summaryContent` | L2737 | Everything | Final completion summary |
| `fillFromCalling` / `fillFromRoadmap` | L2623 | calling statement / roadmap activities | **Mutates** the letter textarea — derived content becomes editable participant content |

Two things worth flagging for the configurator design:

- Every recap **caps and sorts** (`slice(0,4)`, `slice(0,3)`, `slice(0,5)`, `gaps.sort` by absolute magnitude). Limits and ordering are authored decisions, not incidental.
- Every recap has an **authored empty state** ("Once you have worked through Sections 3 and 4…", L7176; "Complete Sections 1 and 2 first…", L4954). Given the requirement that an unconfigured app shows an empty screen, empty-state text needs to be a first-class authorable field on derived blocks, not an afterthought.

---

### Mentor briefs (migration content, verbatim)

Structure: `{title, purpose, duration, ask[], watch[], avoid}` (L5028–5093). Rendered as a `<details>` panel by `renderMentorBrief` L5096. Labelled in-product as "Placeholder – the full guidance will be sent to your mentor with this section."

**Session 1 – Their gifts** · 45–60 minutes
*Purpose:* Help them believe what the assessment is telling them, and notice where they discount themselves.
*Ask:* Which of these results surprised you, and which felt obvious? / Where others rated you higher than you rated yourself – why do you think that gap is there? / What is something you are good at that you have stopped noticing because it comes easily? / Which of these strengths do you actually enjoy using, and which just drain you?
*Watch:* People routinely dismiss their strongest gift as "nothing special". If they wave something away, slow down and ask about it. / A low score is not a failing. Help them read the whole profile, not just hunt for weaknesses.
*Avoid:* Do not treat the assessment as a verdict. It is a conversation starter, not a diagnosis.

**Session 2 – Their life timeline** · 60 minutes
*Purpose:* Help them read their own story back and notice the threads they are too close to see.
*Ask:* Walk me through this. Which chapter was hardest to write down? / Where do you see hardship and fruit sitting in the same season? / Who shows up at the turning points, and what did they see in you? / What is missing from this timeline that you chose not to include?
*Watch:* Seasons of suffering are often where the clearest formation happened. Be gentle, and do not rush to make meaning of something still raw. / If a whole category is empty – no people, or no sense of God leading – that absence is worth asking about kindly.
*Avoid:* Do not impose your own reading of their story. Ask what they see before offering what you see.

**Session 3 – Their calling and the possibilities** · 60 minutes
*Purpose:* Pressure-test the calling statement, and make sure they have genuinely explored the range before narrowing.
*Ask:* Read me the sentence. Does it sound like you, or does it sound like someone you think you should be? / Which of these did you dismiss quickest, and why? / What would it cost you to pursue the one you starred? / Which of these could you start something toward within a month?
*Watch:* Statements that are all abstraction ("to bring hope to people") are hard to act on. Push gently for specificity. / Watch for a calling shaped entirely by what would impress others, or entirely by what feels safe.
*Avoid:* Resist narrowing it for them. Your job is to widen the field and test the options, not to pick.

**Session 4 – Their growth plan** · 45 minutes
*Purpose:* Make the plan realistic, and agree how they will be held to it.
*Ask:* Which of these will actually happen, and which is wishful thinking? / What is the first thing, and when precisely will you do it? / What is most likely to derail this in the next six months? / Who else needs to know about this plan for it to survive?
*Watch:* Over-loaded quarters are the commonest failure. Two or three real commitments beat ten aspirations. / Plans with no character or mentorship work in them tend not to last.
*Avoid:* Do not let the conversation end without a specific date for the first step, and a date to review it together.

There is **no Session 5** brief for the letter.

---

### Authored config data, verbatim

These five arrays are what an author would be configuring. They are the concrete test case for the configurator's schema.

**Idea lenses** (L4384–4425) — `{id, icon, label, color, blurb, prompts[]}`

| id | label | prompts |
|---|---|---|
| `who` | Who it serves | 5 |
| `mode` | Your part in it | 6 |
| `vehicle` | What carries it | 7 |
| `wild` | What if…? | 7 |

Example prompt (`wild`): *"Write the version where the thing you are worst at is essential."*

**Marker types** (L5300–5316) — `{id, label, icon, color, prompt, question, ask, examples[]}`

| id | label | examples |
|---|---|---|
| `door` | Open door | 3 |
| `closed` | Hardship & loss | 5 |
| `person` | Person | 4 |
| `fruit` | Lasting fruit | 3 |
| `leading` | God's leading | 5 |

`starterChapters` (L5318): Childhood, Secondary school, University / training, First job, Current season.

**Roadmap categories** (L6017–6038) — `{id, label, color, icon, field, question, why, suggestions[3]}`: `experiment` (Steps of faith), `skills` (Grow gifting), `character`, `mentorship`, `disciple` (Disciple others).
`roadmapQuarters` (L6040): Q3 2026 → Q4 2027 (6, **hardcoded absolute dates** — will expire).
`categoryTiming` (L6044): maps each category to the quarter indices it "naturally" occupies, driving the "Suggest an order" affordance.

**Role fields** (L4576–4581): `who` "Who is it for?" (2 rows) · `daily` "What would your days actually look like?" (3) · `needs` "What would it take?" (3) · `tuesday` "Describe one Tuesday in this life" (3).

**Account setup reasons** (L1899): post-secondary, graduating, job-change, redundancy, retirement, exploring, other.
**Observer relationships** (L1836): family, friend, colleague, church, mentor, other.

---

### Notes for the rebuild

1. **Hidden legacy field mirrors.** Every JS-rendered section writes its state into a block of `display:none` textareas — `opps-*`, `comm-*`, `fruit-*`, `disc-*` (L2429–2438, 15 of them), `s2-calling`/`s2-glory` (L2478), `s2-expr{1,2,3}-{market,church,future}` (L2503), `s3-*` (L2545). They exist only so the mentor-preview and summary builders can read a flat DOM. They are a **dual source of truth** and are the likeliest source of silent data loss. Note the shape mismatch: three fixed `expr` slots mirror an unbounded `ideas[]` array, and `syncCallingToFields` (L5020) writes *only starred ideas* into `s2-expr3-church` — a field whose name has nothing to do with its contents.

2. **The configurator already has a versioning problem in miniature.** `renderExpressions` (L4429) contains orphan-reference remapping: *"The lens list has changed since some people saved their progress. Anything filed under a lens that no longer exists would be counted but never shown, so move it to the first lens rather than losing it."* Silently reassigning a participant's response to the wrong category is a data-integrity bug. Once lenses are author-configurable this stops being a one-off and becomes the general case — published-version pinning plus an explicit orphan policy needs designing up front, not retrofitting.

3. **`renderBaselineButtons` (L2978) early-returns if the container already has children**, and pre/post answers share one `_baselineAnswers` map keyed by container id (`bl-*` vs `pl-*`). It works, but it means the baseline block is not re-renderable — worth knowing before porting.

4. **Gating is two-layer and uniform**: a scripture read-confirm unlocks the activity area within a screen (`confirmReading()`), and section completion unlocks the next section at the hub. Both are expressible as the same predicate mechanism.

5. **Every gate has authored "what's missing" copy** distinct from the CTA label (`expr-gate`: "Add at least six possibilities across two different lenses to continue", and L4858 substitutes "Try at least one more lens – range matters more than volume" when the shortfall is lens-variety rather than volume). Gate messaging is *conditional on which clause failed*, so a predicate needs per-clause messages, not one message per gate.

6. **Hardcoded absolute dates** (`roadmapQuarters`, Q3 2026–Q4 2027) will silently expire. Periods need to be either relative to enrolment or author-managed.

7. **Placeholder inventory**: all 6 videos, all 4 resource cards, all 5 team + 3 advisory profiles, the newsletter, the mentor briefing PDF, letter delivery, the offline workbook PDF. Plus PII notices on three screens warning the seeded data is fake (L1887, L1972, L2054).
