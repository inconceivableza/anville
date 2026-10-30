# Building Anville with AI

> ✨ Drafted with AI assistance, for the handover (30 Oct 2026).

Most of Anville was built with Claude Code driving [Matt Pocock's skills](https://github.com/mattpocock/skills). This page says which flows were used, and the tools around them, so the next developer can carry on the same way or drop what does not suit them.

## Installing the skills

The skills are not in the repo. Install them from the repo's root:

```
npx skills add mattpocock/skills
```

and choose Claude Code when asked. Install them into this project, not globally: they belong in the repo's own `.claude/`, not the machine's `~/.claude/`. This command was written down at the handover but not tried again since the first install; check what it asks. They land in `.agents/skills/`, linked from `.claude/skills/`, both ignored by git. `skills-lock.json` lists the skills this project used, with the source path and hash of each. Then run `/setup-matt-pocock-skills` once if the skills ask for it; this repo's answers are already in `docs/agents/` (a local tracker in `.scratch/`).

When unsure which skill fits, type `/ask-matt <what you want>`: it maps the request onto the flows below.

## Token cost

On a capped plan, the flows differ a lot in what they use:

- **Heavy: `/implement-spec` with parallel implementers.** Each subagent starts cold, reads the spec, tickets and code again, and runs its own tests; four at once used a day's allowance in hours, and runs were cut off by the usage limit (sprints 2b and 3c). `method.md`'s "Saving usage" and "Tried, and what we kept" say what helped: at most four implementers, a smaller model for light tickets, several short runs rather than one long one.
- **Heavy: `/code-review`.** Two reviewers read the whole diff; over a whole build that is a lot. Run it on a ticket's diff, or at a build's end only if usage allows.
- **Moderate: `/grill-with-docs` → `/to-spec` → `/to-tickets`.** Long conversations, but one session.
- **Light: `/implement` per ticket, `/tdd`, `/ask-matt`.** One context, fresh per ticket.
- Anything that reads screenshots costs about 1,000–1,600 tokens a picture (`bin/screenshot` says so).

## Where things were left (30 Oct 2026)

- **Code review stopped with the checklist.** Sprint 3c was never reviewed as a whole: it ran in three runs (26–28 Oct), each reviewed at its end, runs 1 and 2 on both axes, run 3 (tickets 100 and 74) on the Spec axis alone. The hand-check fixes after each review were not reviewed again. Most of what was committed after the checklist method began (below) has not been through `/code-review`; the one exception is ticket 104 (the sealed letter), reviewed on 30 Oct before commit `be9fa6d`. A review of `main` since sprint 3b's merge, Standards axis especially, is worth doing early.
- **Checklist, not tickets, at the end.** From about 27 Oct the content owner's feedback was worked straight from their checklist (`Whatever You Do feedback - checklist.md`, kept beside the repo), item by item, rather than written up as tickets in `.scratch/`. That was a temporary measure for the last days; go back to tickets (`/to-tickets`, `docs/agents/issue-tracker.md`) for new work.

## The flows used

| Flow | Skills | Used for | Leaves |
|---|---|---|---|
| Idea → spec → tickets | `/grill-with-docs` (runs `/grilling` and `/domain-modeling`), then `/to-spec`, then `/to-tickets` | Every milestone and sprint | `GLOSSARY.md`, `docs/adr/`, `.scratch/<feature>/spec.md` and `issues/` |
| One ticket at a time, test first | `/implement`, which drives `/tdd` and ends in `/code-review` | Small or sequential work; sprint 3b | Commits, `docs/manual-checks.md` entries |
| A whole sprint in parallel | `/implement-spec`, following `.claude/builds/method.md` | Sprints 2b, 3a and 3c | One integration branch, merged into `main` |
| Two-axis review | `/code-review` (Standards and Spec, in parallel) | After each ticket and each build | Findings, fixed as `fix-<n>` |
| Looking back | `/retro`, `/writing-for-agents` | After each build | New hooks, scripts and lessons in `method.md` |
| Side trips | `/research`, `/prototype`, `/to-questionnaire`, `/wizard`, `/handoff`, `/wait-what` | Now and then | Research notes, prototypes, `bin/deploy-staging` |

Never used here: `/triage`, `/wayfinder`, `/diagnosing-bugs`, `/improve-codebase-architecture`.

Keep the grilling, spec and tickets in one session; start each ticket fresh. Tickets follow `docs/agents/issue-tracker.md`.

## Ways of working that proved their worth

- **Pairing on tests.** Before code, agree the seams and a short list of tests (about five, ranked by risk). The agent writes them failing, the developer sees them red, then the agent makes them pass.
- **Commit points.** The agent stops at each commit with a proposed message; nothing is pushed by the agent.
- **Wording.** Participant-facing wording the content owner has not seen is recorded the day it changes, in the wording document kept beside the repo (see `AGENTS.md`).
- **`✨` marks AI-produced comments and docs** (see `AGENTS.md`).

## Tools

| Tool | What it does |
|---|---|
| `bin/pytest-expect "all passed"` | Runs pytest and checks the summary is the one expected; `"named failed, rest passed" --why "<test>=<words>"` for a red step. Counts tests itself. |
| `bin/worktree` | Makes a git worktree for a ticket under `.claude/worktrees/`, linked to the main checkout's frontend build. |
| `bin/build-watch` | Follows a parallel build's tool log, filtered to what matters. |
| `bin/tool-log` | Reads `.claude/tool-log.txt`, the log of every tool call. |
| `bin/screenshot` | Draws pages saved by snapshot tests as PNGs (needs the Playwright venv; see the script). |
| `bin/deploy-staging` | Interactive walk through a staging deploy. |

Hooks in `.claude/hooks/`, wired up in `.claude/settings.json`:

- `bash-guard.sh` refuses `git push` and `rm` (use `trash`), asks before risky git, and wants a description on every command. Its cases are in `bash-guard-cases.txt`.
- `migration-guard.sh` stops hand-written migrations: run `makemigrations`, then read what it made.
- `user-only-skill.sh` keeps the agent from running skills meant to be typed by the developer.
- `tool-log.sh` writes the tool log.

For a parallel build, `.claude/settings.build.json` loosens the ask rules; `method.md` says how to swap it in and back.

## What stayed local

The first developer's agent memory, tool logs, session transcripts, meeting notes, the content owner's feedback files and the per-build notes in `.claude/builds/NN-*/` were not committed: they hold names and conversations. `method.md` carries every lesson they produced.
