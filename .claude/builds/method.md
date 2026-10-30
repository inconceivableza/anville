# The /implement-spec build method

> ✨ Drafted with AI assistance, from the sprint 3a build (20–21 Oct) and the builds before it. The per-build folders it names stayed on the first developer's machine.

This file is the method; each build's folder, `.claude/builds/NN-<build>/`, holds only what is particular to that build: its brief (`implement-spec-<build>.md`) and its shared brief for implementers (`<build>-shared-brief.md`), plus anything written during or after it (end report, notes). Where a build's brief differs from this file, the build's brief wins. Only this file and the newest folder are current: older folders are history, read when looking back, never copied as a template. A lesson learned in a build is written here, not carried forward from brief to brief.

A build starts in a fresh session, auto mode on, with:

`/implement-spec <ticket folder> — first read .claude/builds/method.md in full, then .claude/builds/NN-<build>/implement-spec-<build>.md from the heading "The developer's brief": together they are the brief for this build and override the skill where they differ; where they differ from each other, the build's file wins.`

The spec is `.scratch/whatever-you-do-milestone-1/spec.md`; the tickets are the named folder alone (other folders hold parked tickets that still read `ready-for-agent`).

`<branch>` below is the build's integration branch, named in its brief.

## The developer's checklist (the run skips this part)

