## Persistence, Collaborator Flows & Simulation Seams

> ✨ Extracted from the prototype source with AI assistance; line references verified against the file.

Scope: storage, save-file format, observer/mentor/trusted-contact flows, email simulation, demo mode, the future letter. Assessment maths, section gates and block taxonomy are covered elsewhere.

Everything below is client-side. There is no server anywhere in this file. No `fetch`, no `XMLHttpRequest`, no form `action`.

---

### 1. Persistence

All save/resume logic lives in one IIFE at **L7413–7877**, exposed as `window.wydSave` (L7866). Public surface: `save`, `exportFile`, `importFile`, `clear`, `snapshot`, `available`.

#### localStorage keys — there are only three

| Key | Written | Holds |
|---|---|---|
| `wyd_progress_v1` (`KEY`, L7416) | `doSave()` L7596 | The entire progress snapshot, JSON |
| `wyd_tester_intro_seen_v1` (`TI_KEY`, L7032) | `tiMarkSeen()` L7044 | Literal `'1'` — tester briefing dismissed |
| `__wyd_t__` | `storageWorks()` L7450 | Transient write/delete probe, removed immediately |

`storageWorks()` (L7448) decides `autoOK`. If localStorage throws — Safari on `file://` — auto-save silently disables and the UI degrades to manual save-file only (message at L7775).

#### Write triggers (L7855–7863)

Capture-phase `input`, `change` and `click` listeners on `document` → `queueSave()` → 600 ms debounce → `doSave()`. Plus a 15 s interval, `visibilitychange` (hidden), `pagehide`, `beforeunload`. Aggressive and untargeted: every click anywhere re-serialises the whole workbook.

#### Snapshot shape — `snapshot()` L7476

```jsonc
{
  "v": 1,
  "at": "2026-09-18T10:22:31.005Z",
  "fields": {
    "wbUserName": "Ed",
    "gifts-summary": "…",
    "chk:mentor-confirmed": 1,      // checkbox/radio, only when checked
    "sld:g12": "64"                 // assessment slider, keyed by data-id
  },
  "wb": { /* wbState      */ },
  "sa": { /* saState      */ },
  "cl": { /* callingState */ },
  "tl": { /* timelineState*/ },
  "rm": { /* roadmapState */ },
  "lt": { /* letterState  */ },
  "bl": { /* _baselineAnswers */ },
  "screen": "screen-hub",
  "inApp": true
}
```

The state-object key map is at **L7478**: `wb→wbState, sa→saState, cl→callingState, tl→timelineState, rm→roadmapState, lt→letterState`, plus `bl→_baselineAnswers` (L7480).

`collectFields()` (L7458) sweeps every `textarea[id], select[id], input[id]`. Skips: `mentorLink`, any id starting `__`, and types `button/submit/file/range`. Range inputs are excluded because assessment sliders carry `data-id` not `id` and are collected separately (L7468) with the `sld:` prefix.

**This is a DOM-scrape, not a model.** The saved "fields" bag is keyed by DOM element id. Any id rename in a rebuild silently orphans saved data. There is no schema.

#### Restore — `restore(d)` L7539

Order matters and is fragile: `assign()` each state object (L7543–7549) → stash `pendingFields` → `enterApp()` if `d.inApp` → `applyFields(false)` → `rerender()` → `applyFields(true)` → navigate to `d.screen` → `applyFields(true)` **again** (L7574). Three passes because re-renders blow away freshly-applied values. `applyFields(true)` means "only fill if currently empty".

`assign(target, src)` (L7490) is a shallow `for…in` copy — nested objects are replaced wholesale, never merged.

Two screens can't just be shown, they must be rebuilt: `screen-score` → `buildScoreScreen()`, `screen-comparison` → `buildComparison()` (L7562–7565). Anything that throws falls back to `screen-hub`.

#### Versioning — absent

`v:1` is **written at L7477 and never read**. `restore()` does no version check, no migration, no shape validation beyond `typeof d === 'object'`. A v1 file will be force-fed into any future build. **CONFIGURABLE / migration:** the rebuild needs a real versioned document schema from day one; there is nothing here to inherit.

#### `scrub()` — L7433 — SECURITY

```js
function scrub(v){
  if (typeof v === 'string') return v.replace(/[<>]/g, '');
  // recurses arrays and plain objects, returns everything else untouched
}
```

Applied **only on file import** (L7645: `restore(scrub(JSON.parse(r.result)))`). **Not applied to the localStorage read path** at L7841–7845 — that JSON goes into `restore()` raw. The comment at L7431 is honest about why it exists: the workbook renders user text straight into `innerHTML`.

