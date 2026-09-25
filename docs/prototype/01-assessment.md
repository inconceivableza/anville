## Assessment & Scoring Engine

> ✨ Extracted from the prototype source with AI assistance; line references verified against the file.

Source: `Prototypes for reference/original-prototype.html`. All logic lives in JS block 2 (L2809–6443), concentrated at **L3934–4272**.

This is the whole engine. There is no server, no persistence of assessment results beyond `saState` in memory, and — importantly — **no thresholds, no weights, and no normalisation beyond a single percentage-of-total division**. The engine is far simpler than the prior prose summary implies. See "Corrections" at the end.

---

### 1. The two frameworks

The prototype scores **one set of 36 slider values into two independent partitions**:

| Framework | Dimensions | Code key |
|---|---|---|
| **APEST(d)** — fivefold ministry gifting *plus a sixth diaconal dimension* | Apostle `A`, Prophet `P`, Evangelist `E`, Shepherd `S`, Teacher `T`, **deacon `d`** | `item.apest` |
| **PEP** — Professional Energy Profile | Ponder `Po`, Ideate `Id`, Assess `As`, Rally `Ra`, Facilitate `Fa`, Deliver `De` | `item.pep` |

Note the `d` key is **lowercase** and is rendered as lowercase "deacon" in the UI (L4041: `a.id==='d'?'deacon':a.name`). It is a 6-dimension framework, not 5. Every id comparison in the codebase is case-sensitive on this.

Each of the 36 items carries **exactly one** APEST tag and **exactly one** PEP tag. So the two frameworks are two different partitions of the *same* 36 numbers, and their raw totals are identical. This matters: `aT === wT` always.

---

### 2. The item bank (all 36) — L3937–3973

`var giftItems = [...]`

| # | id | Label | APEST | PEP |
|---|---|---|---|---|
| 1 | `a1` | Pioneering new ideas through iteration and experimentation | A | Id |
| 2 | `a2` | Identifying the right foundations and structures to put in place | A | As |
| 3 | `a3` | Casting a compelling vision that gets people on board | A | Ra |
| 4 | `a4` | Coaching and raising up other leaders | A | Fa |
| 5 | `a5` | Building something that will outlast you | A | De |
| 6 | `p1` | Going against the grain and challenging the status quo | P | Po |
| 7 | `p2` | Having strong instincts about situations and people — and being proved right | P | As |
| 8 | `p3` | Sensing trends before others do | P | Po |
| 9 | `p4` | Using compelling, provocative methods to articulate what's wrong | P | Id |
| 10 | `p5` | Speaking hard truths that shift how people think and act | P | Ra |
| 11 | `e1` | Naturally empathetic towards people whose lives and experiences are very different from yours | E | Fa |
| 12 | `e2` | Genuinely curious about how people from different walks of life see the world | E | Po |
| 13 | `e3` | Persuading someone one-to-one about something that really matters to you | E | Ra |
| 14 | `e4` | Motivating others to spread a message or cause they believe in | E | Ra |
| 15 | `e5` | Finding fresh ways to make important ideas accessible to new audiences | E | Id |
| 16 | `s1` | Making sure nobody falls through the cracks | S | De |
| 17 | `s2` | Giving people the tools, opportunities or platform they need to succeed | S | Fa |
| 18 | `s3` | Drawing people in and getting them involved | S | Ra |
| 19 | `s4` | Seeing when someone is heading off track and needs redirecting | S | As |
| 20 | `s5` | Walking with someone through a long difficult season | S | De |
| 21 | `t1` | Mastering a subject so thoroughly you could explain it to anyone | T | Po |
| 22 | `t2` | Creating fresh analogies and frameworks that make complex ideas simple | T | Id |
| 23 | `t3` | Training people to apply what they've learned to their everyday lives | T | De |
| 24 | `t4` | Pulling together ideas from different fields and spotting the patterns between them | T | Po |
| 25 | `t5` | Assessing whether ideas and information are accurate and well-founded | T | As |
| 26 | `d1` | Supporting and resourcing other people's initiatives | d | Fa |
| 27 | `d2` | Following through on the detail until the job is done properly | d | De |
| 28 | `d3` | Bringing order to chaos — admin, systems, processes | d | As |
| 29 | `d4` | Improving how things work so processes are more effective | d | Id |
| 30 | `d5` | Seeing what needs doing and just getting on with it | d | De |
| 31 | `a6` | Imagining what an organisation or community could become | A | Po |
| 32 | `t6` | Patiently helping someone work through a problem until they get it themselves | T | Fa |
| 33 | `d6` | Getting everyone organised and moving when something needs doing | d | Ra |
| 34 | `e6` | Reading a room and knowing exactly what will resonate | E | As |
| 35 | `p6` | Spotting the talents and potential in others, and helping them see it too | P | Fa |
| 36 | `s6` | Creating environments where people genuinely connect and belong | S | Id |

