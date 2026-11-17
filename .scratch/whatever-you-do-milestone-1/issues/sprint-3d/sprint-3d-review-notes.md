Sprint 3d build: end report

The build is done. sprint-3d holds tickets 105–114, fix 1 and the change to Sections 3–5's finish (74 commits ahead of main). The final tip passes all 1703 tests (up from 1647), with no migrations outstanding. Tickets 110 and 112 each have one criterion left open (the photos), handed to 115. Tickets 115 and 116 are yours, so they're still ready-for-human. Nothing is on main and nothing is pushed.

Your steps

1. ✓ Prepare the integration worktree:
   - cd .claude/worktrees/integration
   - Apply migration engine/0031_signupchoice: /workspace/.venv-linux/bin/python manage.py migrate
   - Reload Whatever You Do: /workspace/.venv-linux/bin/python manage.py load_pathway pathways/whatever-you-do.json. The faithful port is unchanged.
   - The frontend is already built in the integration worktree.
   - Run runserver on a port other than your usual 8000.
2. Hand checks, with a fresh participant started after the reload. They're under these headings in docs/manual-checks.md:
   - ✓ Ticket 110 and Ticket 111: the homepage.
   - ✓ Ticket 112: Before we begin.
   - Ticket 108: the sort and the tie-break.
   - Ticket 106 and sprint-3d-r1-fix-1: Sections 1 and 2, and the comparison.
   - Ticket 107: the letter.
   - Ticket 109: the observer, coach and account pages.
   - Ticket 113: the demo shortcuts.

   Every look change needs your eye. bin/screenshot can't run in this container (no Playwright venv, and snap.py points at a Mac path), so no implementer saw a rendered page.
3. Review git diff main...sprint-3d. All the new and changed sentences are in "Part 3: Sprint 3d" of Whatever You Do - wording changes.md.
4. Merge: git merge --no-ff -F .claude/builds/07-sprint-3d/merge-message.txt sprint-3d, from the main checkout.
5. Tooling fix, a separate commit to main if you want it: bin/pytest-expect and bin/worktree fall back to .venv-linux. Without that, the database probe fails in this container. Suggested message: chore: pytest-expect and worktree use .venv-linux where .venv is a devcontainer's empty placeholder. Your .claude/settings.json change stays out of it, as you asked.
6. Clean up after merging:
for t in A1-105 F1-114 B1-108 C1-110 D1-112 A2A-106 A2B-107 C2-111 B2-109 E1-113 sprint-3d-r1-fix-1; do git worktree remove --force .claude/worktrees/$t && git branch -D ticket/$t; done
git worktree remove --force .claude/worktrees/integration && git branch -D sprint-3d

Calls worth a look

All of these are in .claude/builds/07-sprint-3d/run-1-decisions.md.

- 113, the demo shortcut and an existing coach: if a participant already has a coach who hasn't accepted, the shortcut issues a new link and accepts through it, so the old copy stops working. Also, just-leading does tie in the Contribution Profile, so the shortcut answers its pairs with the leading gift staying on top.
- Fix 1, the coach's view: the coach's comparison is still headed "How others experience [name]".
- Fix 1, ADRs: ADRs 0005 and 0017 aren't amended. The spec records the change.
- 109, consent text: it kept version 3, so nobody is asked to agree again. The observer note now says "we may email you a reminder".
- 107, the letter's date: the date picked on page 2 isn't kept until sealing, so going back offers the default again.
- 111, Stay in touch wording: the choice labels, the thanks lines and the "Sign up" button are the implementer's wording, for the content owner to see.
- A flaky test: test_hub.py::test_the_row_of_someone_who_withdrew_looks_as_the_row_of_someone_who_sent failed once each for two implementers, then passed on rerun. The final runs were clean, but it's worth a look.

Still open

- 115, questions for the content owner:
  - the privacy details, for ticket 62;
  - "Your pathway";
  - stopping reminders for good;
  - confirming that a retake deletes what observers sent;
  - showing them this sprint's wording;
  - the photos: wizard boots for 112, journalling for How it works steps 3–4 for 110. Those steps show notebook.jpg and bible.jpg as stand-ins for now.
- 116, the accessibility check: unblocked now.

A /code-review of sprint-3d against main is the method's last optional step. It's heavy on usage, so tell me if you want it.