What it fails to do:

- **SECURITY — prototype pollution.** Both `scrub()` (L7442, `o[k] = …`) and `assign()` (L7492, `target[k] = src[k]`) copy attacker-controlled keys onto objects with plain assignment. A save file containing `__proto__` reaches `Object.prototype`. Nothing filters key names.
- **SECURITY — localStorage bypass.** Anything that can write `wyd_progress_v1` (any XSS, any shared-origin script) skips the scrubber entirely.
- **Does not neutralise** `javascript:` URLs, `&#60;` entity-encoded brackets, or CSS/attribute-context injection — it only assumes HTML-tag context.
- **Corrupts legitimate input.** A participant writing "I was < 50% sure" loses characters on every export/import round-trip. Lossy sanitisation applied to user prose is a data-integrity bug, not just a security shortcut.

The rebuild should escape on output (as `escLetter()` at L7196 correctly does) rather than mutate on input.

#### Export / import

`exportFile()` L7619 — `Blob` → object URL → synthetic `<a download>`. Filename: `whatever-you-do-<slug(name)>-<YYYY-MM-DD>.json`, where `slug()` (L7615) lowercases and hyphenates, falling back to `progress`.

`importFile()` L7633 — synthetic `<input type=file>`, `FileReader.readAsText`, parse → scrub → restore. Any failure produces one generic `alert()` (L7647). No partial recovery, no diff, no confirmation before overwriting current work.

#### Clear — `clearSaved()` L7733

Two-click confirm (L7734–7739, 6 s disarm) because sandboxed previews ignore `window.confirm()` (comment L7671). Then: remove the key → restore every state object from `PRISTINE` (deep clones taken at init, L7830) → `wipeFields()` → `backToStart()` → `redrawAll()`. `wipeFields()` (L7685) deliberately spares ids beginning `demo` or `wydSave`.

Note `cleared` is reset to `false` at L7760, so auto-save immediately resumes from the clean slate.

---

### 2. Observer / trusted-contact flow — the load-bearing illusion

#### Invitation — there is no invitation

```js
// L6405
link.value = window.location.href.split('?')[0] + '?observer=true';
```

**SECURITY — there is no token.** The "invite link" is a static query flag. Consequences for the rebuild, all of them load-bearing:

- No observer identity is encoded. Every observer gets a byte-identical link.
- No binding to the participant. The link is just *this page*.
- No expiry, no revocation, no single-use, no consent record.
- Detection is a substring test: `window.location.search.indexOf('observer=true') > -1` (L6412) → show `screen-respondent-welcome`.
- Mentor is the same pattern: `?mentor=true` (L3058).

Nothing about tokens, delivery, or response-tracking exists to migrate. It must be designed from scratch.

#### Trusted-contact capture

`addContactRow()` L3061 — appends a row; note the new row is **pre-filled** with `Sam` / `sam2@example.com` (L3067). `checkContactsReady()` L3071 gates Continue on **≥ 5** rows having a name and an email containing `@` past position 0 (L3077, L3079). **CONFIGURABLE:** the minimum-5 threshold is hardcoded in three places (L3079, L4223, and the copy at L2362).

`submitContacts()` L3087 writes `wbState.contacts = [{name, email}, …]`. `skipContacts()` L3098 sets it to `[]`. Skipping is unrestricted and has no downstream consequence — the comparison screen fabricates observers regardless (see below).

#### Observer questionnaire — the real questions

From `submitObserverForm()` L6375. Identity: `respondentName`, `respondentRelationship` (a select; `startRespondentForm()` L6358 validates both are non-empty). Then a card-sort + slider pass reusing the participant's 36 items, plus seven free-text fields:

| Field id | Question |
|---|---|
| `q-energised` | What energises them / where they seem most alive |
| `q-qualities` | Three best qualities |
| `q-new-skill` | One new skill to develop |
| `q-existing-skill` | One existing skill to develop further |
| `q-character` | One character area to develop |
| `q-change` | Biggest change observed in them |
| `q-struggles` | Tasks or work they struggle with |

**CONFIGURABLE:** all seven are hardcoded DOM ids read by hand. In the rebuild these are a configured question set attached to an observer questionnaire.

#### Where observer answers go

```js
// L6392
console.log('Observer submission:', data);
showScreen('screen-resp-thankyou');
```

**Nothing is persisted, transmitted, or aggregated.** The thank-you screen is unconditional. The seven qualitative answers are collected into `data.answers` and discarded. Not one observer answer ever reaches the comparison UI — the qualitative questions exist only as a UX sketch.

#### SECURITY / BUG — observer and participant share one global