Array order is **not** grouped: items 1–30 are `a1-a5, p1-p5, e1-e5, s1-s5, t1-t5, d1-d5`, then the sixth item of each dimension is appended out of order (`a6, t6, d6, e6, p6, s6`). Presentation order is randomised anyway (§3), so array order is cosmetic — but any import script must not assume grouping.

#### 2a. Design balance — a real finding

Both partitions are **exactly 6 items per dimension** (6 × 6 = 36). Verified both ways.

But the *cross-tabulation* is uneven. Only Apostle draws once from each PEP tag:

| APEST | Po | Id | As | Ra | Fa | De |
|---|---|---|---|---|---|---|
| **A** | 1 | 1 | 1 | 1 | 1 | 1 |
| **P** | 2 | 1 | 1 | 1 | 1 | **0** |
| **E** | 1 | 1 | 1 | 2 | 1 | **0** |
| **S** | **0** | 1 | 1 | 1 | 1 | 2 |
| **T** | 2 | 1 | 1 | **0** | 1 | 1 |
| **d** | **0** | 1 | 1 | 1 | 1 | 2 |

Consequence: PEP scores are structurally correlated with APEST scores in an uneven way. A participant who scores high on Shepherd or deacon can *never* accrue Ponder points from those items; a high Teacher can never accrue Rally. This is almost certainly unintentional and it biases the PEP output. **CONFIGURABLE / DESIGN DEBT** — the rebuild should either accept this as authored content or rebalance the matrix deliberately. Flag for the domain owner; do not silently "fix" it, because it changes everyone's results.

---

### 3. Step 1 — the 5-bucket sort (L3975, L3991–4015)

```js
var BUCKETS=[
  {id:5,label:'Definitely not me'},
  {id:4,label:'Not really me'},
  {id:3,label:'Average / not sure'},
  {id:2,label:'Good at this'},
  {id:1,label:'Real strength'}];
```

**⚠ The bucket ids are inverted relative to strength.** `id:1` is the *strongest* ("Real strength"), `id:5` is the *weakest*. The array is declared weakest-first so it renders left-to-right as "Definitely not me → Real strength", but the stored integer runs the other way. This is a live trap for any migration: a naive `1..5 = low..high` assumption inverts every profile.

Mechanics:
- `shuffle()` (L3978) — Fisher-Yates, `Math.random()`, **unseeded**. Card order differs every run and is not recorded. Not reproducible. **CONFIGURABLE** (deterministic/seeded order should be an option for research validity).
- Deck is all 36 items; one card shown at a time (`saState.sortDeck[0]`), counter `(done+1)/36`.
- `sortToBucket(bid)` (L4013) shifts the item off the deck, pushes its **id string** into `saState.buckets[bid]`, and pushes `{id, bucket}` onto `sortHistory`.
- `undoSort()` (L4014) pops history, removes from bucket, unshifts item back to deck front. Single-level-repeatable undo (full history stack).
- Card fly animation direction is derived from bucket: `bid<=2 ? 'fly-right' : bid>=4 ? 'fly-left' : 'fly-down'` — cosmetic only.
- `submitSort()` (L4015) builds `saState.rankedIds` by concatenating buckets in order 1,2,3,4,5 (i.e. strongest-first). **`rankedIds` is written but never read anywhere in the scoring path** — vestigial.
- Progress: `Math.round(done/36*40)` — sort phase occupies 0–40% of the bar.

Sort is **mandatory and exhaustive**: all 36 must be sorted; the continue button only appears when `sortDeck.length === 0`.

---

### 4. Step 2 — the 0–100 slider fine-tune (L4016–4023)

Seed values per bucket (L4018):

