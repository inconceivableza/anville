# Re-theming prompts — sample prompts per phase

> ✨ Drafted with AI assistance. These are prompts to hand to an AI coding assistant (or a developer) to implement each phase of the re-theming plan. Each prompt is self-contained: it names the files to touch, the design tokens to use, and the acceptance criteria. Review each before running it, and commit after each phase.

The plan these prompts implement is the **Option A** approach agreed with the team: keep the multi-page Django architecture, restyle each template with the new "Whatever You Do" design system, and port the interactions that make sense per page. The engine-derived behaviour (statuses, locks, gates, autosave) stays server-side and authoritative.

The reference design is `docs/plans/retheme_index.html` (946 lines, 84 KB). It is a single-page marketing + onboarding + hub concept with a warm editorial "care brand" aesthetic: cream/paper surfaces, near-black brown for dark panels, one lime-green accent, serif + script + mono type, full-bleed photography, and rich interactions.

---

## Phase 0 — Abstract the design tokens

**Goal:** Close the abstraction gap found in the audit. Colours are already fully abstracted in `:root`; typography, spacing, and radius are not. Introduce scales so the rest of the re-theme can use tokens instead of hardcoded values.

**Files to touch:**
- `frontend/src/styles.css`

**Prompt:**

> In `frontend/src/styles.css`, the `:root` block already defines all colours as custom properties, plus `--radius: 16px` and two fonts. But the rules below hardcode dozens of font sizes, line heights, letter spacings, border radii, spacing values, and box-shadow dimensions.
>
> Add three scales to `:root`:
>
> ```css
> /* Type scale */
> --text-xs: 0.8125rem;   /* 13px */
> --text-sm: 0.875rem;    /* 14px */
> --text-base: 1rem;      /* 16px */
> --text-lg: 1.25rem;     /* 20px */
> --text-xl: 1.5rem;      /* 24px */
> --text-2xl: 2rem;       /* 32px */
> --text-3xl: 2.75rem;    /* 44px */
> --text-4xl: 3.5rem;     /* 56px */
> --text-display: clamp(2.5rem, 5vw, 4rem);
>
> /* Spacing scale */
> --space-1: 0.25rem;  --space-2: 0.5rem;  --space-3: 0.75rem;
> --space-4: 1rem;     --space-5: 1.5rem;  --space-6: 2rem;
> --space-7: 3rem;     --space-8: 4rem;    --space-9: 6rem;
>
> /* Radius scale */
> --radius-sm: 8px;  --radius-md: 12px;  --radius-lg: 16px;
> --radius-xl: 22px; --radius-pill: 999px;
> ```
>
> Then sweep the existing rules to use these tokens instead of raw values. Do not change any visual output — this is a pure refactor. Replace:
> - Hardcoded `font-size` values with the nearest `--text-*` token.
> - Hardcoded `line-height` and `letter-spacing` values with named tokens only where a clear scale emerges; otherwise leave them, but note them.
> - Hardcoded `border-radius` values with `--radius-*` tokens.
> - Hardcoded `padding`/`margin`/`gap` values with `--space-*` tokens.
> - Hardcoded `box-shadow` dimensions with a `--shadow-*` token set.
>
> **Acceptance criteria:**
> - No raw colour values anywhere outside `:root` (already true — verify).
> - No hardcoded `font-size`, `border-radius`, or spacing values in the rules; all use tokens.
> - Visual output is unchanged (compare before/after screenshots of the hub, a section page, and the homepage).
> - `npm run build` succeeds.

---

## Phase 1 — Swap the palette and fonts

**Goal:** Land the new visual identity. Replace the cool green/cream palette with the warm cream/brown/lime palette, and add the new fonts.

**Files to touch:**
- `frontend/package.json`
- `frontend/src/styles.css`

**Prompt:**

> Replace the `:root` colour block in `frontend/src/styles.css` with the new "Whatever You Do" palette, mapping the new names onto the existing semantic variables so existing rules keep working:
>
> | New HTML | Anville semantic | Notes |
> |----------|------------------|-------|
> | `--cream:#f2f0e3` | `--cream` | warm cream (was cool `#f4f7f5`) |
> | `--paper:#f8f7ef` | `--white` | card surface |
> | `--brown:#1d1413` | `--deep` / `--footer` | dark panels (was dark green) |
> | `--ink:#1c1714` | `--ink` | near-black text |
> | `--muted:#6c625a` | `--ink-muted` | |
> | `--green:#a6cf72` | `--gold` | the lime accent (was deep green) |
> | `--green-deep:#2f5a2b` | `--gold-dark` | |
> | `--green-ink:#1d2a10` | `--gold-pale` text | |
>
> Keep the existing semantic variable names (`--gold`, `--deep`, `--footer`, `--ink`, `--cream`, `--white`, etc.) so the rules below keep working — only their values change. Add the new names as aliases where the new HTML uses them.
>
> **Fonts:** the new HTML uses **Newsreader** (already bundled), plus **Inter** (replaces Instrument Sans), **Pinyon Script** (the script accent), and **IBM Plex Mono** (the mono labels). Add `@fontsource-variable/inter`, `@fontsource/pinyon-script`, `@fontsource/ibm-plex-mono` to `frontend/package.json` and import them in `frontend/src/styles.css`. Update `--font-heading` (Newsreader), `--font-body` (Inter), and add `--font-script` (Pinyon Script) and `--font-mono` (IBM Plex Mono).
>
> **Acceptance criteria:**
> - The palette swaps everywhere without breaking existing rules (all rules still use variables).
> - The new fonts load and render (verify in the browser).
> - `npm run build` succeeds.
> - The hub, a section page, and the homepage all show the new palette.

