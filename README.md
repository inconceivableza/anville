# Anville

Anville is a configurable coaching-pathway engine and studio. Its first pathway is *Whatever You Do*, a Christian vocational-calling workbook. See [CONTEXT.md](CONTEXT.md) for the domain language.

> ✨ Written with AI assistance and checked against the setup it describes.

## Prerequisites

- Python 3.13
- Docker (for PostgreSQL 17)
- Node 20.19+ or 22.12+ (for the Vite build)

## First-time setup

```sh
docker compose up -d                       # PostgreSQL on localhost:5432

python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

In `.env`, paste the generated key into `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=true`, and choose an `ANVILLE_ENROLMENT_CODE`. Sign-up is refused while the code is empty.

```sh
python manage.py migrate

cd frontend
npm ci
npm run build
cd ..
```

## Running

```sh
python manage.py runserver
```

Open http://localhost:8000 and sign up with an `@example.com` address and your enrolment code, ticking "I am 18 or over", then agree on the consent page. Use fake data only. If you are already signed in, the sign-up page sends you back to the hub. There is no sign-out button yet, so sign out at http://localhost:8000/accounts/logout/ or use a private window.

Password reset is switched off until email delivery exists (ticket 28a), so sign-in offers no "Forgot your password?" link. To reset a password, run `python manage.py changepassword <username>`. allauth derives each username from the start of the email address (`participant` for participant@example.com, with a suffix if that is taken), so check the admin if unsure.

After changing anything in `frontend/src/`, run `npm run build` again in `frontend/`.

## Age and consent

Sign-up asks for an "I am 18 or over" confirmation beside the enrolment code, and keeps neither: there is no date of birth anywhere (ADR 0004).

Consent is a separate step at `/consent/`, and every page of the pathway waits for it, so the enrolment code never stands in for it. Agreeing records the version of the consent text and when. Declining records nothing at all. A participant withdraws from the same page, reached by "Your consent" at the foot of the hub; the pathway then waits for consent again. Stored answers are kept on withdrawal for now, because what should happen to them is still open.

The consent text is `access/templates/access/consent.html`, and it is a draft for fake data only. Its version is `CONSENT_TEXT_VERSION` in `access/consent.py`. Raise it whenever a change alters what participants consent to, not for a typo, and everyone is asked again before they continue.

## Loading a pathway

A pathway is a JSON file in `pathways/`, checked against `engine/document/pathway.schema.json` and then a linter for cross-references and duplicate identifiers. Load one with:

```sh
python manage.py load_pathway pathways/whatever-you-do.json
```

`pathways/whatever-you-do.json` is *Whatever You Do* itself, as far as it has been authored:
five baseline ratings, Section 1 with its scripture and reflection, the Strengths assessment (the sort and
its results, in a section of its own so the offline track can share it), the calling-statement section
and the letter, with Sections 2 and 4 carrying their hint text until their activities are built.
`pathways/example.json` is a smaller file for trying the loader out.

`pathways/whatever-you-do-faithful-port.json` is the faithful port: the same pathway as the original
prototype has it, without the content owner's later changes (so far, only the fifth baseline rating).
Both documents grow together, and a test fails if they differ in anything else, so the finished
pathway can be compared with the original prototype's. Load it the same way to see the original prototype's
version. Both are titled *Whatever You Do*, so loading one publishes it in place of the other: load
`pathways/whatever-you-do.json` again afterwards to return new participants to the current pathway.

Loading validates the file and prints any problems with their document paths. A valid file becomes an immutable pathway version, which is then published. Loading unchanged content again does nothing. Loading content you had before publishes that earlier version again.

A participant who has saved an answer stays on the version they started, even after a later one is published. Everyone else sees the latest published version. So check a content change by signing out and signing up as a new participant.

## The hub, locks and gates

The hub at `/` is derived by the engine from what a participant has answered and completed: each section's status, its lock, the next step and the counts. None of it is authored, so an author cannot write a status chip or forget a lock.

A section has its own page at `/sections/<id>/`. It opens once every section in its `requires` list is complete. A locked section is decided on the request, never in the markup: its page redirects to the hub, and its blocks refuse an answer. Progress counts only the blocks a participant does something with.

An agreement scale marked `"fixed_once_complete": true` is fixed once it has been answered and its section completed: from then on it cannot be changed, even if the section is reopened. One left blank at completion can still be answered, and is fixed the next time the section is completed. *Whatever You Do* marks its start and end ratings this way, as the original prototype does not let either be revisited. The server refuses a change, and the page shows the rating as chosen but disabled.

A section's `gate` is an optional list of clauses, all of which must pass before the participant may mark it complete. Completing is their own act, and the server re-checks the gate when the button is pressed, so re-enabling it in a browser achieves nothing. Every failing clause shows its own authored message. The clause types are:

| Clause | Reads | Requires |
|---|---|---|
| `has_answer` | any answer | the block has been answered; blank text and an empty list do not count |
| `min_text_length` | text | at least `min` characters, ignoring space at either end |
| `entry_count` | entries | at least `min` entries, or with `only_with_content` only those with something in them |
| `distinct_value_count` | entries | at least `min` different values of `field` |
| `every_entry_has` | entries | every entry has a value for `field` — true of no entries, so pair it with `entry_count` |

The gate re-renders with each autosave, so the messages and the button keep up with what is being written without a reload. Completing is also reversible: a completed section stays editable and offers "Mark as not complete", which removes that one completion record and leaves every answer alone. Nothing cascades — sections completed before or after it keep their own records, and a section a participant has completed is never locked again, whatever happens to the sections it required. Changing an answer never un-completes a section by itself; with autosave that would make the hub flicker and could re-lock a later section mid-sentence.

Clauses that carry the same message say it once, so "Answer all four to continue" is written as four `has_answer` clauses and one sentence.

A clause may only name a block whose answer it can read and, except for `has_answer`, only one in its own section; the linter refuses both. `has_answer` may wait on another section's block ("the sort has been done"), which is how Section 1 waits on the Strengths assessment; what another section's answer holds is for that section's own gate. The three entry clauses have no block to name yet, because no block type captures a list of entries: they wait for the contact list and timeline board (tickets 10 and 17). A new kind of clause is a code change, never an expression in the document (ADR 0003).

A `section_link` block leads to another section, named by `section`, with an optional `body`. It shows that section's title and status exactly as the hub does, and a locked section is named but not linked. It takes no answer and counts towards no progress.

A `scripture_reading` block shows its authored passages and a confirm control. The activity beneath it is decided by the server too: until the confirmation is saved, the blocks after it are not sent to the browser and will not accept an answer.

## Answers

Each answer saves by itself as the participant types or chooses, and only that answer is written. A block type is defined in one place, `engine/document/blocks.py`: its authored text, what it captures and whether it counts towards progress all follow from that entry. Answers are checked on the server against their block, and a participant signing in anywhere sees them all. Whether a response is test data is recorded on the server (`Response.is_test_data`), never set by a browser.

A `long_text` block may carry a `placeholder`: ghost text in the empty box, such as the letter's "Dear me,". It is a hint only; the prompt stays the box's label, and the placeholder is never saved as the answer.

Long-text answers are limited to 20,000 characters. The text box carries the same limit and says how much room is left near it. Line breaks are stored as `\n`, although forms send them as `\r\n`. This is the one change made to a participant's text on input, and it keeps the server's count the same as the browser's.

The long-text and 1–10 scale forms also save without JavaScript, through a Save button that is hidden once JavaScript loads. This was added in passing during ticket 03 and is not a standard: later blocks, especially the interactive ones such as the sort and the timeline, need not work without JavaScript, and this fallback may be removed.

## Scoring and results

A `sort_assessment` block's answer is the whole sort, sent as JSON: every item of the pathway's instrument, each with the `bucket` it was placed in and a whole `value` from 0 to 100. The server checks it against that pathway version's own items and buckets. The linter refuses a pathway with a sort but no buckets, items, frameworks or scoring method, and a sort whose section's gate has no `has_answer` clause for it. Until the sort is in, its section offers no way to complete it, as in the prototype.

A sort is scored once, when it is submitted, by the method the document names in `measurement.scoring` (ADR 0003). There is one method, `compositional_share`, the prototype's: each construct's share of the grand total, rounded half up as JavaScript rounds, ranked with ties kept in declaration order. A method is frozen once any response has been scored with it, so a change in behaviour is a new name. The result is stored with the answer and never recomputed, and a second sort is refused because retake does not exist yet.

The sort itself is a JavaScript widget, `frontend/src/sort.js`: one card at a time into the buckets, with undo, then a slider per item seeded from its bucket. It sends the whole sort once, and the server answers by sending the browser to the results.

The results page, `/results/<block_id>/`, shows the stored result in the wording of the document's `presentation`: a heading and subtitle per framework, a description, persona and tone per construct, the disclaimer, and a title in which `{name}` is the participant's username. Colours stay in the stylesheet: a construct names a tone, and a framework's bars are coloured by tone, or with `"bars": "rank"` by rank, so tied scores share a colour.

The golden fixtures in `tests/core/golden/` are the prototype's own scoring output. To add a case, edit `prototype_scoring.mjs` and run `node tests/core/golden/prototype_scoring.mjs` from the repository root.

## Tests

```sh
pytest
```

Postgres must be running and the frontend must be built first. Tests sit at two seams:

- `tests/journeys/`: the participant journey over HTTP, through Django's test client against real PostgreSQL
- `tests/core/`: pure functions, with no browser and no database

Nothing runs a browser, so what JavaScript, CSS and assistive technology do is checked by hand, using [docs/manual-checks.md](docs/manual-checks.md).

## Where decisions live

- [docs/adr/](docs/adr/): architecture decisions
- `.scratch/<feature>/`: specs and tickets
- [docs/prototype/](docs/prototype/): behavioural reference for the prototype
