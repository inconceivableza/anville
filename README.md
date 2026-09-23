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

Open http://localhost:8000 and sign up with an `@example.com` address and your enrolment code. Use fake data only. If you are already signed in, the sign-up page sends you back to the hub. There is no sign-out button yet, so sign out at http://localhost:8000/accounts/logout/ or use a private window.

Password reset is switched off until email delivery exists (ticket 28), so sign-in offers no "Forgot your password?" link. To reset a password, run `python manage.py changepassword <username>`. allauth derives each username from the start of the email address (`participant` for participant@example.com, with a suffix if that is taken), so check the admin if unsure.

After changing anything in `frontend/src/`, run `npm run build` again in `frontend/`.

## Loading a pathway

A pathway is a JSON file in `pathways/`, checked against `engine/document/pathway.schema.json` and then a linter for cross-references and duplicate identifiers. Load one with:

```sh
python manage.py load_pathway pathways/example.json
```

Loading validates the file and prints any problems with their document paths. A valid file becomes an immutable pathway version, which is then published. Loading unchanged content again does nothing. Loading content you had before publishes that earlier version again.

A participant who has saved an answer stays on the version they started, even after a later one is published. Everyone else sees the latest published version. So check a content change by signing out and signing up as a new participant.

## The hub, locks and gates

The hub at `/` is derived by the engine from what a participant has answered and completed: each section's status, its lock, the next step and the counts. None of it is authored, so an author cannot write a status chip or forget a lock.

A section has its own page at `/sections/<id>/`. It opens once every section in its `requires` list is complete. A locked section is decided on the request, never in the markup: its page redirects to the hub, and its blocks refuse an answer. Progress counts only the blocks a participant does something with.

A section's `gate` is an optional list of clauses, all of which must pass before the participant may mark it complete. Completing is their own act, and the server re-checks the gate when the button is pressed, so re-enabling it in a browser achieves nothing. Every failing clause shows its own authored message. The clause types are:

| Clause | Reads | Requires |
|---|---|---|
| `has_answer` | any answer | the block has been answered; blank text and an empty list do not count |
| `min_text_length` | text | at least `min` characters, ignoring space at either end |
| `entry_count` | entries | at least `min` entries, or with `only_with_content` only those with something in them |
| `distinct_value_count` | entries | at least `min` different values of `field` |
| `every_entry_has` | entries | every entry has a value for `field` — true of no entries, so pair it with `entry_count` |

Completing is also reversible: a completed section offers "Reopen this section", which removes that one completion record and leaves every answer alone. Nothing cascades — sections completed before or after it keep their own records, and a section a participant has completed is never locked again, whatever happens to the sections it required. Changing an answer never un-completes a section by itself; with autosave that would make the hub flicker and could re-lock a later section mid-sentence.

A clause may only name a block in its own section, and only one whose answer it can read; the linter refuses both. The three entry clauses have no block to name yet, because no block type captures a list of entries: they wait for the contact list and timeline board (tickets 09 and 17). A new kind of clause is a code change, never an expression in the document (ADR 0003).

A `scripture_reading` block shows its authored passages and a confirm control. The activity beneath it is decided by the server too: until the confirmation is saved, the blocks after it are not sent to the browser and will not accept an answer.

## Answers

Each answer saves by itself as the participant types or chooses, and only that answer is written. A block type is defined in one place, `engine/document/blocks.py`: its authored text, what it captures and whether it counts towards progress all follow from that entry. Answers are checked on the server against their block, and a participant signing in anywhere sees them all. Whether a response is test data is recorded on the server (`Response.is_test_data`), never set by a browser.

Long-text answers are limited to 20,000 characters. The text box carries the same limit and says how much room is left near it. Line breaks are stored as `\n`, although forms send them as `\r\n`. This is the one change made to a participant's text on input, and it keeps the server's count the same as the browser's.

The long-text and 1–10 scale forms also save without JavaScript, through a Save button that is hidden once JavaScript loads. This was added in passing during ticket 03 and is not a standard: later blocks, especially the interactive ones such as the sort and the timeline, need not work without JavaScript, and this fallback may be removed.

## Tests

```sh
pytest
```

Postgres must be running and the frontend must be built first. Tests sit at two seams:

- `tests/journeys/`: the participant journey over HTTP, through Django's test client against real PostgreSQL
- `tests/core/`: pure functions, with no browser and no database

## Where decisions live

- [docs/adr/](docs/adr/): architecture decisions
- `.scratch/<feature>/`: specs and tickets
- [docs/prototype/](docs/prototype/): behavioural reference for the prototype