```js
var dv = {1:85, 2:65, 3:45, 4:25, 5:10};
```

| Bucket | Label | Slider seed |
|---|---|---|
| 1 | Real strength | **85** |
| 2 | Good at this | **65** |
| 3 | Average / not sure | **45** |
| 4 | Not really me | **25** |
| 5 | Definitely not me | **10** |

**CONFIGURABLE** — these five magic numbers are the entire bridge between the qualitative sort and the quantitative score. They are hardcoded inline in a rendering function.

- Sliders: `<input type="range" min="0" max="100" step="1">`, one per item, grouped under their bucket heading with the bucket's label and count.
- Empty buckets are skipped entirely (`if(!ids.length)return;`).
- If the participant never touches a slider, the seed value stands. **A participant who sorts and then clicks straight through produces a fully-formed score from bucket seeds alone.**
- `submitScores()` (L4023) reads every `.score-slider` from the DOM into `saState.giftScores[itemId] = parseInt(value)`.

State shape: `saState.giftScores = { 'a1': 85, 'p3': 10, ... }` — 36 keys, integer 0–100.

UI bug worth noting: the sort screen is labelled "Step 1 of 3" (L3996) but the fine-tune screen is labelled "Step 2 of 2" (L4017).

---

### 5. The scoring maths — `computeAll()` (L4024–4034)

This is the complete algorithm. Reproduced in full because it is short and everything else references it.

```js
function computeAll(){
  var g=saState.giftScores, s={};
  function sumA(l){var t=0;giftItems.forEach(function(i){if(i.apest===l)t+=(g[i.id]||0);});return t;}
  function sumW(tag){var t=0;giftItems.forEach(function(i){if(i.pep===tag)t+=(g[i.id]||0);});return t;}

  var aR={A:sumA('A'),P:sumA('P'),E:sumA('E'),S:sumA('S'),T:sumA('T'),d:sumA('d')},
      aT=0; for(var k in aR) aT+=aR[k];
  s.apest=[{id:'A',name:'Apostle',raw:aR.A}, ... ];
  s.apest.forEach(function(a){a.pct = aT>0 ? Math.round(a.raw/aT*100) : 0;});
  s.apest.sort(function(a,b){return b.pct-a.pct;});

  var wR={ponder:sumW('Po'),ideate:sumW('Id'),assess:sumW('As'),
          rally:sumW('Ra'),facilitate:sumW('Fa'),deliver:sumW('De')},
      wT=0; for(var wk in wR) wT+=wR[wk];
  s.pep=Object.keys(wR).map(function(k){return{id:k,raw:wR[k],pct: wT>0 ? Math.round(wR[k]/wT*100):0};});
  s.pep.sort(function(a,b){return b.pct-a.pct;});
  return s;
}
```

**As explicit arithmetic, reimplementable and unit-testable:**

```
For dimension D in {A,P,E,S,T,d}:
    raw(D) = Σ  score(i)   for all items i where i.apest == D     # 6 terms, each 0..100
    raw(D) ∈ [0, 600]

grandTotal = Σ raw(D) over all 6 APEST dimensions     ∈ [0, 3600]

pct(D) = round( raw(D) / grandTotal * 100 )     if grandTotal > 0, else 0
```

Identically for PEP over tags {Po,Id,As,Ra,Fa,De}, with `wT == aT == grandTotal` (same 36 addends, different grouping).

Properties a developer must know:

- **Weighting: none.** Every item contributes its raw slider value, coefficient 1.
- **Normalisation: none beyond the share-of-total division.** No z-scores, no min-max rescale, no population norms, no per-dimension max.
- **The result is compositional**, not absolute. Scores are *shares summing to ~100%*, so they cannot express "strong across the board" — a participant who slides everything to 100 gets exactly the same profile (16–17% each) as one who slides everything to 10. Only the *relative* shape survives. This is a significant modelling decision and is nowhere stated in the UI.
- **Rounding drift**: each `pct` is rounded independently, so the six values often sum to 99 or 101, not 100. Do not assert `sum == 100` in tests.
- Null-safety: `(g[i.id]||0)` means missing items score 0 rather than throwing.
- Both arrays are returned **sorted descending by pct**. The sort is JS-default-stable on modern engines, so ties fall back to the declaration order (`A,P,E,S,T,d` / `ponder,ideate,assess,rally,facilitate,deliver`). **There is no explicit tie-break.**
- **There is no "top N" selection, no dominant-type label, no archetype, no category assignment.** Every dimension is always displayed, ranked. The "categorisation" is purely the sort order.

