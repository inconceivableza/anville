# Anville

Anville is a configurable coaching-pathway engine and studio. Its first pathway is *Whatever You Do*, a Christian vocational-calling workbook. See [CONTEXT.md](CONTEXT.md) for the domain language.

> ✨ Written with AI assistance and checked against the setup it describes.

## License and Contributions

The software code and content here are Copyright, although there is intention to publish them under a more permissive license in the near future.
Contributions require a Copyright Assignment from the author.
For any queries, please contact the project.
See [LICENSE.md](LICENSE.md) for the interim license notice.

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

In `.env`, paste the generated key into `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=true`, and set `ANVILLE_ENROLMENT_REQUIRED=false` so anyone can sign up. Left out, the enrolment code is required, and sign-up is refused until you choose an `ANVILLE_ENROLMENT_CODE`.

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

Open http://localhost:8000 for the homepage, press "Begin →" and sign up with an `@example.com` address and your enrolment code, ticking "I am 18 or over", then agree on the consent page. Use fake data only. If you are already signed in, the sign-up page sends you back to the hub. There is no sign-out button yet, so sign out at http://localhost:8000/accounts/logout/ or use a private window.

Password reset is switched off until email delivery exists (ticket 28a), so sign-in offers no "Forgot your password?" link. To reset a password, run `python manage.py changepassword <username>`. allauth derives each username from the start of the email address (`participant` for participant@example.com, with a suffix if that is taken), so check the admin if unsure.

After changing anything in `frontend/src/`, run `npm run build` again in `frontend/`.

## Running in a devcontainer

The setup above assumes you are on the machine running Docker. Inside a devcontainer you usually are not: there is no Docker client, so `docker compose up -d` stays a host command, and a Postgres published on the host's loopback is not reachable from the container. The devcontainer image also has to provide Python 3.13 itself, and the frontend build still has to be run somewhere.

Postgres can live on either side. Pick one.

### Postgres inside the devcontainer

Install PostgreSQL 17 in the devcontainer image and run it there. `compose.yaml` goes unused and `.env` needs no change, because from the container's point of view the database really is on `localhost:5432`. Everything sits in one place, at the cost of rebuilding the image when it changes, and the data lives and dies with the container.

### Postgres from compose on the host

Run `docker compose up -d` on the host as before, and give the `db` service a second network — the one the devcontainer itself runs on — so the two containers can talk to each other directly. The network name is particular to your machine, so this belongs in `compose.override.yaml`, which compose merges over `compose.yaml` automatically and which is gitignored:

```yaml
services:
  db:
    networks:
      - default
      - devcontainer        # whatever network your devcontainer is on

networks:
  devcontainer:
    external: true
```

Both containers are then on the same user-defined Docker network, where Docker's embedded DNS resolves container names, and the devcontainer reaches the database by container name: compose names it after the project directory, so here `anville-db-1:5432`. List both networks: that list replaces the implicit one rather than adding to it, so leaving `default` out would cut the service off from the rest of the project. Keep the `127.0.0.1:5432` publication too if you still want to reach it from the host.

This is worth preferring to a tunnel. The published `127.0.0.1:5432` is the *host's* loopback, which is not the container's, so connecting to `localhost:5432` from inside the devcontainer is simply refused. A shared network removes the problem rather than working around it. If you do tunnel instead, it has to listen *inside* the container and forward out to the host's 5432; a forward that listens on the host is the opposite direction and will fight compose for the port.

### Settings in `.env`

`.env` is a single file on both sides of the mount, so it cannot name the database twice. Leave it as the host's and override the one variable in the container's environment:

```sh
export DATABASE_URL=postgres://anville:anville@anville-db-1:5432/anville
```

`config/settings.py` reads `.env` through django-environ's `read_env()`, which does not overwrite anything already in the environment, so a real environment variable wins over the file. Setting it in the devcontainer's own configuration makes it stick across rebuilds. Nothing else in `.env` differs from the host.

