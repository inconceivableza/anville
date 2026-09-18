# Prototype Reference — read this first

> ✨ This document set was produced with AI assistance by extracting behaviour directly from the prototype source. Line references were verified against the file.

Reference for `Prototype for reference/vibe-coded-prototype.html` — 7,881 lines, 477 KB, one self-contained file.

**Purpose of this document set:** read these instead of the HTML. Orientation costs ~4k tokens here versus ~120k for the file. Work on one area costs one appendix.

| Need | Read |
|---|---|
| Orientation, traps, what's real | This file |
| The 36-item instrument, scoring maths, results copy, baseline scales | [01-assessment.md](01-assessment.md) |
| Per-section state shapes, exact gate predicates, routing, enumerations | [02-sections.md](02-sections.md) |
| The 31 block types, pathway outline, derived/recap blocks, mentor briefs | [03-blocks.md](03-blocks.md) |
| Storage, save format, observer/mentor flows, demo mode, the letter | [04-persistence.md](04-persistence.md) |

---

## What it is

A single-file, client-side prototype of **Whatever You Do** — a Christian vocational-calling and discernment workbook. It is the first product intended to be built *with* Anville; it is not Anville itself, and it is not the production architecture.

There is **no server anywhere in the file**. No `fetch`, no `XMLHttpRequest`, no form `action`. Everything is in-memory JavaScript plus `localStorage`.

Two unrelated surfaces share one stylesheet:

| Surface | Lines | In scope? |
|---|---|---|
| Marketing brochure — homepage, churches page, blog, team, donate | L1247–1766 | **No.** Treat as a separate CMS or static-site concern. |
| Participant app — 34 `.screen` divs, one visible at a time | L1767–2760 | **Yes.** This is the product. |
| Demo/tester tooling | L6445–6526 | No. Labelled "not part of the product" in-source. |

File layout: CSS L13–1099 · JS L1102–1245 · HTML L1246–2808 · **JS L2809–6443 (the bulk)** · HTML L6444–6526 · JS L6527–7879.

## What it is trying to be

The participant journey: **onboarding** (account → 4 baseline ratings → mentor → ≥5 trusted contacts → online/offline choice) → **hub** → **five sections** → **closing** (video → the same 4 ratings repeated → summary).

| Section | Subject | Core interaction |
|---|---|---|
| 1 | How you have been designed | 36-item card sort + slider fine-tune → APEST(d) and PEP profiles, then self-vs-observer comparison |
| 2 | The shape of your life | Timeline: chapters, typed markers dropped into them, recurring threads |
| 3 | Putting your calling into words | Sentence builder → idea generation through 4 lenses → 2–3 developed "role pictures" |
| 4 | Growth plan | Activities across 5 categories assigned to a quarter grid |
| 5 | Letter to your future self | Composed letter, sealed, nominally delivered on a future date |

**The distinctive claim** is the join: a participant's self-assessment and several observers' assessments, scored on the same constructs and presented side by side, with observer identities withheld. Everything else is a workbook; this is the part that makes it a product.

That is also the one part with nothing behind it. See trap 4.

---

## Traps

These are load-bearing. Each one costs real money if discovered late.

**1. Bucket IDs are inverted.** `BUCKETS` (L3975) declares `id:1 = 'Real strength'` and `id:5 = 'Definitely not me'`. The array is ordered weakest-first so it *renders* left-to-right as a normal scale, but the stored integer runs the other way. A naive `1..5 = low..high` assumption inverts every participant's profile. *Verified against source.*

**2. Screen IDs and state keys lie.** Sections were renumbered mid-prototype and nothing was migrated.
- `screen-section3` is **Section 4** (Growth Plan) and sits between `section2b` and `section2c` in source order.
- `wbState.section2Done` means **Section 3** complete; `wbState.section3Done` means **Section 4**.
- `wbState.pillars` holds only `gifts`, `timeline`, `letter`. Sections 3 and 4 use ad-hoc booleans outside it — three different completion mechanisms in one product.

**3. Almost every gate is cosmetic.** `checkSection1Complete()` and `checkSection5()` only toggle `style.display` on `section{N}-locked` divs. They hide UI; they do not prevent navigation. The **only** hard guard in all 7,881 lines is in `showScreen()` (L2840–2848), covering screens 2b/2c. **Section 4 has no gate at all** — the "Complete workbook ✓" button (L6238) carries no `disabled`, no readiness function, and `gp-gate` appears zero times in the file. You can finish the workbook with no activities. *Verified against source.*

**4. The observer comparison is fabricated at render time.** `generateDummyObserverData()` (L4221) invents `max(5, contacts.length)` observers from hardcoded bias tables (`S:+7, T:+4, E:−5`) plus unseeded `Math.random()` noise. Consequences:
- The "feedback from people who know you" **changes on every page load** and after every restore.
- Observers are fabricated even if the participant skipped adding contacts.
- The biases are editorially tuned to manufacture the insight — the demo always shows Shepherd and Facilitate rated higher by others. The narrative is pre-baked, not discovered.
- It lives in `saState`, so it **is** serialised into `localStorage` and export files, **indistinguishable from real data**.

The seven qualitative observer questions are collected and sent to `console.log` (L6392). Nothing is persisted, transmitted or aggregated. Invite links are the literal string `?observer=true` — no token, no identity, no binding to a participant, no expiry.

**5. Observer and participant share one global.** `startRespondentForm()` (L6365) overwrites `saState` — the participant's own assessment — with a fresh deck. An observer opening the link in a browser holding participant progress **destroys that progress**, and the 600 ms autosave writes the loss to storage.