Theoretical max for one dimension: 600/3600 = 16.7% if all dimensions equal; a dimension can reach 100% only if all other 30 items are 0.

---

### 6. Thresholds — what actually exists

Contrary to expectation, the profile itself has **zero thresholds**. There are exactly **three** threshold-like rules in the whole engine, all in the *comparison* feature:

**(a) Comparison access gate** (L4072): requires `wbState.contacts.length >= 5`. Below that, the comparison screen renders a "Not enough trusted contacts yet — you've added N of 5" empty state. **CONFIGURABLE** (minimum-respondents-for-aggregation is exactly the privacy control the production system needs).

**(b) Gap significance** (L4184–4190): ±5 percentage points.
```
|diff| >= 5 && diff > 0  → "hidden strength" copy
|diff| >= 5 && diff < 0  → "blind spot" copy
|diff| <  5              → "A modest gap – worth noting but not necessarily significant."
```

**(c) Observer agreement banding** (L4286–4287), on `range = max - min` of individual observer percentages:
```
range <= 6   → "Strong agreement"  (#2E7D32)
range <= 14  → "Some variation"    (#F9A825)
else         → "Divided views"     (#E53935)
```

All three constants (5, ±5, 6/14) are hardcoded. **CONFIGURABLE.**

RAG colouring of PEP bars (L4048–4051) is **by rank position, not by score**:
```js
var ragColors=['#2E7D32','#4CAF50','#F9A825','#FF9800','#E53935','#B71C1C'];
var uniqueScores = [...unique pct values...].sort(desc);
var scoreRank = uniqueScores.indexOf(w.pct);
var color = ragColors[Math.min(scoreRank,5)];
```
Deduplicating before ranking means **tied scores share a colour** — a deliberate tie handling, and the only tie-aware code in the engine. Note APEST bars do *not* use RAG; they use fixed per-dimension colours.

---

### 7. Result labels and explanatory copy

**APEST(d)** — section heading "✨ Your APEST(d) Profile", subtitle "Fivefold ministry gifting plus diaconal service" (L4040).

Colours (L4038): `A:#7B68EE  P:#C25B56  E:#1a7a4c  S:#5B7A5E  T:#4A6FA5  d:#8B7355`
(The comparison screen at L4110 uses *slightly different* hexes for the same dimensions — `A:#7B5EA7 P:#C25B56 E:#2e9e66 S:#5B8C5A T:#4A7FB5 d:#8B7355`. Inconsistency, worth unifying.)

Descriptions (L4039), rendered under each bar:

| Dim | Name | Description |
|---|---|---|
| A | Apostle | Envisioning, pioneering, designing foundations, developing content, raising leaders, building legacy |
| P | Prophet | Challenging the status quo, strong instincts, sensing trends, advocating for justice, communicating hard truths |
| E | Evangelist | Empathy across difference, curiosity, one-to-one persuasion, motivating others, making ideas accessible |
| S | Shepherd | Caring for those struggling, helping groups thrive, welcoming outsiders, correcting where needed, faithful presence |
| T | Teacher | Going deep into source material, breaking down concepts, training to apply learning, communicating through media, evaluating accuracy |
| d | deacon | Supporting others' initiatives, following through on detail, bringing order, improving processes, seeing and doing what's needed |

**PEP** — heading "⚡ Your Professional Energy Profile (PEP)", subtitle "Which types of work energise you most, and which drain you?" (L4046). Labels, personas and descriptions (L4045):

| key | Label | Persona | Description |
|---|---|---|---|
| `ponder` | Ponder | The Philosopher | Stepping back to ask the big "what ifs?" and thinking deeply |
| `ideate` | Ideate | The Creator | Generating options and creating potential solutions |
| `assess` | Assess | The Judge | Applying a reality check to evaluate what will actually work |
| `rally` | Rally | The Catalyst | Gathering the team, building energy and creating buy-in |
| `facilitate` | Facilitate | The Coach | Clearing hurdles, navigating logistics and supporting the team |
| `deliver` | Deliver | The Doer | Rolling up sleeves and pushing the work over the finish line |

