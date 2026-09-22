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

After changing anything in `frontend/src/`, run `npm run build` again in `frontend/`.

## Loading a pathway

A pathway is a JSON file in `pathways/`, checked against `engine/document/pathway.schema.json` and then a linter for cross-references and duplicate identifiers. Load one with:

```sh
python manage.py load_pathway pathways/example.json
```

Loading validates the file and prints any problems with their document paths. A valid file becomes an immutable pathway version, which is then published. Loading unchanged content again does nothing. Loading content you had before publishes that earlier version again.

A participant who has saved an answer stays on the version they started, even after a later one is published. Everyone else sees the latest published version. So check a content change by signing out and signing up as a new participant.

## Answers

Each answer saves by itself as the participant types or chooses, and only that answer is written. Answers are checked on the server against their block, and a participant signing in anywhere sees them all. Whether a response is test data is recorded on the server (`Response.is_test_data`), never set by a browser.

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