---

## Phase 2 — Replace the homepage (`home.html`)

**Goal:** Restyle the public marketing homepage with the new design language. This is the largest and most self-contained piece.

**Files to touch:**
- `engine/templates/engine/home.html`
- `frontend/src/styles.css` (the `hp-*` and `hiw-*` rules)
- `frontend/src/main.js` (homepage interactions)

**Prompt:**

> Restyle `engine/templates/engine/home.html` to match the "Whatever You Do" landing view in the reference HTML. Keep the multi-page Django structure — this is a template + CSS rewrite, not an SPA.
>
> Map the reference sections onto the existing homepage:
>
> | Reference section | Existing | Action |
> |-------------------|----------|--------|
> | Hero (video, wordmark, CTA, logo row) | `hp-hero` | Restyle; keep `{% include "access/demo_notice.html" %}` |
> | Mission (scroll-reveal statement) | `hp-about` | Restyle; add word-by-word reveal |
> | How it works (sticky scrollytelling, 3 steps) | `hiw` | Replace the 4-step `hiw-steps` with the 3-step scrollytelling version |
> | Assessment tabs (auto-advancing) | — | New section; content is static marketing copy |
> | Impact (count-up stats + quote + churches) | `hp-impact` | Restyle; add count-up |
> | Connect (writing, newsletter, contact, give) | — | New section |
> | Meet (ring carousel) | — | New section |
> | Footer | `site-footer` | Restyle |
>
> Use the new palette tokens from Phase 1. Use the type/spacing/radius tokens from Phase 0. Use `clamp()` for responsive type, as the reference does.
>
> **Acceptance criteria:**
> - The homepage shows the new editorial design language.
> - The hero video plays (unless `prefers-reduced-motion`), with the demo notice still present.
> - The "How it works" section is the 3-step scrollytelling version.
> - The assessment tabs, impact stats, connect, and meet sections render.
> - All interactions respect `prefers-reduced-motion`.
> - `npm run build` succeeds and the page renders without console errors.

---

## Phase 3 — Replace the hub (`hub.html`)

**Goal:** Restyle the participant's workbook hub. This is where the engine's derived data plugs in — do not hardcode the section list, statuses, or counts.

**Files to touch:**
- `engine/templates/engine/hub.html`
- `engine/templates/engine/hub_section.html`
- `engine/templates/engine/participant_header.html`
- `frontend/src/styles.css`
- `frontend/src/main.js`

**Prompt:**

> Restyle `engine/templates/engine/hub.html` to match the "Whatever You Do" hub view in the reference HTML. Keep the engine-derived data — do not hardcode the section list, statuses, or counts.
>
> Map the reference hub elements onto the engine sources:
>
> | Reference element | Engine source | Action |
> |-------------------|---------------|--------|
> | `hub-head` title + "0 of 5 sections complete" | `hub.answered` / `hub.total` | Bind to real progress |
> | `next` panel (photo, title, CTA) | `hub.next_step` | Restyle the existing `next-step` banner |
> | `slist` / `srow` (numbered sections, locked) | `hub.outline` | Restyle `hub_section.html`; keep locks |
> | `side` → "Five trusted voices" card | invitations / `hub.consent` | Restyle; keep the invite form + counts |
> | `side` → "Walk with a mentor" card | `coach` / `coach_page` | Restyle the coach card |
> | `side` → "Where you started" baseline | results / baseline scores | New card; bind to real baseline data |
>
> The hub's `nav` (My workbook / Resources / Saved tag) replaces the current `participant_header.html` sidebar. Keep the `ANVILLE_SIDEBAR` setting — the new hub nav is the sidebar's successor, so wire it through the same `participant_nav` template tag.
>
> **Acceptance criteria:**
> - The hub shows the new design language.
> - The section list, statuses, locks, and progress are all engine-derived (no hardcoded values).
> - The trusted-voices card shows real invite counts and the invite form works.
> - The coach card reflects the real coach state.
> - The baseline card shows real baseline data.
> - `npm run build` succeeds and the hub renders without console errors.

---

## Phase 4 — Add the onboarding wizard

**Goal:** Add the 4-step pre-hub wizard as a real Django flow, not a JS state machine.