Take care that `DJANGO_SECRET_KEY` does not contain a `$`. Compose reads this same `.env` for its own variable substitution and will warn about, and blank out, anything that looks like `$name` — generate another key if yours trips it.

### Reaching the development server from the host

`runserver` binds to `127.0.0.1:8000`, the container's own loopback, which nothing outside the container can reach. Bind it to every interface instead:

```sh
python manage.py runserver 0.0.0.0:8000
```

Then forward port 8000 from the host into the container. Note this is the opposite direction to the database: here the listener belongs on the host and the traffic travels inward. Editors that attach to a devcontainer generally do this for you — look for their forwarded-ports list — and failing that any `ssh -L` style tunnel listening on the host and pointing at the container's port 8000 will serve.

`DJANGO_ALLOWED_HOSTS` already lists `localhost`, so http://localhost:8000 is accepted. Reaching the site by any other name means adding that name to the list.

One thing to watch if your editor forwards ports automatically: do not let it forward 5432. A listener on the host's 5432 stops compose from binding the port, and in the meantime connections to it are accepted and then hang rather than being refused, which is a slow thing to diagnose.

## Age and consent

Sign-up asks for an "I am 18 or over" confirmation beside the enrolment code, and keeps neither: there is no date of birth anywhere (ADR 0004).

Consent is a separate step at `/consent/`, and every page of the pathway waits for it, so the enrolment code never stands in for it. Agreeing records the version of the consent text and when, then leads a participant with nothing saved straight to their first step, as the prototype goes from its account screen into onboarding (so *Whatever You Do* asks the reason for taking the course first); anyone who has begun goes to the hub. Declining records nothing at all. A participant withdraws from the same page, reached by "Your consent" at the foot of the hub; the pathway then waits for consent again. Stored answers are kept on withdrawal for now, because what should happen to them is still open.

The consent text is `access/templates/access/consent.html`, and it is a draft for fake data only. Its version is `CONSENT_TEXT_VERSION` in `access/consent.py`. Raise it whenever a change alters what participants consent to, not for a typo, and everyone is asked again before they continue.

## Loading a pathway

A pathway is a JSON file in `pathways/`, checked against `engine/document/pathway.schema.json` and then a linter for cross-references and duplicate identifiers. Load one with:

```sh
python manage.py load_pathway pathways/whatever-you-do.json
```

`pathways/whatever-you-do.json` is *Whatever You Do* itself, as far as it has been authored:
five baseline ratings, Section 1 with its scripture and reflection, the Strengths assessment (the sort and
its results, in a section of its own so the offline track can share it), the Workbook and the letter.
Sections 2–4 are done on paper, in the content owner's workbook, which the Workbook section offers as a PDF once
Section 1 is complete, and Section 1 asks for the coach's link and two observers' links before then.
`pathways/example.json` is a smaller file for trying the loader out.

The workbook PDF is `pathways/files/whatever-you-do-workbook.pdf`, served only to a participant who has reached the
Workbook. For now it is the content owner's draft, saved from the Word file in `Prototypes for reference/`, and the
Workbook page says so; replace it, under the same name, with the finished PDF when it arrives, and take the draft
sentence out of the Workbook's text.

`pathways/whatever-you-do-faithful-port.json` is the faithful port: the same pathway as the original
prototype has it, without the content owner's later changes (so far, the fifth baseline rating, the coach page and the
Workbook in place of Sections 2–4, which the faithful port keeps; it also asks for five contacts where *Whatever You
Do* asks for two for now).
Both documents grow together, and a test fails if they differ in anything else, so the finished
pathway can be compared with the original prototype's. Load it the same way to see the original prototype's
version. Both are titled *Whatever You Do*, so loading one publishes it in place of the other: load
`pathways/whatever-you-do.json` again afterwards to return new participants to the current pathway.

Loading validates the file and prints any problems with their document paths. A valid file becomes an immutable pathway version, which is then published. Loading unchanged content again does nothing. Loading content you had before publishes that earlier version again.