Paths are from the main checkout (the repo's root). The **integration worktree** is a second checkout at `.claude/worktrees/integration`, on `<branch>`: every finished ticket is merged into it, so it is the build's combined result so far.

**Before starting**
1. `git status` is clean on `main`, and `git worktree list` shows the main checkout alone.
2. PostgreSQL is running: `docker compose up -d`. The dev database is up to date with `main`: `python manage.py migrate`, then `python manage.py showmigrations | grep "\[ \]"` prints nothing. The build's brief says whether `.env` needs anything new.
3. Loosen the ask rules for the build. First `diff .claude/settings.json .claude/settings.build.json`: no output means they are still loosened from the last build, so skip the `cp` (it would overwrite the copy of your normal rules). Otherwise:
   `cp .claude/settings.json .claude/settings.before-build.json && cp .claude/settings.build.json .claude/settings.json`
4. Stop any `runserver` on `main`.
5. In a second terminal: `bin/build-watch`.
6. Start a fresh session with the line above, auto mode on.

**During the run**, in a terminal in the integration worktree (`cd .claude/worktrees/integration`):
- once, when the run says the worktree is ready: `cd frontend && npm ci && npm run build && cd ..`
- nothing else is needed until the end: wording and hand checks wait for it. You may still look in and send findings to the run's session.

**At the end**
1. Before your hand checks, in the integration worktree: `python manage.py migrate` if the run reports a migration; `cd frontend && npm run build && cd ..` if it reports a frontend change; load both pathways again if a ticket changed one (`python manage.py load_pathway pathways/whatever-you-do.json` and `python manage.py load_pathway pathways/whatever-you-do-faithful-port.json`). Then `python manage.py runserver`.
2. Walk the hand checks with a **fresh participant**: a participant stays on the version they started, so one from before the reload sees none of the build's rules.
3. Review `git diff main...<branch>`, the new sentences the run lists, and the `docs/manual-checks.md` entries it names.
4. Merge `<branch>` into `main` (the run proposes the message). Deploy staging when you choose.
5. Restore the ask rules: `mv .claude/settings.before-build.json .claude/settings.json`
6. Run the clean-up commands the run's last report gives.

---

## For the run

### Authorisation

The build's brief states it; the usual form, when the developer has waived pairing for the build:
- implementer subagents and you committing on `ticket/*` branches and on `<branch>`, cut from `main`, and merging tickets into it;
- running pytest without the developer's red/green report (the pairing rule is relaxed for the build: the developer reviews the diff and does the hand checks, not each step);
- running `makemigrations` inside a worktree, under the migrations rule below. Never `migrate` against the dev database: tests make their own.

It does **not** cover `main` or any push: stop with a proposed message before anything lands on `main`. Tell each subagent, in its prompt, that this authorisation came from the developer, so a commit is never "unrequested".

### What a build's brief gives

The tickets and their chains; the ADRs to read whole for which tickets; the order beyond the `**Blocked by:**` lines; where tickets meet; what each ticket touches (`frontend/`, migration, faithful port); setup particulars; the migrations expected; anything new in `.env`; the agreed tests; and what the end report leads with. If the developer starts a build with only some chains, work only those, and end as below.

### Saving usage

- A big sprint is split into **runs**, each a fresh session on the same integration branch, working only its chains; the build's brief gives the runs as a table that is the task graph. The orchestrator reads this file and the build's brief, not the spec or the tickets.
- Implementers read only the build's **self-contained shared brief**, never this file; their prompts are pointers only.
- Light tickets (wording, look, homepage) run on a smaller model, named in the brief; engine, access and privacy work, fixes and the code review run on the session's.
- The orchestrator merges a ticket itself on its report's count, migrations check and `git -C MAIN status`, without a merger subagent or rereading the diff, unless something is wrong.
- When the tip has moved since a ticket merged it in, the orchestrator merges the ticket into the integration worktree itself if git merges it cleanly, then runs the whole suite there once (`"all passed"`). Only a conflict sends the ticket back to its implementer: resuming one reloads its whole context (06, run 1: 87 and fix-2 were resumed just to merge).
- A one-line change to wording or look (a label, a sentence, a colour) the orchestrator makes itself in the integration worktree with Edit, commits with `-F`, and runs the suite on: a subagent spends 40,000 tokens starting up for it (06, run 2: fix-14 changed one sentence). Anything touching engine rules, access, privacy or tests still goes to an implementer.
- Findings from hand checks are grouped before briefing: one implementer per page or area takes every finding on it, rather than one per finding; the developer is asked to send findings together where they can.
- Small follow-ups (one file, wording or a template) and fixes found in hand checks that change only wording or look run on the smaller model; anything touching engine rules, access or privacy stays on the session's.
- `pytest-expect` prints progress lines only in a terminal, so agents' runs return just the FAILED/ERROR lines and the verdict.

### Order

**At most four implementers at a time.** When a slot frees, an unblocked chain ticket goes first, then the next single in the brief's order. Start the head of the longest path first.

**Where tickets meet:** whichever merges second takes the other's change in when it merges the tip, keeping both. The brief lists the shared files.

### Lessons from the earlier builds (follow them)

1. **The orchestrator never `cd`s.** Subagents inherit its shell's directory. Use `git -C` and absolute paths. Since 06, run 3 (two slips at setup), `.claude/settings.local.json` sets `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1`, so every Bash call starts back in MAIN whatever the last one did; it is read at startup, so a session started before it is unprotected.
2. **The orchestrator makes each worktree with `MAIN/bin/worktree <ticket> <branch>`**, naming it by the ticket's full prefix (`A1-64`, `B1B-67a`). Subagents don't use `isolation: "worktree"`: that started from `main`, and auto mode refused subagents' links. The script prints one-line commands for the worktree and whether its `.env` link is set; pass them on. It is safe to run again: a branch left without its worktree gets one (06, run 1, where a pipe into `head` left 92 and 94 half-made).
3. **A ticket that changes `frontend/` gets `--own-dist` from the start**, and its subagent runs `npm ci` and `npm run build` in its own worktree. "Possibly" gets it too. A ticket without it that finds it needs `frontend/` stops and reports, rather than building into the main checkout's `dist`.
4. **Subagents write only in their worktree, never MAIN.** MAIN paths are for reading. Point each subagent at its worktree's copy of the ticket; every write, tickets and spec included, goes to the worktree (53c edited the main checkout's ticket, 19 Oct).
5. **Each Bash call starts in MAIN; a `cd` does not carry over to the next call.** So every test or `manage.py` command runs as `cd <worktree> && MAIN/bin/pytest-expect --db <ticket> "all passed" <paths>` (or `cd <worktree> && MAIN/.venv/bin/python manage.py …`). This is the one exception to the no-cd-chains rule, for subagents in worktrees only. `--db` gives each ticket its own test database, and `pytest-expect` refuses `--db` from the main checkout (fix-8, 20 Oct, ran main's tests from there and reported them as its own).
6. **Counts come from pytest, never from arithmetic.** `pytest-expect` collects the same args first: `"all passed"` expects every collected test to pass, `"1 failed, rest passed"` fills in the rest, and a plain number that doesn't match stops before running. It also stops at once when a run that renders pages has no frontend build, or when the database can't be reached, and past 20 failures it shows the first 10 and the commonest reasons rather than every line. Every report quotes the run's `collected N` line and how N differs from the tip's measured count (tests added, less any removed, named). The orchestrator collects the ticket's worktree before merging and the integration tip after (06, run 1: about ten runs lost to guessed totals, and one six-minute run to a missing build).
7. **Every report quotes `git -C MAIN status --short`**, and the orchestrator runs it too after every merge. Anything there stops the run until it is explained.
8. **Read the comment above anything you change.** Keep the reason it gives, or say in the report why it no longer holds (fix-7 undid the photo fix by changing a rule without reading why it was there).
9. **Commits:** stage by name; message written with Write to a file, then `git commit -F`. A message names no person, not even by role ("the content owner", "the developer"): it says what changed, not who chose it (06, run 3). A local pre-commit hook (`.git/hooks/pre-commit`, shared by every worktree) refuses added lines over 120 characters, ruff errors on added lines, Markdown headings without blank lines around them, and models out of step with migrations: fix and stage again; `--no-verify` is the developer's alone, and the guard asks. Shell writes are left to run inside `.claude/worktrees/`, since the developer reviews a build's diff, not each edit. If auto mode refuses a commit, the subagent stops and reports; the orchestrator brings it to the developer, never commits it on the subagent's behalf unasked.
10. **Clean-up:** `git worktree remove --force` and `git branch -D ticket/<t>`; hand the developer the commands, never run them.
11. **Tests and `.env`:** a test that depends on a setting the developer's `.env` may set (`ANVILLE_DEMO_NOTICE`, the Google client pair, the email settings) sets it itself, so the suite passes whatever `.env` holds.
12. **Chain a merge's checks with `&&`, never `;`,** and run the suite in a subshell (`(cd <integration> && …)`) so the orchestrator's shell stays in MAIN. With `;`, a conflicted merge went on to run the suite on a half-merged tree (06, run 2).
13. **A template comment over more than one line is `{% comment %}`, never `{# #}`.** Django's short comment ends at the line's end, so a two-line `{# #}` prints on the page; the suite passed with one showing on every section page (06, run 3, fix-16). Grep a template change for a `{#` without its `#}` before committing.

### Setup (first, on `<branch>` from `main`)

Create the branch (`git -C MAIN branch <branch> main`). Add its worktree at `MAIN/.claude/worktrees/integration` with `git -C MAIN worktree add <path> <branch>` and a link to `MAIN/.env`, as `bin/worktree` makes, but with its own frontend build rather than a link to `MAIN/frontend/dist`. Hand the developer its `npm ci` and `npm run build` rather than running them.

Run the whole suite once in the integration worktree (`cd <integration> && MAIN/bin/pytest-expect --db integration "<the last known count> passed"`): the summary it prints is the tip's count every first report adds to. If two parallel tickets will add the same file, URL module or pathway field, stub it here first (the organisations build's routes).