Note the key mismatch: item tags are two-letter (`Po`,`Id`,`As`,`Ra`,`Fa`,`De`) but score keys are full words (`ponder`,`ideate`,…). The mapping is implicit in `computeAll` and re-declared as `pepT` at L4053. Two vocabularies for one concept — worth collapsing in the rebuild.

**Validity disclaimer** (L4056) — significant, and should carry into production:
> "**Important:** This is a free, rapid, directional tool, designed to give you a useful starting point for reflection and conversation. It is not backed by extensive psychometric datasets or rigorous validation (yet). Please treat these results as indicative, not definitive."

Followed by outbound recommendations to 5Q (`5qcentral.com`, Alan Hirsch) and Working Genius (`workinggenius.com`, Patrick Lencioni) — L4057–4058. PEP is transparently modelled on Working Genius's six-verb structure.

Each results section also has a collapsible "Show item scores" `<details>` listing every item and its raw 0–100 value, grouped by dimension (L4042–4044 for APEST, L4052–4055 for PEP).

---

### 8. Observer comparison — `generateDummyObserverData()` (L4221–4272)

**This is entirely fabricated. No observer ever supplies data.** Cached on `saState.observerData` so it stays stable within a session (L4095), lost on reload.

```
n = max(5, contacts.length)

apestBias = { A:-3, P:+2, E:-5, S:+7, T:+4, d:-2 }
pepBias   = { ponder:-4, ideate:-2, assess:+5, rally:+3, facilitate:+6, deliver:-3 }
apestSpread = { A:6, P:4, E:3, S:8, T:5, d:7 }
pepSpread   = { ponder:5, ideate:9, assess:4, rally:7, facilitate:3, deliver:6 }

for each dimension D, for each observer o in 0..n-1:
    noise = round( (random() - 0.5) * 2 * spread[D] )      # ∈ [-spread, +spread]
    indiv[D][o] = clamp( selfPct(D) + bias[D] + noise, 1, 40 )

then per observer o (re-normalise so each observer's profile sums to 100):
    aTot = Σ_D indiv[D][o]
    indiv[D][o] = round( indiv[D][o] / aTot * 100 )

then per dimension:
    obs[D] = round( Σ_o indiv[D][o] / n )
```

The biases are what manufacture the "insight": the demo always shows Shepherd (+7), Facilitate (+6) and Assess (+5) rated higher by others, and Evangelist (−5) and Ponder (−4) rated lower. The narrative is pre-baked, not discovered.

The `clamp(...,1,40)` upper bound rarely binds (typical pct values are 10–25) but would silently distort any strongly-dominant profile. Note this observer path is the **only** place a second normalisation step exists — and it is per-observer, applied *before* averaging, which is the statistically correct order and worth preserving in the real implementation.

`renderDistribution()` (L4275–…) draws a dot strip: each observer is a dot, plus a range band from min to max, scaled to `max(selfPct, max(individual)) + 4`. Reports lo/hi/avg/range and the agreement band from §6(c).

**Biggest Gaps** (L4164–4195): builds a combined list of all 12 dimensions (6 APEST + 6 PEP) with `diff = others - self`, sorts by `Math.abs(diff)` descending, takes **top 5**. Mixes the two frameworks in one ranked list. Badge reads "Others rate higher" (diff>0) or "You rate higher" (diff<0), always with `(+|diff|)`.

Four fixed reflection prompts follow (L4201–4204): Hidden strengths / Blind spots / Confirmed strengths / The surprise.

---

### 9. Baseline rating scales (pre and post)

Rendered by `renderBaselineButtons()` (L2978–2988) — **ten `<button>` elements, values 1–10**, not a slider. Anchors "Strongly disagree" (left) / "Strongly agree" (right). Identical question set is asked twice.

| slot | Pre id | Post id | Statement |
|---|---|---|---|
| bible | `bl-bible` | `pl-bible` | I have a detailed understanding of what the Bible teaches about 'work' and 'calling' |
| gifts | `bl-gifts` | `pl-gifts` | I have a detailed understanding of what my God-given talents/gifts and limitations are |
| call | `bl-call` | `pl-call` | I have a strong sense of what God's specific 'call' and purpose is for my life |
| plan | `bl-plan` | `pl-plan` | I have a clear, practical plan for how to pursue God's purpose for my life, in terms of 'work' / 'calling' |