A participant who has saved an answer stays on the version they started, even after a later one is published. Everyone else sees the latest published version. So check a content change by signing out and signing up as a new participant.

## The hub, locks and gates

The hub at `/hub/` is derived by the engine from what a participant has answered and completed: each section's status, its lock, the next step and the counts. None of it is authored, so an author cannot write a status chip or forget a lock.

A section may carry an `estimate`, worded as it is shown ("About 15 minutes"): it appears with the section's title on the hub, even while locked, and under its heading on its page as "Whole section: …", until the participant answers something there. Where a section has several activities, the block that starts each one may carry its own `estimate`, shown just above it as "This part: …" whatever has been answered. The lead-ins are the engine's, so an author writes only the figure. *Whatever You Do* gives Section 1 none, since it cannot be finished without the Strengths assessment's longer sort.

A section has its own page at `/sections/<id>/`. It opens once every section in its `requires` list is complete. A locked section is decided on the request, never in the markup: its page redirects to the hub, and its blocks refuse an answer. Progress counts only the blocks a participant does something with.

A `page_break` block (only an `id`) splits a section into pages, played one after another as the original prototype's screens are; a section without one is a single page. The hub still shows the section once, with one estimate and its blocks counted wherever they sit, and leads to the page the participant has reached, or to the first once the section is complete; so do the sidebar and a section link. Each page says which it is ("Page 2 of 3") under the section's heading. Page 1 stays `/sections/<id>/` and each page is also `/sections/<id>/pages/<n>/`. Every page but the last ends in "Continue →", a plain form the server checks against that page's own gate clauses (a clause belongs to the page of the block it names, or to the last page if that block is in another section), and refuses while an unconfirmed reading or a held link on the way holds what follows. The last page ends in the section's completion, which still checks the whole gate, and its checklist also lists anything left unmet on an earlier page. Moving past a page is stored, so a page that needs nothing, such as *Whatever You Do*'s coach page, still holds the participant until they continue. A page not reached is shut: a typed address and completion lead back to the page reached, and an answer or a coach checklist step on it is refused, as behind a lock or an unconfirmed reading. An earlier page stays open through "← Previous page", worded apart from "← Back to the hub" at the top, beside the way on as the coach checklist's "Back" is beside its "Continue →"; it lands at that page's way on, the "Continue →" pressed to leave it, rather than its top. Confirming a reading lands at its confirmation, with what it opened beneath, and each new coach checklist screen, swapped in place, is brought into view and given the focus as a new page would be; the same screen sent back (a refusal, a coach's link issued or revoked) stays where it is. The linter refuses a break that would leave a page empty. A break may carry a `skip_label`, which words the way on from the page it ends while nothing on that page holds an answer, as a secondary button rather than "Continue →"; *Whatever You Do*'s coach page uses the original prototype's "I'll sort this later →" until a coach is kept. Onboarding is split this way: the reason and the start ratings, then (in *Whatever You Do* only) "Walking with a coach", then "Who knows you best?".

An agreement scale marked `"fixed_once_complete": true` is fixed once it has been answered and its section completed: from then on it cannot be changed, even if the section is reopened. One left blank at completion can still be answered, and is fixed the next time the section is completed. *Whatever You Do* marks its start and end ratings this way, as the original prototype does not let either be revisited. The server refuses a change, and the page shows the rating as chosen but disabled.

A section's `gate` is an optional list of clauses, all of which must pass before the participant may mark it complete. Completing is their own act, and the server re-checks the gate when the button is pressed, so re-enabling it in a browser achieves nothing. The button reads "Mark complete" unless the section sets `complete_label`, as *Whatever You Do*'s onboarding does with the prototype's "Continue →". Completing leads back to the hub, which points at the next step, as the prototype's sections do. Every clause's authored message is listed beneath the button, ticked once met, so the list keeps its place and height as answers change. An unmet `links_issued` message is itself a link to where those links are issued: the coach page for a coach checklist, the invitations page for a contact list. The clause types are:

| Clause | Reads | Requires |
|---|---|---|
| `has_answer` | any answer | the block has been answered; blank text and an empty list do not count |
| `min_text_length` | text | at least `min` characters, ignoring space at either end |
| `entry_count` | entries | at least `min` entries, or with `only_with_content` only those with something in them; with `allow_none`, no entries at all also passes |
| `distinct_value_count` | entries | at least `min` different values of `field` |
| `every_entry_has` | entries | every entry has a value for `field` — true of no entries, so pair it with `entry_count` |
| `comparison_visited` | a sort | the participant has pressed "Compare with how others see you →" on that sort's results, whatever the comparison then shows: below the minimum of observers, its explanation counts. Loading the comparison's address alone does not, since a browser may load it ahead of time |

The gate re-renders with each autosave, so the messages and the button keep up with what is being written without a reload. Completing is also reversible: a completed section stays editable and offers "Mark as not complete", which removes that one completion record and leaves every answer alone. Nothing cascades — sections completed before or after it keep their own records, and a section a participant has completed is never locked again, whatever happens to the sections it required. Changing an answer never un-completes a section by itself; with autosave that would make the hub flicker and could re-lock a later section mid-sentence.

Clauses that carry the same message say it once, so "Answer all four to continue" is written as four `has_answer` clauses and one sentence.

A clause may only name a block whose answer it can read and, except for `has_answer` and `comparison_visited`, only one in its own section; the linter refuses both. `has_answer` may wait on another section's block ("the sort has been done"), which is how Section 1 waits on the Strengths assessment, and `comparison_visited` on a visit to that sort's comparison; what another section's answer holds is for that section's own gate. The three entry clauses read a contact list, and later the timeline board (ticket 17). A new kind of clause is a code change, never an expression in the document (ADR 0003).

A `section_link` block leads to another section, named by `section`, with an optional `body`. It shows that section's title and status exactly as the hub does, and a locked section is named but not linked. With a `button_label`, such as Section 1's "Open Strengths Assessment →", a button leads there and the title is plain text. With `"holds_what_follows": true`, the blocks after it are held back until the linked section's gate passes, as beneath an unconfirmed scripture reading: they are not sent to the browser and will not accept an answer. The linked section need not be completed. Section 1 holds its reflection this way until the sort is in. The linter refuses a link that holds back its own section, which could never be finished. It takes no answer and counts towards no progress.

A section with `part_of` naming another section is a part of it, as *Whatever You Do*'s Strengths assessment is a part of Section 1, where the original prototype keeps it. The hub and the sidebar list a part within its section's entry. A part has no completion of its own: it is complete once its gate passes, worked out from the answers rather than stored, so the hub, locks and links count it as complete as soon as the sort is in, and a completion posted for it is refused. A part opens only once the participant reaches its section's link to it, so the Strengths assessment waits until Section 1's reading is confirmed; one whose section has no link to it opens with that section, and one whose section is outside the track by its own `requires`. Its page's "← Back", its results page and the end of its comparison lead to the section it is a part of. The linter refuses a `part_of` naming no section, the section itself, or a section that is itself a part, and a part with no gate, which would be complete before it was begun.

A `scripture_reading` block shows its authored passages and a confirm control. The activity beneath it is decided by the server too: until the confirmation is saved, the blocks after it are not sent to the browser and will not accept an answer.