`startRespondentForm()` (L6365–6368) **overwrites `saState`** — the participant's own assessment state — with a fresh shuffled deck and empty buckets:

```js
saState.sortDeck = shuffle(giftItems.slice());
saState.sortHistory = [];
saState.buckets = {1:[],2:[],3:[],4:[],5:[]};
saState.giftScores = {};
```

There is one `saState` for both roles. An observer opening `?observer=true` in a browser that holds participant progress destroys that progress — and the 600 ms auto-save then writes the destruction to `wyd_progress_v1`. The rebuild needs participant responses and observer responses as separate, separately-owned records. The `// TODO: secularise items for observer` at L6364 also flags that observers currently see the participant's religious framing.

#### The fabrication — `generateDummyObserverData(self)` L4221

This is the single most important thing in this document. The self-vs-others comparison is **entirely invented in the browser at render time.**

```js
var contacts = wbState.contacts || [];
var n = Math.max(5, contacts.length);   // L4223 — always ≥5 observers, even if you skipped
```

Fixed bias and spread tables, hardcoded (L4226–4231):

```js
var apestBias   = { A:-3, P: 2, E:-5, S: 7, T: 4, d:-2 };
var pepBias     = { ponder:-4, ideate:-2, assess: 5, rally: 3, facilitate: 6, deliver:-3 };
var apestSpread = { A:  6, P: 4, E: 3, S: 8, T: 5, d: 7 };
var pepSpread   = { ponder: 5, ideate: 9, assess: 4, rally: 7, facilitate: 3, deliver: 6 };
```

Per observer `i`, per dimension (L4234–4249):

```js
noise = Math.round((Math.random() - 0.5) * 2 * spread);   // uniform ±spread
value = clamp(1, 40, self.pct + bias[dim] + noise);
```

Then each synthetic observer's profile is normalised so their APEST sums to 100 and their PEP sums to 100 (L4253–4259), and the per-dimension mean across observers becomes `obs.apest[id]` / `obs.pep[id]` (L4262–4269).

`Math.random()` is **unseeded**. The comparison is non-deterministic: the same participant sees different "feedback from the people who know them" on every page load, and after a restore.

The biases are editorially chosen to manufacture a narrative — Shepherd `+7` and Teacher `+4` mean others "see more pastoral gift in you than you do"; Evangelist `-5` means they see less. `apestSpread.S = 8` makes the dimension with the largest positive bias also the most "divided". This is designed to look insightful.

Returned shape (L4224) — **this is the contract real aggregation must satisfy**:

```jsonc
{
  "apest":           { "A": 18, "P": 14, "E": 9, "S": 31, "T": 20, "d": 8 },  // mean %, sums ~100
  "pep":             { "ponder": 12, "ideate": 14, … },                        // mean %, sums ~100
  "apestIndividual": { "A": [16,19,21,15,18], … },   // one normalised % per observer
  "pepIndividual":   { "ponder": [10,13,…], … },
  "n": 5
}
```

Stored at `saState.observerData` (nulled in `startFreshAssessment()`, L3890). In-memory only — though note it *is* inside `saState`, so it **is** serialised into `wyd_progress_v1` and into export files. Fabricated data therefore persists and is indistinguishable from real data on reload.

#### What the comparison UI computes — `renderDistribution(individual, selfPct, color)` L4275

Per dimension, from the individual array only:

- `lo` / `hi` — min and max (L4283)
- `avg` — mean, rounded (L4284)
- `range = hi - lo` (L4285)
- Agreement band (L4286) — **CONFIGURABLE thresholds**: `range ≤ 6` → "Strong agreement" (green `#2E7D32`); `≤ 14` → "Some variation" (amber `#F9A825`); else "Divided views" (red `#E53935`)
- Axis scale `0 → max(selfPct, max(individual)) + 4` (L4277)

Renders a band from `lo` to `hi`, one dot per observer, and a "You" marker at `selfPct`.

**So real data slots in cleanly**: supply `apestIndividual` / `pepIndividual` as arrays of per-observer normalised percentages plus `n`, and both the averages and the distribution strip work unchanged. That is the whole integration surface. What must be added around it: minimum-n suppression before any distribution is shown (5 dots from 5 named contacts is trivially de-anonymising), consent, and participant-controlled sharing. **SECURITY — anonymity:** with `n` small and contacts named by the participant, a distribution strip plus one outlier dot identifies the dissenter. No aggregation threshold exists in the prototype because there is no real data to protect.

---

### 3. Mentor flow

