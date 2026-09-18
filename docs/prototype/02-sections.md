## Section State Shapes & Completion/Routing Logic

> ✨ Extracted from the prototype source with AI assistance; line references verified against the file.

Extracted from `Prototype for reference/vibe-coded-prototype.html`. All line refs are to that file.

### Naming trap — read this first

The section numbering in `wbState` is **off by one** against the user-facing section numbers, because sections were renumbered during prototyping and the state keys were never migrated (L3437 comment: *"'Expressing your calling' is now Section 3"*).

| User-facing section | State flag | Set by |
|---|---|---|
| Section 1 — Gifts | `wbState.pillars.gifts` | `completePillar('gifts')` L3370 |
| Section 2 — Timeline | `wbState.pillars.timeline` | `completePillar('timeline')` L3370 |
| Section 3 — Calling statement | `callingState.statementDone` | `finishCallingStatement()` L4863 |
| Section 3 — Possibilities + role pictures | **`wbState.section2Done`** | `completeSection2()` L3436 |
| Section 4 — Growth plan | **`wbState.section3Done`** | `completeWorkbook()` L3454 |
| Section 5 — Letter | `wbState.pillars.letter` | `updateLetterStatus()` L7121 (derived, not set) |

`wbState.pillars` only ever contains three keys (`gifts`, `timeline`, `letter`, L2813). Sections 3 and 4 live in ad-hoc booleans outside it. **CONFIGURABLE:** the production model needs one uniform per-section completion record, not three different mechanisms.

---

### State shapes

```ts
// L2811
type WbState = {
  userName: string;
  pillars: { gifts: Status; timeline: Status; letter: Status };  // Status = 'not-started'|'in-progress'|'completed'
  section2Done: boolean;          // = user-facing Section 3 complete
  section3Done?: boolean;         // = user-facing Section 4 complete; NOT initialised (L3456 creates it)
  history: string[];              // screen-id stack for back button
  account?: { name: string; email: string; dob: string; reason: string };  // L2967
  mentor?: { name: string; email: string } | null;                          // L3032 / L3037
  contacts?: Array<{ name: string; email: string }>;                        // L3093
  journeyType?: 'online' | 'offline';                                       // L3043
  onboardingComplete?: boolean;                                             // L3033
};

// L5290
type TimelineState = {
  chapters: Array<{ id: number; label: string }>;            // L5927, L5936
  markers: Array<{ id: number; chapterId: number | null; type: MarkerTypeId; text: string }>;  // L5394
  nextId: number;                 // shared id counter across BOTH chapters and markers
  openChapter: number | null;
  pendingType: MarkerTypeId;      // default 'door'
  phase: 1 | 2 | 3;               // L5357 tlPhase() clamps anything else to 1
  dragMarkerId: number | null;
  threads?: string;               // NOT in the initialiser — only created by syncTimelineToFields() L5980
};

// L4311
type CallingState = {
  contribution: string; who: string; outcome: string;
  statement: string; glory: string;
  ideas: Array<{ id: number; text: string; lens: LensId; starred: boolean }>;  // L4781
  ideaId: number;
  lens: LensId;                   // currently-selected lens, default 'who'
  promptIdx: number;
  combo: string;                  // HTML string of a random two-lens mashup (L4800)
  expressions: Array<{ id: number; title: string; who: string; daily: string; needs: string; tuesday: string }>;  // L4604
  expressionId: number;
  statementDone: boolean;
  exampleOpen?: boolean;          // UI toggle, L4712
  anchorOpen?: boolean;           // UI toggle, L4749
};

// L6013
type RoadmapState = {
  activities: Array<{ id: number; text: string; category: CategoryId; quarter: string | null }>;  // L6260
  nextId: number;
  selectedId: number | null;
  draggingId?: number;            // L6289, not initialised
};

// L7103
type LetterState = { sealed: boolean; sealedAt: string | null };  // ISO string
```

Note `combo` holds raw HTML (`L4800`), and `expressions[].title/who/daily/needs/tuesday` are the real fields — there is no `body` field, but `roleHasContent()` (L4589) and `renderGrowthPlanAnchor()` (L6060) both still probe `ex.body`, a leftover from an earlier shape. Harmless but dead.

---

### Completion / readiness predicates — exact

#### Onboarding

**Account** — `checkAccountReady()` L2948, enforced again in `startWorkbook()` L2965
```
name.trim() && email.trim() && email.indexOf('@') > 0 && dob && reason
```
`reason` is a select. DOB is not range-checked. Email check is `indexOf('@') > 0` only.