Every passage is from a translation the document declares under `translations`, keyed by its abbreviation, with its `name` and the `notice` its publisher asks for, word for word. The document's `translation` is the one a passage is from unless it names its own `translation`. The linter refuses a translation that is named but not declared, and a passage with no translation to fall back on. A passage from a translation other than the document's shows that translation's abbreviation beside its reference. Every declared notice is on the credits page, which every page links to. The homepage's verse (Colossians 3:23, NIV) belongs to no pathway, so the credits page carries its notice itself; a document declares only the translations its own passages use. The document's own translation's notice therefore begins "Unless otherwise indicated", and each other notice names the passages it covers ("marked NIV"). A passage's text is the translation's word for word: a cut is marked with an ellipsis (…), or, where a passage stops partway through its last verse, its reference may say so instead ("Psalm 37:3–7a"). The publishers' free allowance is 500 verses of each translation, quoting no complete book (the ESV: no more than half of any one book), with scripture under 25% of the work's text.

## Answers

Each answer saves by itself as the participant types or chooses, and only that answer is written. A block type is defined in one place, `engine/document/blocks.py`: its authored text, what it captures and whether it counts towards progress all follow from that entry. Answers are checked on the server against their block, and a participant signing in anywhere sees them all. Whether a response is test data is recorded on the server (`Response.is_test_data`), never set by a browser.

A `long_text` block may carry a `placeholder`: ghost text in the empty box, such as the letter's "Dear me,". It is a hint only; the prompt stays the box's label, and the placeholder is never saved as the answer.

A `single_select` block is a drop-down of authored `options`, each an `id` and a `label`, and saves as soon as one is chosen. The answer is the option's `id`, so a label can be reworded without changing what earlier answers mean; the server refuses anything that is not one of the block's own options, and the linter refuses two options sharing an `id`. An empty choice always leads the list, showing the optional `placeholder` ("Select..."), so an unanswered select never looks answered; choosing it again takes the answer back, as emptying a text box does. Onboarding asks the reason for taking the course this way, and its gate requires it.

A `contact_list` block asks for people who know the participant, a first name and an email address per row, and opens with `min_rows` empty rows (five unless the author says). "+ Add another person" adds a row, up to 50. The whole list saves as each field is left, with empty rows dropped; the server refuses it whole, naming the row, for a row with only a name or only an email, or an email address Django would not accept. These are other people's details, so they are kept as `Contact` records against the response, not among its answers, and someone taken off the list is deleted. The gate and progress still read the list as the block's answer. Onboarding asks this way, and its gate uses `entry_count` with `allow_none`, so the list may be left empty for later, as the prototype's "I'll do this later →" allowed, but not started short. The faithful port asks for the prototype's five; *Whatever You Do* asks for two for now, so it can be tried without inventing five.

A `coach_checklist` block helps the participant choose a coach, as the content owner's coach-selection prototype does: why the choice matters, the candidate's first name, then the authored questions, each answered Yes, Not sure or No. The rule turning the answers into going ahead, a second thought or trying someone else is engine code (`engine/document/coach.py`). None of the answers is stored or logged: they are opinions about another person, including their faith, so they travel only in the form, screen to screen, and the outcome is worked out again from what was posted. Going ahead asks for the coach's name and email address and a tick that the participant has spoken to them; saving keeps only the name and email, as a `Contact` with the coach role, and is refused past a stop. Once saved, the block shows the coach, with "Choose someone else" (the coach is kept until another is saved, which the intro says, with "Keep Sam" to go back to them) and "Remove". While a coach is kept, the way on from their page reads "Continue with Sam →", so it reads apart from the checklist's own "Continue →" when choosing again. It counts towards no progress, no gate may name it, and it can be left without choosing anyone.

Long-text answers are limited to 20,000 characters. The text box carries the same limit and says how much room is left near it. Line breaks are stored as `\n`, although forms send them as `\r\n`. This is the one change made to a participant's text on input, and it keeps the server's count the same as the browser's.

The long-text, single-select, contact-list and 1–10 scale forms also save without JavaScript, through a Save button that is hidden once JavaScript loads. This was added in passing during ticket 03 and is not a standard: later blocks, especially the interactive ones such as the sort and the timeline, need not work without JavaScript, and this fallback may be removed.

## Scoring and results