**Files to touch:**
- `engine/views.py` (new view)
- `config/urls.py` (new route; routes are configured centrally)
- `access/models.py` (new account fields: `reason`, `path`, `remind`, and onboarding completion)
- `access/forms.py` and `access/migrations/` (mark new accounts for onboarding and preserve existing accounts)
- `engine/templates/engine/onboarding.html` (new template)
- `frontend/src/styles.css` (the `.ob-*`, `.scale`, `.sl`, `.opts`, `.field` rules)
- `frontend/src/main.js` (slider value enhancement only; Django owns wizard state)

**Prompt:**

> Add a 4-step onboarding wizard as a real Django flow, matching the "Whatever You Do" onboarding view in the reference HTML. Keep the existing signup and consent sequence first; show the wizard to new accounts after consent. The wizard is a new template + view, not a JS state machine.
>
> The 4 steps:
> 1. **Reason** — use the authored `single_select` block with ID `reason`; persist its validated answer to the account and the pathway `Response`.
> 2. **Baseline** — show all five authored `agreement_scale` blocks in the reason's section as 10-point sliders, and persist them as pathway `Response` answers. Do not duplicate or hardcode the statements. The slider UI (`.scale`/`.sl`/`.slider`) is a new CSS component.
> 3. **Path** — online vs paper → persist the choice to the account.
> 4. **Save** — show the name/email already captured during signup and save the reminder preference to the account. Make clear that reminder emails are not sent yet.
>
> The wizard's `chrome()` (step label, progress bar, scripture quote) is presentational and ports directly.
>
> **Acceptance criteria:**
> - New participants reach the wizard after signup and consent; existing accounts are not sent through it.
> - The wizard renders as a 4-step flow with a progress bar and scripture quote.
> - Reason and all five authored baseline scores are saved using existing pathway validation and `Response` storage; path and reminder preference are saved to the account.
> - Signup name and email are displayed without asking the participant to enter them twice.
> - The baseline sliders use the `agreement_scale` block type.
> - The wizard respects `prefers-reduced-motion`.
> - `npm run build` succeeds and the wizard renders without console errors.

---

## Phase 5 — Port the interactions into `main.js`

**Goal:** Port the presentational interactions from the reference HTML into `main.js`, each guarded by `prefers-reduced-motion`.

**Files to touch:**
- `frontend/src/main.js`

**Prompt:**

> Port the presentational interactions from the reference HTML into `frontend/src/main.js`. Each must be guarded by `prefers-reduced-motion` (the reference already does this). Keep the existing htmx autosave, contact-row, coach-checklist, and copy-link logic untouched.
>
> Port these:
> - **Wipe transition** — only for the landing→onboarding CTA; drop the SPA view-switching.
> - **Ring carousel** (`#ringStage`) — the "Meet" section.
> - **Word-by-word scroll reveal** (`#reveal`, `[data-reveal]`).
> - **Auto-advancing assessment tabs** (`#aTabs`).
> - **Sticky scrollytelling** (`#howSteps`).
> - **Count-up stats** (`.stat`).
> - **Magnetic buttons** (`.pill`).
> - **Logo carousel** (`#logoRow`).
>
> **Acceptance criteria:**
> - Each interaction works on its page.
> - Each respects `prefers-reduced-motion`.
> - Existing htmx autosave, contact-row, coach-checklist, and copy-link logic still work.
> - `npm run build` succeeds and the pages render without console errors.

---

## Phase 6 — Verify no schema changes needed

**Goal:** Confirm the new HTML introduces no new data model — its components map to existing block types.

**Files to touch:**
- None (verification only)

**Prompt:**

> Verify that the "Whatever You Do" reference HTML introduces no new data model. Its components map to existing block types:
>
> | Reference component | Existing block type |
> |---------------------|--------------------|
> | `.scale` slider | `agreement_scale` |
> | `.opts` / `.opt` buttons | `single_select` |
> | `.field` inputs | `long_text` / contact fields |
> | `.check` checkbox | `coach_checklist` |
> | `.srow` section list | `section_link` |
>
> Confirm no new block types or schema changes are required. The onboarding baseline sliders reuse `agreement_scale`.
>
> **Acceptance criteria:**
> - No new block types are needed.
> - No schema changes are required.
> - The onboarding baseline sliders reuse `agreement_scale`.

---

## What we deliberately don't port

- **The SPA view-switching** (`show()`, `hidden` toggling) — replaced by Django routing.
- **The fake/mock data** (hardcoded sections, fake stats, placeholder logos, sample invites) — replaced by engine-derived data.
- **The marketing-only copy** (newsletter, donation, "From our writing") — these are homepage content, not participant features.

---

## Suggested sequencing

1. **Phase 0** (tokens) — small, unblocks everything.
2. **Phase 1** (palette/fonts) — the visual identity lands.
3. **Phase 2** (homepage) — largest, self-contained, highest visual payoff.
4. **Phase 3** (hub) — the participant's daily surface.
5. **Phase 4** (onboarding) — new flow, needs a model field or two.
6. **Phase 5** (interactions) — sprinkle in as each surface lands.
7. **Phase 6** — verify no schema changes needed (likely none).