**Mentor** — `checkMentorReady()` L3018
```
name.trim() && email.trim() && email.indexOf('@') > 0 && mentor-confirmed.checked
```
Skippable via `skipMentor()` L3036, which sets `wbState.mentor = null`.

**Trusted contacts** — `checkContactsReady()` L3071
```
count(rows where name.trim() && email.trim() && email.indexOf('@') > 0) >= 5
```
**The minimum is 5** — the prose summary omits this number. Skippable. `submitContacts()` L3087 stores rows where `name && email` (looser than the gate — a row with a malformed email still persists).

#### Section 1 — Gifts

`checkPillarReady('gifts')` L3315–3329
```
saState.completed && saState.comparisonViewed && $('gifts-summary').value.trim().length > 0
```
Three-part gate; gate message branches in that priority order (L3343–3350). `pillarTextareas` (L3316) maps only `gifts: ['gifts-summary']` — **CONFIGURABLE:** this is the single place a section declares which free-text fields it requires.

#### Section 2 — Timeline

`timelineIsReady()` L5331
```
chapters.length >= 3
&& markers.length >= 5
&& distinct(markers.map(m => m.type)).length >= 3
&& markers.every(m => m.chapterId)
&& threads.trim().length >= 10
```
**Bug worth carrying knowledge of:** L5340–5341 reads threads from the *DOM* (`$('tl-threads').value`) and only falls back to `timelineState.threads`. After a save/restore that repopulates state but not the DOM, or when the element is not rendered, the gate reads stale/empty. Also `markers.every(m => m.chapterId)` uses truthiness — a marker legitimately assigned to a chapter whose `id` is `0` would fail, though `nextId` starts at 1 so this never fires in practice.

Gate copy in `timelineGateMessage()` L5346–5355, branching in the same order. **CONFIGURABLE:** all five thresholds and all five messages.

#### Section 3a — Calling statement

`callingIsReady()` L4989
```
statement.trim().length >= 10
```
That is the whole gate. `contribution` / `who` / `outcome` are **not** required — they only auto-compose a draft statement (L4359). `glory` is **not** required despite being a prompted field.

#### Section 3b — Possibilities

`expressionsAreReady()` L4837
```
ideas.length >= 6 && distinct(ideas.map(i => i.lens)).length >= 2
```
Starring is **not** gated — `starred` ideas feed downstream recaps but no predicate requires any.

#### Section 3c — Role pictures

`rolesAreReady()` L4596
```
expressions.filter(roleHasContent).length >= 2
```
`roleHasContent(ex)` L4584: true if `ex.title.trim()` OR any of `who|daily|needs|tuesday` is non-empty, OR `ex.body.trim()`. **A single character in any one of five fields counts as a filled picture.** The UI copy says "Aim for three; two is the minimum" (L4619) but only 2 is enforced, and very weakly.

`goToRoles()` L4598 seeds two blank cards, so `expressions.length` is always >= 2 — the gate is really "at least 2 of them have any text at all".

#### Section 4 — Growth plan

**THERE IS NO GATE.** L6238:
```html
<button class="btn btn-primary" onclick="completeWorkbook()">Complete workbook ✓</button>
```
No `disabled`, no `id`, no readiness function, no `gp-gate` element anywhere in the file. `completeWorkbook()` L3454 sets `wbState.section3Done = true` unconditionally and advances to the closing video.

This is **stronger than the prose summary's** "does not clearly enforce a complete configured plan" — there is no enforcement whatsoever. A participant can reach Section 5 with zero activities, and the hub will report Section 4 complete. **CONFIGURABLE:** minimum activities, minimum categories covered, whether every activity must hold a quarter.

#### Section 5 — Letter

`sealLetter()` L7373
```
letterAnyText()                                     // any text in lt-message
&& (lt-email empty OR lt-email.indexOf('@') !== -1) // only validated if non-empty
```
`LETTER_FIELDS` L7105 contains exactly one field, `lt-message`. So the gate is "the letter textarea is non-empty" — no minimum length. The delivery **date is never validated** (not required, not checked for being in the future). The email is optional. Status is derived, not set: `updateLetterStatus()` L7121 writes `wbState.pillars.letter` from `letterState.sealed`.

---

### Routing & locking

Two distinct mechanisms, with very different strength.

**1. Hard guard — `showScreen()` L2836–2848.** The only genuine enforcement in the file. Runs on *every* screen change, so it survives hub clicks, browser back/forward and Demo-mode jumps:
```js
if ((id === 'screen-section2b' || id === 'screen-section2c') && !callingState.statementDone)
  id = 'screen-section2a';                         // redirect
if (id === 'screen-section2c'
    && !(callingState.expressions?.length) && !(callingState.ideas?.length))
  id = 'screen-section2b';                         // redirect
```
Note the second guard checks only that ideas/expressions *exist*, not `expressionsAreReady()` — so with 1 idea you can reach the role-pictures screen even though the Section 3b button is still disabled.