- Screens: `screen-baseline` (L1911, pre) and `screen-postbaseline` (L2676, post).
- Answers accumulate in a module-global `var _baselineAnswers = {}` (L2989) keyed by the *element id*, so pre and post coexist in one flat object.
- Gate: all four must be answered before continue enables — `ids.every(id => _baselineAnswers[id])` (L3001). Button goes `opacity 0.4 / pointerEvents none` → `1 / auto`, label changes from "Answer all four to continue →" to "Continue →". **Note the truthiness check: a score of 0 would fail, but the scale starts at 1 so it cannot occur.**
- `submitBaseline()` (L3009) writes `wbState.baseline = {bible,gifts,call,plan}` then navigates to `screen-mentor`.
- `submitPostBaseline()` (L3298) writes `wbState.postbaseline = {...}`, calls `buildSummary()`, shows `screen-complete`.
- `renderBaselineButtons` guards with `if (container.children.length > 0) return;` — idempotent, but this means **re-rendering never refreshes the selected state**; the demo path has to reapply selections manually (`_demoApplyBaseline`, L6767–6768).
- **No scoring whatsoever.** The four values are stored raw. Any pre/post delta is computed at display time in the summary, not here.
- Demo seed values (L6809–6811): `{bible:6, gifts:5, call:4, plan:3}`.

**CONFIGURABLE**: question wording, count (hardcoded to exactly four, with the literal string "Answer all four"), scale bounds (1–10), anchor labels, and the fact that the post set is an exact repeat.

---

### 10. Session state shape

```js
saState = {
  name: '',                    // copied from wbState.userName
  buckets: {1:[],2:[],3:[],4:[],5:[]},   // bucket id -> [itemId]  (1 = strongest!)
  sortDeck: [],                // remaining item objects, shuffled
  sortHistory: [],             // [{id, bucket}] for undo
  rankedIds: [],               // written by submitSort, never read
  giftScores: {},              // itemId -> 0..100
  completed: false,            // set true at end of buildResults
  comparisonViewed: false,     // set true at end of buildComparison
  observerData: null           // cached fabricated data
}
```

Lifecycle: `openAssessment()` (L3873) short-circuits to results if `saState.completed`; otherwise `startFreshAssessment()` (L3882) resets everything. `retakeAssessment()` (L3893) confirms via `confirm()` then resets — **destroying prior results with no history**. `returnFromAssessment()` (L3899) flips the workbook's `assessment-status` element to done and re-enters the gifts pillar.

There is a compatibility shim at L3922 creating a stub `appState` if undefined, and `APEST_AREAS` is referenced at L3504/L3682 for mentor/summary output — a **separate, older** data structure from `giftItems`, guarded by `typeof !== 'undefined'`. Two generations of assessment code coexist.

---

### 11. Corrections to the prior prose summary

1. **"Receives calculated APEST and Professional Energy Profile results"** understates it — APEST here is **APEST(d), six dimensions**, including a lowercase `d` deacon dimension. Not the standard fivefold model.
2. **"Weights", "Formulas", "Normalisation", "Thresholds", "Category classification"** are listed as things the configurator must define, implying the prototype has them. **It has none of them.** Scoring is an unweighted sum → percentage of grand total → rank. There is no category assignment at all. This is good news for migration (the maths is trivial to port and test) and bad news for fidelity expectations (there is no hidden sophistication to recover).
3. **"Sorts every item into five buckets"** — true, but the stored bucket integers are **inverted** (1 = "Real strength", 5 = "Definitely not me"). Highest migration-risk detail in this document.
4. **"Fine-tunes each item using a 0–100 slider"** — the summary omits that buckets *seed* the slider at `{85,65,45,25,10}`, and that untouched sliders keep those seeds. The sort is therefore sufficient on its own to produce a complete profile.
5. The summary treats the assessment as self-contained; in fact **the comparison gate (≥5 contacts), the ±5pp gap rule and the 6/14 agreement bands are the only real thresholds in the product**, and they belong to the observer feature rather than the profile.
6. Not mentioned at all: the **compositional** nature of the score (shares sum to 100, so absolute strength is discarded), the **unbalanced APEST×PEP cross-tab**, the unseeded shuffle, and the vestigial `rankedIds`.