A `sort_assessment` block's answer is the whole sort, sent as JSON: every item of the pathway's instrument, each with the `bucket` it was placed in and a whole `value` from 0 to 100. The server checks it against that pathway version's own items and buckets. The linter refuses a pathway with a sort but no buckets, items, frameworks or scoring method, and a sort whose section's gate has no `has_answer` clause for it. Until the sort is in, its section offers no way to complete it, as in the prototype.

A sort is scored once, when it is submitted, by the method the document names in `measurement.scoring` (ADR 0003). There is one method, `compositional_share`, the prototype's: each construct's share of the grand total, rounded half up as JavaScript rounds, ranked with ties kept in declaration order. A method is frozen once any response has been scored with it, so a change in behaviour is a new name. The result is stored with the answer and never recomputed, and a second sort is refused because retake does not exist yet.

The sort itself is a JavaScript widget, `frontend/src/sort.js`: one card at a time into the buckets, with undo, then a slider per item seeded from its bucket. It sends the whole sort once, and the server answers by sending the browser to the results. Its own wording around the items (headings, the instruction, the slider ends, the submit button) is the document's `presentation.sort_wording`, keyed by role like any text, with the engine's own (`SORT_WORDING` in `engine/document/blocks.py`) for any field left out. For an observer, `{name}` in it, and in the items and bucket labels, is the participant's name.

The results page, `/results/<block_id>/`, shows the stored result in the wording of the document's `presentation`: a heading and subtitle per framework, a description, persona and tone per construct, the disclaimer, and a title in which `{name}` is the participant's username. Colours stay in the stylesheet: a construct names a tone, and a framework's bars are coloured by tone, or with `"bars": "rank"` by rank, so tied scores share a colour.

The golden fixtures in `tests/core/golden/` are the prototype's own scoring output. To add a case, edit `prototype_scoring.mjs` and run `node tests/core/golden/prototype_scoring.mjs` from the repository root.

## Inviting observers

`/invitations/`, linked from the hub, lists the people on the participant's contact list, each with a link of their own to act as an observer (ADR 0005). The participant issues a link, copies it and sends it themselves; nothing is emailed. A link carries a token of 32 random bytes, of which only a SHA-256 hash is kept as an `Invitation`, so the link is shown only in the page that comes back after issuing it; a lost link is reissued. Issuing redirects back to that page, so a reload never issues again, and the link travels there in a signed, HttpOnly cookie that lasts a minute and is deleted as it is read, never in the address or the session. With JavaScript, htmx follows the same redirect and swaps in that person's row alone, so the page stays put. Each contact has at most one live link: reissuing stops the previous one, and revoking deletes it. A link works for the document's `observers.link_lifetime_days` (30 when left out), and a wrong, expired or revoked link at `/observe/<token>/` gets one refusal, the same for all three, naming nobody. The coach's link is ticket 13c's.

A live link opens the privacy notice (the document's `observers.privacy_notice`, in the observer's wording, or, for a document without one, a stand-in marked as a draft, in `engine/document/observers.py`) and "I'm answering for …", which claims it: the invitation keeps the hash of a new secret of 32 random bytes, which goes to the observer in an `observer` cookie (HttpOnly, path `/observe/`) and once, as a link of their own, `/observe/<secret>/`. The participant's copy then says "already used" (410), so if they claimed it first, the observer notices and asks for a new one. `/observe/` reaches the observer's page by the cookie, which only the claim (a POST) sets, so no other site can plant one; the observer's pages are sent `no-store`. Reissuing replaces the invitation record, so nothing claimed through the old link carries over. Observers have no account; the participant's name is their username until accounts hold one.

The page also shows the pathway's contact list, so a participant who skipped it in onboarding can add people there. Each row of a contact list sends back its contact's id, so a save edits that person in place and their link keeps working; an id that is not one of this list's own is taken as a new person, and someone taken off the list is deleted with their link.

An observer's answers are kept as an `ObserverResponse` (an observer assessment and written answers), attached to the participant's response and never to a contact or invitation. Only submitted ones reach the observer average.