**2. Cosmetic locks — `checkSection1Complete()` L3405 and `checkSection5()` L3426.** These only toggle `style.display` on `section{N}-locked` / `section{N}-unlocked` / `section{N}-video` divs. **They hide UI; they do not prevent navigation.** Anything that calls `wbNav('screen-section3')` or `showScreen(...)` directly bypasses them entirely.

Lock chain, and what actually enforces it:

| Transition | Condition | Enforcement |
|---|---|---|
| → Section 2 visible | `pillars.gifts === 'completed'` | **cosmetic** (L3408) |
| → Section 3 visible | `pillars.timeline === 'completed'` | **cosmetic** (L3417) |
| → 3b possibilities | `callingState.statementDone` | **hard** (L2840) |
| → 3c role pictures | any idea or expression exists | **hard** (L2844), but weaker than the button gate |
| → Section 4 visible | `wbState.section2Done` | **cosmetic** (L3439, set inside `completeSection2`) |
| → Section 5 visible | `wbState.section3Done` | **cosmetic** (L3428) |
| Section 4 → complete | *(none)* | **absent** |

**Gates that look enforced but are not:** every `section{N}-locked` panel. The padlock UI is display-toggling only. For the rebuild, route authorisation must be server-side and evaluated per navigation, not rendered as hidden divs.

`hubNextAction()` L5198 is the single source of "what next" — a priority cascade returning `{step, of, sec, title, sub, cta, action, card}`. It is the closest thing to a declarative pathway definition in the prototype, and is the natural thing to replace with configuration. **CONFIGURABLE:** the whole cascade, including `of:5` (the step count is hardcoded in every branch) and all copy.

---

### Enumerations

**Marker types** — `markerTypes` L5300. Each: `{id, label, icon, color, prompt, question, ask, examples[]}`. **CONFIGURABLE — all of it, including the count.** The timeline gate hardcodes "3 of the 5 kinds" (L5351 copy says "five").

| id | label | icon | color |
|---|---|---|---|
| `door` | Open door | 🚪 | `#4A7FB5` |
| `closed` | Hardship & loss | 💔 | `#7B6CA7` |
| `person` | Person | 👥 | `#C25B56` |
| `fruit` | Lasting fruit | 🌿 | `#5B8C5A` |
| `leading` | God's leading | 🕊️ | `#B8860B` |

Full per-type prompt/question/ask/examples content is at L5301–5315 — migration content, reproduce verbatim.

**Starter chapters** — `starterChapters` L5318, offered as one-click adds:
`['Childhood', 'Secondary school', 'University / training', 'First job', 'Current season']` — **CONFIGURABLE**, and strongly UK/Western-education shaped.

**Possibility lenses** — `ideaLenses` L4383. Each: `{id, icon, label, color, blurb, prompts[]}`.

| id | label | prompts |
|---|---|---|
| `who` | Who it serves | 5 |
| `mode` | Your part in it | 6 |
| `vehicle` | What carries it | 7 |
| `wild` | What if…? | 7 |

Note the labels differ from the prose summary ("Your part in it" not "The participant's contribution"; "What carries it" not "The vehicle"). All 25 prompts at L4386–4424 are migration content.

**Role picture fields** — `ROLE_FIELDS` L4576: `who` ("Who is it for?", 2 rows), `daily` ("What would your days actually look like?", 3), `needs` ("What would it take?", 3), `tuesday` ("Describe one Tuesday in this life", 3). Plus a separate `title`. **CONFIGURABLE** — this is a clean example of a repeatable-group block type.

**Growth-plan categories** — `roadmapCategories` L6019. Each: `{id, label, color, icon, field, question, why, suggestions[]}`. The `field` key is the hidden legacy textarea id (see below).

| id | label | icon | legacy field | suggestions |
|---|---|---|---|---|
| `experiment` | Steps of faith | 🚀 | `s3-experiments` | Volunteer somewhere that tests this calling · Shadow someone doing this work for a day · Run a small side project for three months |
| `skills` | Grow gifting | 📚 | `s3-skills` | Take a course in a core skill · Find a stretch project at work · Read three books in this field |
| `character` | Character | 🌱 | `s3-character` | Establish a weekly rhythm of silence · Join a small group for accountability · Begin a monthly fast |
| `mentorship` | Mentorship | 🧭 | `s3-mentors` | Ask someone to mentor me monthly · Interview three people about their calling · Join a peer accountability pair |
| `disciple` | Disciple others | 🤝 | `s3-disciple` | Mentor someone a few steps behind me · Teach a session on what I have learned · Start a group for others exploring calling |