- Capture — `mentor-name`, `mentor-email`, `mentor-confirmed` checkbox → `wbState.mentor = {name, email}` (L3032).
- Skip — `skipMentor()` L3036 sets `wbState.mentor = null`. Unrestricted.
- Post-onboarding both paths route via `returnToHubOrGifts()` (L3041), which respects `wbState.journeyType`.
- Link — `?mentor=true` (L3058), generated once in an IIFE at page load, so it reflects the URL at load time. `copyMentorLink()` L3045 uses the deprecated `document.execCommand('copy')`.
- `renderMentorStatus()` L3271, `openMentorScreen()` L3287, `renderMentorBrief(section)` L5095 — per-section briefing content, hardcoded. **CONFIGURABLE:** briefing purpose/duration/questions/watch-outs per section belong in pathway configuration.
- `copyMentorText()` L3811 — copies `#mentorPreviewContent` as plain text via `navigator.clipboard` with a `<textarea>` + `execCommand` fallback.

#### The two `doc.write` preview windows

**L3834 `printMentorPreview()`** — creates an off-screen `<iframe>` (`left:-9999px`), writes a minimal light-only document, injects `#mentorPreviewContent.innerHTML` verbatim, calls `contentWindow.print()`, removes the frame after 2 s. Triple fallback to `window.print()`. This is a print shim, not a sharing mechanism — the mentor only ever receives whatever the participant manually copies or prints.

**L7361 `printLetter()`** — `window.open('', '_blank')`, writes a Georgia-serif document containing `escLetter(buildLetterText())` with `\n` → `<br>`. Correctly escaped here. Handles popup-blocking with an alert pointing at the copy button.

---

### 4. Email / delivery simulation

**Every** email in the product is a preview or a no-op.

| Surface | Reality |
|---|---|
| Observer invite | No email. Copy-a-link only (L6396). Preview text on `screen-invite` (L1853–1864) describes what observers "will receive". |
| Mentor invite | No email. Copy-a-link only (L3045). |
| Observer submission | `console.log` (L6392). |
| Future letter | `lt-email` captured and format-checked only (L7379). Never sent, never scheduled. |
| Newsletter | Input at L1436 is literally labelled `placeholder="Demo only – not connected"`. |

Real implementation needs, per surface: a tokenised recipient record, delivery state (queued/sent/bounced/opened), a template bound to pathway configuration, unsubscribe/consent, and for the letter a durable server-side scheduler that survives a year of calendar time. None of this is sketched.

---

### 5. Demo / tester mode

**`var demoMode = true` (L6529) — demo mode is ON by default.** Toggle is `#demoModeCheck`, `checked` in markup (L6519), `setDemoMode(on)` at L6581. Screen navigation calls `if (demoMode) fillDemoData(id)` (L6678).

`fillDemoData(targetId)` L6798 sets `window._demoSeeded = true` and populates:

- Account — `Ed` / `ed@example.com` / dob `1990-05-15` / reason `exploring` (L6801)
- Baseline — `{bible:6, gifts:5, call:4, plan:3}`; post-baseline `{bible:8, gifts:8, call:7, plan:7}` (L6809–6810) — pre-loaded improvement
- Mentor — `Sarah Williams` / `sarah@example.com`, confirmed checkbox ticked (L6813)
- Contacts — five: Tom, Grace, Peter, Hannah, Mark, all `@example.com` (L6819)
- `onboardingComplete` — set `true` **unless** the target is one of the five onboarding screens (L6826), so the linear flow isn't bypassed when you're testing it
- Pillar textareas — the string `'This is placeholder demo text to illustrate how the completed field looks in context.'`
- Timeline — 5 chapters (Childhood → Current season) and 11 markers (L6842–6859)

`seedDemoAssessment()` L6787 — `saState.giftScores[id] = Math.floor(Math.random()*70) + 20` for all 36 items (range **20–89**), then sets `completed = true` and `comparisonViewed = true`. A second unseeded RNG.

`applyDemoDataToDOM(id)` L6755 re-applies on each screen show, guarded by `demoMode && _demoSeeded`.

#### PII placeholders (L6941–6957)

A separate mechanism from demo mode. Every name/email field **ships pre-filled in the markup** with reserved `example.com` values so testers never type real people's details: `wbUserEmail: alex@example.com`, `mentor-email: sam@example.com`, `lt-email: alex@example.com`, `newsletter-email: you@example.com`, and `PII_CONTACT_EMAILS = ['jo@','priya@','chris@','dani@','rob@','sam2@'…]`. Applied/reapplied by `applyPiiPlaceholders()`.

#### Is demo state distinguishable from real state in storage? **No.**

