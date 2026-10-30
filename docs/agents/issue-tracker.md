# Issue Tracker: Local Markdown

> ✨ Drafted with AI assistance.

Issues and specs for this repo live as markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`, never a single combined tickets file. An oversized ticket splits into lettered siblings (13 → 13a, 13b, 13c)
- A feature may sort its tickets into sprint folders under `issues/` (`sprint-1`, `sprint-2b`, `sprint-3plus-or-unassigned`). A ticket keeps its number when it moves, and numbers stay unique across the folders
- In a sprint being worked, a ticket's file name takes a prefix for its chain and its order in it: `A1-36-<slug>.md`. Tickets in different chains can be worked in parallel; within a chain, each is blocked by one before it. Tickets sharing a place take a letter after it (`A4A-`, `A4B-`) and can be done in either order. A ticket may also be blocked by one in another chain: its `**Blocked by:**` line is the record, and the prefix only a guide. The title keeps the plain number
- Work a sprint by pointing at its folder alone: other folders hold parked tickets that still read `ready-for-agent`
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- No ✨ in ticket or spec files

## Ticket shape

Use this in place of the `/to-tickets` template:

```

# <NN>: <Ticket title>

**What to build:** the end-to-end behaviour, from the user's side

**Blocked by:** <NN> (<title>), with its prefix if it has one, or "None (can start immediately)"

**Status:** ready-for-agent

**Sprint:** <n> (ends <date>)

**Spec:** <exact spec heading>; <exact spec heading>

- [ ] Acceptance criterion
```

- `**Spec:**` names the spec sections the ticket needs, by exact heading text, separated by semicolons. Where a heading repeats, name its parent too: `Implementation Decisions › Coach`
- Criteria are checkable behaviour, about 5 or fewer. The reasons behind them go in the spec or an ADR. No file paths or ids, except a prototype reference. No lists of test cases
- `**Carried from NN**`, under the criteria, holds only what no criterion already says (`- [ ]` for work, `- ` for context)

## Working a ticket

- **Old shape:** a ticket with `**Parent:**` in place of `**Spec:**` is in the old shape. Before starting, offer to trim it to the shape above, moving any rationale to the spec
- **Reading:** read the sections its `**Spec:**` line names (grep their headings), not the whole spec. Grep prototypes in `Prototypes for reference/`; never read one whole
- **Tests:** before writing any, agree the ticket's seams and a capped list of behaviours with the developer (spec, Testing Decisions)
- **While working:** `Status: claimed`. Step records go in commit messages; decisions go in an ADR, `CONTEXT.md` or the spec. A `## Comments` heading at the bottom holds only a line per criterion left partly met at a commit
- **Resolving:** set `**Status:** resolved` exactly (a ticket is unblocked only when every blocker reads `resolved`). Carry each open note or criterion into the ticket that will act on it, under `**Carried from NN**`; a note with no owning ticket goes beside the relevant decision in the spec. With open criteria, add a `**Handed over:**` line under the status and suffix each open criterion "(… carried to NN)". `## Answer` is only an index of where the notes went

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Wayfinding operations

Used by `/wayfinder` only. The map is a file with one child file per ticket.

- **Map**: `.scratch/<effort>/map.md` (the Notes / Decisions-so-far / Fog body).
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.scratch/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: for a wayfinding question ticket only, append the answer under an `## Answer` heading, set `Status: resolved`, then append a context pointer to the map's Decisions-so-far in `map.md`. Implementation tickets resolve as above.
