# Handover

> ✨ Drafted with AI assistance.

Where *Whatever You Do* stands at the end of sprint 3c (30 Oct 2026), and what is left.

## Where things are

- **Running and deploying:** `README.md`, then `deploy/README.md` and the staging runbook, `deploy/environments/runbook.md`. Only a staging environment exists; it is publicly reachable and carries a demo notice.
- **Domain words:** `CONTEXT.md`. **Decisions:** `docs/adr/`.
- **Specs and tickets:** `.scratch/<feature>/spec.md` and `.scratch/<feature>/issues/`, worked as `docs/agents/issue-tracker.md` describes. A ticket's `**Status:**` line says whether it is open; `sprint-3plus-or-unassigned/` holds the parked ones.
- **Review rules:** `CODING_STANDARDS.md`.

## Before anyone real takes part

- **Ticket 62** (`sprint-3plus-or-unassigned/62-before-real-participants.md`): the minimum for data protection. Until it is done, every instance holds test data only. The privacy page (`engine/templates/engine/privacy.html`) has four marked placeholders for it.
- Staging's "Stay in touch" form already stores the email addresses people leave, so the privacy page's placeholders are the most urgent part.

## Switched off or not yet built

- **Observer reminders** are built (`send_reminders`, run daily by the chart) but off (`reminders.enabled: false`). Turning them on needs the email provider's processing agreement (ticket 62).
- **The letter to your future self** is written and stored, and nothing more: nothing seals it until a date or brings it back. The quarterly check-in prototype (`Prototypes for reference/quarterly-checkin-prototype.html`) keeps it sealed in the app until the fourth check-in, about twelve months on. Its wording ("let it find you again") should say only what is true until that is built.
- **Evaluation autosave:** the sort keeps placed cards only in the browser until "Send", so leaving part-way loses them.

## Open tickets worth doing next

- **76**, staging backup and restore: the nightly backup and one rehearsed restore. Needs the Storage Box account.
- **63**, production hardening: before a production environment is stood up.
- **103**, sign-in leaving the page loading: needs checking by hand on staging.

## Last review

The two-axis review last covered main up to `e93eaf3` (28 Oct). The work after it, to the end of sprint 3c, has had only a quick scan for risky patterns and deserves a proper review.