**6. The hidden legacy fields are not duplication — they are a different abandoned taxonomy.** Three `sync*ToFields()` functions write derived strings into hidden inputs named `opps-*`, `comm-*`, `fruit-*`, `disc-*`. Of 16 timeline fields, **8 are unconditionally blanked on every call**. `syncCallingToFields()` mirrors an unbounded `ideas[]` array into three fixed slots, so **possibilities 4+ are silently dropped** from summaries and mentor emails — and overloads `s2-expr3-church` to carry the starred shortlist, a field name unrelated to its contents. The summary builder and mentor-email builder read *these DOM fields*, not the state objects. Do not port any of it.

**7. Scores are compositional, not absolute.** Each dimension is `round(raw / grandTotal × 100)` — shares summing to ~100. "Strong across the board" is mathematically inexpressible: sliding everything to 100 produces the identical profile to sliding everything to 10. Only relative shape survives. This is ipsative data and needs ipsative treatment. Nowhere stated in the UI.

**8. Hardcoded absolute dates already expiring.** `roadmapQuarters` (L6042) is `Q3 2026 … Q4 2027`. Q3 2026 ends this month. Periods must become relative to enrolment or author-managed.

**9. Sanitisation is wrong in three ways.** `scrub()` (L7433) strips `<` and `>` from strings, and runs **only on file import — not on the `localStorage` read path**. It does not stop prototype pollution (`scrub()` and `assign()` both assign attacker-controlled keys with plain `[k] =`), does not neutralise `javascript:` URLs or entity-encoded brackets, and **corrupts legitimate input** — "I was < 50% sure" loses characters on every round-trip. Escape on output; never mutate on input.

**10. Demo mode defaults ON** (`var demoMode = true`, L6529) and demo state carries **no provenance flag** in the snapshot. Seeded accounts, fabricated scores and demo timeline markers land in save files looking exactly like participant work. Preview/test data must be a server-side distinction, not a client global.

**11. There is no versioning.** The snapshot writes `"v": 1` (L7477) and **never reads it**. `restore()` performs no version check, no migration, no shape validation. Nothing here is reusable.

**12. The delivery date does nothing.** `lt-date` is rendered into two strings and swept into the fields bag. No timer, no scheduler, no queue. "It will find you on the date you chose" (L7401) is the most confident untruth in the prototype.

---

## Real vs simulated

| Works for real | Simulated, absent, or a lie |
|---|---|
| The 36-item sort and slider capture | All observer data (fabricated, unseeded) |
| APEST(d) + PEP scoring and ranking | All observer qualitative answers (`console.log`) |
| Timeline, possibilities, growth plan, letter composition as UI | Observer/mentor invitations (no tokens) |
| `localStorage` autosave, JSON export/import | All email (four surfaces, all previews) |
| Print/copy/clipboard actions | Letter delivery and scheduling |
| One hard route guard (screens 2b/2c) | Every `section{N}-locked` padlock |
| Derived recap blocks reading earlier answers | All 6 videos, all 4 resource cards |
| | PDF download, offline workbook, reminders |
| | Newsletter, team and advisory profiles |
| | Section 4 completion enforcement |

## What is genuinely worth migrating

Content, not code. All of it is extracted verbatim in the appendices:

- **The 36-item bank** with APEST and PEP tags — [01](01-assessment.md#2-the-item-bank-all-36--l39373973)
- **Result copy** — 6 APEST descriptions, 6 PEP labels/personas/descriptions, and the validity disclaimer, which should carry into production
- **4 baseline rating statements** (1–10, asked twice)
- **5 marker types** with prompts, questions and examples; **5 starter chapters**
- **4 possibility lenses** with 25 prompts
- **4 role-picture fields**; **5 growth categories** with 15 suggestions and the `categoryTiming` scheduling heuristic
- **4 mentor briefs** (purpose / duration / ask / watch / avoid) — note there is **no Session 5 brief**
- **7 observer questions**; account-setup reasons; observer relationships
- **Every gate's "what's missing" copy**, which is conditional on *which clause failed* — predicates need per-clause messages, not one message per gate

## What must be designed, not migrated

The prior prose summary framed completion rules as something to port. They largely do not exist.

- Routing, gates and completion semantics — there is one real guard to learn from
- Observer invitation, consent, identity, response persistence, anonymity thresholds
- Versioning, publication, immutability — `v:1` is written and never read
- Any notion of an author, a configurator, or a second pathway
- Real delivery for four email surfaces, plus a durable long-horizon scheduler for the letter

One detail deserves attention because it is the whole configurator problem in miniature: `renderExpressions()` (L4429) already contains **orphan-reference remapping** — when a lens no longer exists, responses filed under it are silently reassigned to `lenses[0]`. Filing a participant's answer under the wrong category rather than losing it. Once lenses are author-configurable this stops being a one-off and becomes the general case. Version pinning plus an explicit orphan policy needs designing up front.

## Integration surface for real observer data

`generateDummyObserverData()` returns the shape the comparison UI consumes. Real aggregation need only satisfy it:

```jsonc
{
  "apest":           { "A": 18, "P": 14, "E": 9, "S": 31, "T": 20, "d": 8 },
  "pep":             { "ponder": 12, "ideate": 14, … },
  "apestIndividual": { "A": [16,19,21,15,18], … },   // one normalised % per observer
  "pepIndividual":   { "ponder": [10,13,…], … },
  "n": 5
}
```

Supply per-observer normalised percentages plus `n` and both the averages and the distribution strip work unchanged. Note the prototype normalises **per observer before averaging**, which is the statistically correct order and worth preserving.

What must be added around it: minimum-`n` suppression before any distribution renders, consent capture, and participant-controlled sharing. Five dots from five participant-named contacts is trivially de-anonymising — one outlier dot identifies the dissenter.