The observer's page runs the same sort widget in observer wording. It sends the observer assessment once, to `/observe/assessment/` by the cookie or to `/observe/<secret>/assessment/` from their own link; the participant's copy of the link is refused there as any wrong link is. The `ObserverResponse` keeps a hash of the claimed secret, prefixed so it never equals the invitation's, so it outlives the link and only the secret finds it again (ADR 0007, ADR 0009). A second send from the same secret is refused (409), and after sending the page only says thank you.

To show the comparison without three real observers, `python manage.py seed_observers --observers 3` creates a fake participant, `seed-participant-<n>@example.com` with the password `information.` (`--password` sets another) and consent already given, with a self-assessment and self-result of their own and that many submitted test observers, their values the same on every run. Everything it creates is marked as test data on the server; it needs a published pathway with an assessment block.

## Settings for a deployed environment

Everything a deployed copy needs is read from the environment, so one build serves every deployment (ADR 0002). [docs/server-approach.md](docs/server-approach.md) describes how a deployment is run. Development needs none of these: left unset, each keeps the behaviour described above.

| Variable | Unset | Set |
|---|---|---|
| `DJANGO_HTTPS` | No forwarded header is trusted and plain HTTP is served | `true` behind a proxy that ends TLS: its `X-Forwarded-Proto` is trusted, plain HTTP is redirected to HTTPS, and the session, CSRF and observer cookies are marked Secure. Never set it without such a proxy in front, or anyone can claim to be on HTTPS |
| `DJANGO_HSTS_SECONDS` | No `Strict-Transport-Security` header | How long browsers should refuse plain HTTP. Only read when `DJANGO_HTTPS` is on |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | None | Further origins allowed to post forms, comma-separated. Not needed when the proxy passes the `Host` header on |
| `DATABASE_CONN_MAX_AGE` | A database connection per request | Seconds to keep a connection for reuse |
| `EMAIL_URL` | Email is fake: each message is printed in the server's output and nothing is delivered | The provider, as `smtp+tls://key:secret@host:587` |
| `DEFAULT_FROM_EMAIL` | `webmaster@localhost` | The address messages come from |
| `ANVILLE_EMAIL_DISCLAIMER` | Messages go as written | For a test system that can reach real mailboxes: every message has `[TEST]` put before its subject and this text at the top of its body, plain and HTML alike. The chart sets it on every staging environment |
| `ANVILLE_DEMO_NOTICE` | Nothing is said | For a demo deployment: this text is shown on the homepage and on the account pages (sign up, sign in), saying it is a demo. The chart sets it on every staging environment |
| `ANVILLE_COMMIT` | `unknown` | The commit the code was built from. The image sets it |

`/healthz` answers `{"status": "ok", "commit": "…"}` when the database can be reached, and 503 when it cannot. It still wants a `Host` header that `DJANGO_ALLOWED_HOSTS` lists.

With `DJANGO_DEBUG` off, errors are printed to the server's output with any observer's or coach's link redacted, since whoever holds such a link can answer as them.

To serve the way a deployment does, gather the static files and start gunicorn, which reads `gunicorn.conf.py`:

```sh
python manage.py collectstatic --noinput
gunicorn
```

gunicorn keeps no access log, for the same reason as the redaction. WhiteNoise serves the static files from `staticfiles/`, and tells browsers to keep Vite's hashed files for good.

### The image

The `Dockerfile` builds the one image every deployment runs: the frontend built by Vite, the static files gathered, and gunicorn started as a user with no privileges. `Dockerfile.dockerignore` admits only what the image needs, because the image is public. To run it against the compose database:

```sh
docker compose --profile app up --build
```

That migrates the database, then serves at http://localhost:8001, beside any `runserver` on 8000. It takes the secret key and enrolment code from `.env` and runs with `DJANGO_DEBUG` off. Plain `docker compose up -d` still starts only the database.

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