Each category's `question` and `why` copy at L6021–6038 is migration content.

**Quarters** — `roadmapQuarters` L6042: `['Q3 2026','Q4 2026','Q1 2027','Q2 2027','Q3 2027','Q4 2027']`. **Hardcoded absolute dates — these expire.** CONFIGURABLE, and should almost certainly become relative offsets from enrolment.

**Ordering heuristic** — `categoryTiming` L6045 maps category → allowed quarter indices:
```
character:  [0,1,2,3]     mentorship: [0,1,2]     experiment: [0,1,2,3]
skills:     [1,2,3,4]     disciple:   [3,4,5]
```
`suggestRoadmapOrder()` L6275 round-robins each category's *unassigned* activities through its slots (`slots[i % slots.length]`), leaving already-assigned activities untouched. **CONFIGURABLE** — this is a real, if simple, scheduling algorithm that needs a home in the config model.

**Mentor briefs** — `mentorBriefs` L5028, keyed `1..5`. Each: `{title, purpose, duration, ask[], watch[], avoid}`. **CONFIGURABLE.**

---

### Hidden legacy fields — the trap, precisely

Three `sync*ToFields()` functions write derived strings into hidden `<input>`/`<textarea>` elements that belong to an **earlier, abandoned domain model**. They are write-only from the state's point of view: state → DOM, never DOM → state. The summary builder and mentor-email builder read the DOM fields, not the state objects.

**`syncTimelineToFields()` L5978.** Writes into 16 legacy ids from a taxonomy that no longer exists in the UI (`opps-*`, `comm-*`, `fruit-*`, `disc-*`). Only 6 carry data; **8 are unconditionally blanked every call**:

| legacy id | written |
|---|---|
| `opps-contexts` | bulleted chapter labels |
| `opps-contacts` | markers of type `door` |
| `opps-suffering` | markers of type `closed` |
| `comm-leaders` | markers of type `person` |
| `fruit-past` | markers of type `fruit` |
| `disc-scripture-q` | markers of type `leading` |
| `fruit-threads` | `timelineState.threads` |
| `opps-closed`, `comm-prophetic`, `comm-counsel`, `comm-missing`, `fruit-now`, `disc-burdens`, `disc-seeking`, `disc-honest` | **`''` always** |

Marker → legacy-field mapping is a lossy 5→6 fan-out; chapter membership is flattened into `'• ' + text + ' (' + chapterLabel + ')'` prose. It also mutates state on the way past: L5980 writes `timelineState.threads` from the DOM. **Do not port any of this.** Rebuild summaries and mentor output from the state objects directly.

**`syncCallingToFields()` L5004.** Writes `s2-calling`, `s2-glory`, then blanks a 3×3 grid of `s2-expr{1..3}-{market,church,future}` ids and repopulates only the first column with the first three expressions — so **expressions 4+ are silently dropped from summaries and mentor emails**. `s2-expr3-church` is then overloaded to carry the starred-idea shortlist (L5021), a field name that has nothing to do with its contents.

**`syncGrowthPlanToFields()` L6247.** Writes one newline-joined string per category into `cat.field`, formatted `text (quarter)`. Round-trips lossily — quarters become part of a prose line. Calls `autoSave()`, which is an **empty stub** (L3388), as is `savePillarData()` (L3387).

---

### Absences worth recording

- **No gate at all** on Section 4 (growth plan).
- **No validation** of the letter delivery date, and none of the delivery email unless non-empty.
- **`glory`, `contribution`, `who`, `outcome`** are collected but never required.
- **Starring possibilities** is never required despite driving downstream recaps.
- `autoSave()` and `savePillarData()` are empty stubs — the section code calls them as if persistence exists.
- `wbState.section3Done` is never initialised; it is `undefined` until `completeWorkbook()` runs. `checkSection5()` L3427 coerces with `!!`.
- `updateBaselineLabel()` L2971 is an empty stub called from the baseline UI.
- Baseline ratings render as 1–10 button rows for four fixed question ids (`bl-bible`, `bl-gifts`, `bl-call`, `bl-plan`; closing copies `pl-*`) via `renderBaselineButtons()` L2978 — **CONFIGURABLE**: the scale bounds and the question set are both hardcoded, and the pre/post pairing is by id convention only.