This matters for the question of a safe admin preview mode. The snapshot at L7476 carries `v`, `at`, `fields`, the six state objects, `bl`, `screen`, `inApp` — **and no provenance flag**. `demoMode` and `_demoSeeded` are plain globals, never serialised. Demo-seeded `wbState.account`, fabricated `saState.giftScores`, the 11 demo timeline markers and `saState.observerData` all land in `wyd_progress_v1` and in exported `.json` files looking exactly like participant work. `wipeFields()` spares `demo*` ids but that only protects the tester controls, not the seeded content.

A rebuild cannot retrofit a flag onto existing prototype exports. Preview/test data needs to be a first-class server-side distinction (separate records, or an explicit `is_preview` on the response document) — not a client global.

#### Tester briefing

Four-step overlay `#testerIntro` (L6447), `TI_TOTAL = 4` (L7034). `showTesterIntro()` L7072 auto-fires on load unless `tiSeen()`. Persistence via `wyd_tester_intro_seen_v1` with an in-memory `tiSeenMemory` fallback for blocked storage. Keyboard: Escape closes, arrows navigate (L7090–7095). Explicitly labelled *"not part of the product"* (L7031).

---

### 6. The future letter

`var letterState = { sealed: false, sealedAt: null }` (L7103) — that is the entire persisted model.

#### One field, not many

```js
// L7105
var LETTER_FIELDS = [ { id:'lt-message', label:'My letter' } ];
```

**There is a single textarea.** The prompts visible on screen are static copy above one box, not separate captured fields. The other `lt-*` ids are: `lt-date`, `lt-email`, and two **buttons** — `lt-fill-calling`, `lt-fill-steps` — which insert recap text into `lt-message`.

#### Composition

`renderLetter()` L7140 prefills `lt-email` from `wbState.account.email` and `lt-date` from `letterDefaultDate()` (L7134) — **today + 1 year**, hardcoded. **CONFIGURABLE.**

`renderLetterRecap()` L7155 pulls read-only context: `callingState.statement`; starred ideas from `callingState.ideas` filtered on `i.starred`, **capped at 4** (L7184); roadmap activities as `text (quarter)`, **capped at 5** (L7189). Empty-state copy at L7176 points back to Sections 3 and 4.

`buildLetterText()` composes the plain-text artefact: title, written-date, to-be-read date, "For <name>", rule, the calling statement under `MY CALLING STATEMENT AT THE TIME`, the message body, rule, and a hardcoded closing epigraph — *"Whatever you do, work heartily, as for the Lord and not for men. – Colossians 3:23"*. **CONFIGURABLE** (and content that must not be hardcoded in a multi-tenant pathway engine).

#### Actions

- `sealLetter()` L7373 — requires `letterAnyText()`; validates `lt-email` contains `@` **only if non-empty** (L7379, so blank passes); sets `sealed = true` and `sealedAt = new Date().toISOString()`; forces a `wydSave.save()`. Re-sealing is allowed — the button becomes "Update my letter ✓" (L7206).
- `copyLetter()` L7327 — clipboard with `execCommand` fallback.
- `printLetter()` L7361 — new window, escaped, see §3.
- "Save a copy" routes through the same export machinery.

#### What the delivery date does — **nothing**

`lt-date` is read in exactly three places: `renderLetterSealed()` (L7212) to render "It is set to find you on <date>", `buildLetterText()` for the "To be read" header line, and `collectFields()` sweeps it into `fields` like any other input. **No timer, no scheduler, no queue, no server.** The sealed message at L7401 — *"It will find you on the date you chose"* — is the most confident untruth in the prototype. Sealing is a boolean and a rendered sentence.

---

### Migration checklist implied by this document

1. Replace the DOM-id `fields` bag with a versioned response document keyed by configured question ids.
2. Version and validate the save/restore format; add migrations. Nothing here is reusable.
3. Escape on output; stop mutating user input. Filter `__proto__`/`constructor` on any external-JSON merge.
4. Build observer invitation properly: per-observer token, participant binding, expiry, consent, response persistence, status tracking.
5. Split `saState` into participant-owned and observer-owned records — currently one global shared by both roles.
6. Replace `generateDummyObserverData` with real aggregation returning the same `{apest, pep, apestIndividual, pepIndividual, n}` shape; add a minimum-n suppression rule before any distribution renders.
7. Make bias/spread/agreement thresholds, the ≥5 contacts rule, the letter's +1-year default and closing scripture into configuration.
8. Give preview/test data a server-side identity; it cannot be a client-side global.
9. Build real delivery infrastructure for four separate email surfaces, the future letter needing a durable long-horizon scheduler.