### Migrations

- Never hand-write a schema migration; `makemigrations <app>` in the worktree. A data migration starts from `makemigrations --empty <app>`, with a reverse.
- Two tickets made in parallel start from the same number. Whichever merges second, while still on its ticket branch, trashes its own unmerged migration after merging the tip in, and runs `makemigrations <app>` again. Never a merge migration.
- Before reporting, after merging the tip in: one leaf per app, proved with `makemigrations --check --dry-run`.
- The merger checks again after each merge. A migration on `<branch>` is never edited or regenerated: the developer may already have applied it.
- Anything stored before the change (staging has some) must still load: say in the report how it is read.

### Shared brief for every implementer

The build's folder holds `<build>-shared-brief.md`: MAIN, the authorisation in a sentence, what to read first (AGENTS.md, CODING_STANDARDS.md, issue-tracker.md, the ticket in the worktree, its spec sections), the rules below written out so it stands alone, the commands, and the steps before reporting. Point each subagent at it. Its rules:
- Read MAIN/AGENTS.md, MAIN/CODING_STANDARDS.md and MAIN/docs/agents/issue-tracker.md by absolute path (they are local-only, not in worktrees). Read the ticket in your worktree and only the spec sections its `**Spec:**` line names (grep their headings), and any ADR it or the build's brief names. Grep prototypes in `Prototypes for reference/`; never read one whole. The look is v3's (`whatever-you-do-site-hackethon-artifact-v3/index.html`), with Instrument Sans for text.
- Build with the `tdd` skill against the ticket's agreed list; that list is the cap. A behaviour it lacks that would harm someone or leak or lose data if broken gets a test and a line in the report; anything else, ask.
- Commit at each green step, ticket kept in step (`claimed` → criteria ticked → `resolved`, as issue-tracker.md says, including Carried from and Handed over). Comments carry ✨; ticket and spec files never do.
- Read the comment above anything you change (lesson 8).
- Copy: authored wording goes in the pathway document, in both pathway files where the ticket says so; engine wording (the next-step panel, refusals) goes where the engine's wording already lives. Where a ticket quotes copy, use it as written. Where it gives none, keep the prototype's sentence and say only what's true now; list every new or changed user-facing sentence in the report, quoting what it replaces. The orchestrator records them in the content owner's wording document in MAIN, which implementers can't write (06, run 2: added to twenty prompts by hand).
- *Whatever You Do* only, where the ticket says so: the faithful port's behaviour stays as it is, and its existing tests stay green unchanged. Its look may change through shared styles and templates; a change that needs a faithful-port test edited stops and reports (06, run 2: 89 read "unchanged" as covering the look too, and edited two port tests).
- A look change is seen before it's reported: the implementer saves each changed page from a throwaway `snap_<name>.py` test and draws it with `MAIN/bin/screenshot <worktree>` (no runserver; the changed element alone, at one width unless the change is to layout, since each picture costs a reader 1,000–1,600 tokens), Reads the PNGs, and lists their paths in the report; the orchestrator Reads them before merging (06, run 2: half its fixes were looks no agent had seen).
- A UI change adds its checks to `docs/manual-checks.md` under a heading naming the ticket (`### Ticket <NN>: <title>`, or `### <build>-r<run>-fix-<n>: <title>` for a fix), in the section where its page's checks already live: what to open, what to look for, at phone width too, and whether it needs a participant started after the pathway was loaded again.
- Leave nothing untrue: update whatever the ticket makes untrue in the README, the spec (in the worktree) and `docs/manual-checks.md`, quoted wording included. Grep all three for each sentence, label and status it changes or removes.
- Never read `.env`, never push, never start runserver.
- Every change goes to the worktree's own files (lesson 4); every test or `manage.py` command runs as `cd <worktree> && …` (lesson 5). Write the commit message to `<worktree>/.git-commit-msg.txt` (untracked: never stage it), commit with `git -C <worktree> commit -F` on it, then `trash` it. End every message with a `Co-Authored-By:` line naming the implementer's own model and no other trailer (a local commit-msg hook refuses an agent's commit without one). Delete files only with `trash`.
- Before reporting: merge the `<branch>` tip in, follow the migrations rule, and run the whole suite green against the exact count expected (lesson 6).
- Report in under 15 lines: commits; the final summary line with the count expected and how it was reached; `git -C MAIN status --short`, quoted; criteria met or carried; migrations; whether `frontend/` changed; new user-facing sentences; the places changed in the README, spec and manual checks; decisions the spec didn't make; anything refused (exact error).

### Settings, `.env` and email

Nobody reads `.env`. A ticket that adds a setting gives it a default under which development and the tests need nothing in `.env`, adds a commented line to `.env.example` (and to `secrets.example.yaml` or the chart's values where a deployed environment needs it), and says so. When the developer has to add something to their own `.env` for a hand check, the run says so in a **Your step:**, naming the setting and what to put, never a value read from anywhere. In development email goes to the `runserver` terminal.

### Telling the developer

Wording and hand checks wait for the end.
- After each merge, one or two lines: the ticket, whether it brought a migration or a frontend change. Merge a simple ticket yourself once its suite is green, its count matches and its migrations check passes.
- Use a **Your step:** message, with a push notification if the tool is available, only for what blocks the run or is the developer's: the integration worktree's `npm ci` and build, anything refused, and the end.
- Before telling the developer how a page behaves today (where something sits, what it leads to, what colour it is), open its template or view and quote the line the claim rests on. Notes, decisions files and screenshots describe earlier versions (06, run 2: a row placed from run 1's notes and a pre-87 screenshot, and the fix brief built on it).
- The developer may send findings while the run goes on. Each becomes a fix on its own `ticket/fix-<n>` branch, named `<build>-r<run>-fix-<n>` from sprint 3c run 3 on (06 has a fix-16 from an earlier build and from run 2), built and merged like a ticket, and takes a slot under the cap. A fix to a page a ticket not yet started will change merges before that ticket starts.

### Agreed tests

Agreed with the developer per ticket before the brief is finished: the seams, then one line per behaviour, ranked by risk so the developer can cut from the bottom. Wording and layout are hand checks, not tests (spec, Testing Decisions): where a test must tell which message is chosen, it reads the text from the document rather than a literal.

### End

Through the run, keep a local decisions file in the build's folder (`run-<N>-decisions.md`, or one per build): the developer's calls, the implementers' calls that stood, what is still open, process slips. Add each call when it is made, hand checks after the end report included (06, run 1).

If the developer says usage allows, `/code-review` over `<branch>` against `main`, with fixes in one implementer; otherwise skip it. Then stop and report to the developer:
- a proposed message for merging `<branch>` into `main`;
- the migrations to run, whether the frontend needs building, and whether the pathways need loading again;
- the hand checks to do, from `docs/manual-checks.md`, ticket by ticket, with a fresh participant, in the order the brief gives;
- every new user-facing sentence to check;
- the clean-up commands: one `git worktree remove --force` and one `git branch -D` per ticket and fix, then the same for the integration worktree and `<branch>` once merged;
- that the ask rules are restored after the build: `mv .claude/settings.before-build.json .claude/settings.json`.

**Findings after the end report.** Build the first five or so as fixes in the same session. Past that, the hand checks have become their own run: write each finding not yet started into the decisions file as an open item, give the developer a starting line for a **fix run** (a fresh session on the same `<branch>`, reading this file, the build's brief and the decisions file, building those findings as fixes), and stop. A session carrying a run and a long tail of fixes runs out of context and usage mid-work (06, run 2: 21 fixes after the end report, and the code review's spec reviewer cut off by the usage limit).

## Tried, and what we kept

- **Pairing stops per test** → waived per build, the developer's call, with a capped test list agreed per ticket up front (01 on). Kept.
- **Subagents with `isolation: "worktree"`** started from `main` and had their links refused (01, first attempt) → `bin/worktree` from the orchestrator. Kept.
- **The orchestrator `cd`ing** sent every later subagent into one worktree (01, first attempt) → never. Kept.
- **A shared test database** for parallel tickets (01, first attempt) → `pytest-expect --db` per ticket, refused from the main checkout (03). Kept.
- **A plain `cd` as the first Bash call** (01, 02) → `cd <worktree> && …` on every call, since a `cd` doesn't carry over (03). Kept.
- **A setup commit stubbing shared files** (01) → only when two tickets will add the same file; otherwise "Where tickets meet" (04). Kept, as needed.
- **The whole frontier at once** (02: 24 tickets) → at most four implementers (04). Kept.
- **Hand checks while the run goes on** (02) → wait for the end (03, 04).
- **One ticket at a time, with a quick check after each** (05, sprint 3b) → built with `/implement`, one session per ticket, not this method: with no parallel work, the orchestrator and subagents only added reading and relays. Its brief (`05-sprint-3b/implement-sprint-3b.md`) borrows lessons 8 and 11, the migrations rule and the shared brief's copy and docs rules from here.
- **Findings during the run as `ticket/fix-<n>`** (02 on) → kept, under the slot cap (04). In 03 they grew to 28 fixes and the end report sprawled.
- **Separate walkthrough, notes, limit and end-report files** (02), an end-report file (03) → the run's last report and `docs/manual-checks.md` (04 left no file on disk).
- **A bare "passed"** let a wrong-checkout run pass as a ticket's (03, fix-8) → exact expected counts, and `git -C MAIN status` quoted in every report (03, 04). Kept.
- **Changing a rule without reading its comment** undid the photo fix (03, fix-7) → read the comment above anything changed. Kept.
- **Look tickets without `--own-dist`** risked building into the main checkout's `dist` (03) → `--own-dist` from the start for anything that may touch `frontend/`. Kept.
- **Docs caught up after the build** (the README and manual checks trailed 3a until `346aa94`) → every ticket keeps the README, spec and manual checks true, quoted wording included, with its checks under a heading naming it (from 3b). Kept.
- **Tests agreed for every ticket before the build** (01–04) → sprint 3b agrees each ticket's tests as it starts, against the code it builds on, in the same message as the last ticket's check.
- **`/code-review` at the end**: run in 01 and 03; left optional at 02's end report. Now if usage allows. Kept.
- **Counting by hand with `--collect-only`** (06, run 1, after guessed totals) → `pytest-expect` counts itself (`"all passed"`, `"rest passed"`) and stops on a missing frontend build (06, after run 1). Trying.
- **The reviewer finding long lines by hand** (06, run 1) → a local pre-commit hook on added lines only, so old code never blocks a commit (06, after run 1). Trying.
- **Hand-check fixes in the run's own session** (06, run 2: 21 of them) → after about five, a fresh fix run (06, after run 2). Trying.
- **Merge checks chained with `;`** (06, run 2) → `&&`, and `pytest-expect` refuses to run during a merge (06, after run 2). Kept.
- **One session for the whole sprint** (01–04) → sprint 3c tries three runs of a few chains each, a self-contained shared brief, a smaller model for light tickets, merges without a merger subagent, each implementer capping its own test list (at most five, ranked by risk) and a review at each run's end (06). Trying.
