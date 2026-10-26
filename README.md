# Anville

Anville is a configurable coaching-pathway engine and studio. Its first pathway is *Whatever You Do*, a Christian vocational-calling journey. See [CONTEXT.md](CONTEXT.md) for the domain language.

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

Sign-in's "Forgot your password?" emails a reset link. With no `EMAIL_URL` in `.env`, email is fake: the message, link and all, is printed in the `runserver` terminal. You can also run `python manage.py changepassword <username>`, where the username is the account's whole email address (check the admin if unsure).

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
five baseline ratings, then six numbered sections. Section 1 holds the scripture on gifts and the Strengths evaluation
(the sort and its results, in a section of its own so the offline track can share it), and is finished once the sort
is in. Section 2, "How others see you", holds the way to the comparison and the reflection, and opens once Section 1
is finished. Sections 3–5 are done on paper, each in its part of the content owner's workbook, which the section
offers as a PDF, and Section 6 is the letter.
Section 3 opens once Section 1 is finished and the side cards Walk with a coach and Five trusted voices are
complete (a coach has a link, and three people have links), without waiting for Section 2. Section 4 opens once
Sections 1–3 are finished and the coach has accepted; Section 5, and then the letter, each open once the
participant says they have finished the section before. Section 2's reflection waits until the participant has seen
how others see them, which needs at least three people's answers.
`pathways/example.json` is a smaller file for trying the loader out.

The sections' PDFs are `pathways/files/whatever-you-do-workbook-section-2.pdf`, `-section-3.pdf` and
`-section-4.pdf`, for Sections 3, 4 and 5, each served only to a participant who has reached its section. They are
saved from the content owner's Word files in `Prototypes for reference/`, which still number them 2 to 4; replace each,
under the same name, when a new version arrives.

`pathways/whatever-you-do-faithful-port.json` is the faithful port: the same pathway as the original
prototype has it, without the content owner's later changes (so far, the fifth baseline rating, the coach page, a
PDF in place of each of its Sections 2–4's own blocks, which the faithful port keeps, and Section 1 split in two; it
also asks for five contacts where *Whatever You Do* asks for three).
Both documents grow together, and a test fails if they differ in anything else, so the finished
pathway can be compared with the original prototype's. Load it the same way to see the original prototype's
version. Both are titled *Whatever You Do*, so loading one publishes it in place of the other: load
`pathways/whatever-you-do.json` again afterwards to return new participants to the current pathway.

Loading validates the file and prints any problems with their document paths. A valid file becomes an immutable pathway version, which is then published. Loading unchanged content again does nothing. Loading content you had before publishes that earlier version again.

A participant who has saved an answer stays on the version they started, even after a later one is published. Everyone else sees the latest published version. So check a content change by signing out and signing up as a new participant.

## The hub, locks and gates

The hub at `/hub/` is derived by the engine from what a participant has answered and completed: each section's status, its lock, the next step and the counts. None of it is authored, so an author cannot write a status chip or forget a lock.

A section may carry an `estimate`, worded as it is shown ("About 15 minutes"): it appears with the section's title on the hub, even while locked, and under its heading on its page as "Whole section: …", until the participant answers something there. Where a section has several activities, the block that starts each one may carry its own `estimate`, shown just above it as "This part: …" whatever has been answered. The lead-ins are the engine's, so an author writes only the figure. *Whatever You Do* gives Section 1 none, since it cannot be finished without the Strengths evaluation's longer sort, nor Section 2, which waits on other people's answers.

A section has its own page at `/sections/<id>/`. It opens once every section in its `requires` list is complete. A locked section is decided on the request, never in the markup: its page redirects to the hub, and its blocks refuse an answer. Progress counts only the blocks a participant does something with.

A `page_break` block (only an `id`) splits a section into pages, played one after another as the original prototype's screens are; a section without one is a single page. The hub still shows the section once, with one estimate and its blocks counted wherever they sit, and leads to the page the participant has reached, or to the first once the section is complete; so do the sidebar and a section signpost. Each page says which it is ("Page 2 of 3") under the section's heading. Page 1 stays `/sections/<id>/` and each page is also `/sections/<id>/pages/<n>/`. Every page but the last ends in "Continue →", a plain form the server checks against that page's own gate clauses (a clause belongs to the page of the block it names, or to the last page if that block is in another section), and refuses while an unconfirmed reading or a holding signpost on the way holds what follows. The last page ends in the section's completion, which still checks the whole gate, and its checklist also lists anything left unmet on an earlier page. Moving past a page is stored, so a page that needs nothing, such as *Whatever You Do*'s coach page, still holds the participant until they continue. A page not reached is shut: a typed address and completion lead back to the page reached, and an answer or a coach checklist step on it is refused, as behind a lock or an unconfirmed reading. An earlier page stays open through "← Previous page", worded apart from "← Back to the hub" at the top, beside the way on as the coach checklist's "Back" is beside its "Continue →"; it lands at that page's way on, the "Continue →" pressed to leave it, rather than its top. Confirming a reading lands at its confirmation, with what it opened beneath, and each new coach checklist screen, swapped in place, is brought into view and given the focus as a new page would be; the same screen sent back (a refusal, a coach's link issued or revoked) stays where it is. The linter refuses a break that would leave a page empty, and a break carries nothing but its `id`. Onboarding is split this way: the reason and the start ratings, then (in *Whatever You Do* only) "Walking with a coach", then "Who knows you best?".

An agreement scale marked `"fixed_once_complete": true` is fixed once it has been answered and its section completed: from then on it cannot be changed, even if the section is reopened. One left blank at completion can still be answered, and is fixed the next time the section is completed. *Whatever You Do* marks its start and end ratings this way, as the original prototype does not let either be revisited. The server refuses a change, and the page shows the rating as chosen but disabled.

A section's `gate` is an optional list of clauses, all of which must pass before the participant may mark it complete. Completing is their own act, and the server re-checks the gate when the button is pressed, so re-enabling it in a browser achieves nothing. The button reads "Mark complete" unless the section sets `complete_label`, as *Whatever You Do*'s onboarding does with the prototype's "Continue →". Completing leads back to the hub, which points at the next step, as the prototype's sections do. Every clause's authored message is listed beneath the button, ticked once met, so the list keeps its place and height as answers change, and the button is disabled while any is unmet. A document that sets `"messages_after_a_press": true`, as *Whatever You Do* does, disables no button and lists nothing until a press is refused, then only the messages still unmet, so nobody is greeted with what they have not done yet; a hub side card, with nothing to press, lists nothing (ticket 83). Its wizard's answers save without saying "Saved". An unmet `links_issued` message is itself a link to where those links are issued: the coach page for a coach checklist, the contact list's page for a contact list, unless the block is in the same section, as on a side card. A `links_issued` message says its `min` as `{min}`, as *Whatever You Do*'s "Add at least {min} people." does, so the number is written once; the linter refuses a different number written into it. The clause types are:

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

A clause may only name a block whose answer it can read and, except for `has_answer` and `comparison_visited`, only one in its own section; the linter refuses both. `has_answer` may wait on another section's block ("the sort has been done"), which is how Section 1 waits on the Strengths evaluation, and `comparison_visited` on a visit to that sort's comparison; what another section's answer holds is for that section's own gate. The three entry clauses read a contact list, and later the timeline board (ticket 17). A new kind of clause is a code change, never an expression in the document (ADR 0003).

A `section_signpost` block leads to another section, named by `section`, with an optional `body`. It shows that section's title and status exactly as the hub does, and a locked section is named but not linked. With a `button_label`, such as Section 1's "Open the strengths evaluation →", a button leads there and the title is plain text. A `finished` wording, a `button_label` with an optional `body`, takes the place of the signpost's own once the linked section is complete, and its button then leads to the results of the sort in that section, if it holds one: Section 1's reads "View my results →", so a participant who has done the assessment is never sent back to its start. With `"holds_what_follows": true`, the blocks after it are held back until the linked section's gate passes, as beneath an unconfirmed scripture reading: they are not sent to the browser and will not accept an answer. The linked section need not be completed. The faithful port's Section 1 holds its reflection this way until the sort is in. The linter refuses a signpost that holds back its own section, which could never be finished. It takes no answer and puts no section in progress.

A `comparison_signpost` block is a card for the way to the comparison of the sort it names (`sort`), with its `title`, such as Section 2's "How others see you" above its reflection. It shows nothing until there is a result. Its button is the results page's "Compare with how others see you →", posting to the same address, so it warns before answer collection freezes exactly as that one does. Its status says how many of the minimum number of observers have answered while below it ("2 of 3 answered"), "Ready to view" at or above it, and "Viewed" once the participant has pressed it, or the results page's button, with the minimum in; "Viewed" stays if withdrawals later unfreeze collection. Opening the comparison by its address is not viewing it. The linter refuses a `comparison_signpost` naming anything but a sort. It takes no answer and puts no section in progress.

Pathway versions stored before ticket 75 hold the two signposts as `section_link` and `comparison_link`. A version is never edited, so its row keeps those names, and the engine reads them as the new ones each time it loads the version (`RENAMED_BLOCK_TYPES`); a document being loaded must use the new names, and the schema refuses the old.

A capture block answered on its page (a scripture reading, a long text, an agreement scale or a single select) may carry `after_comparison`, naming a `sort` and a `message`, as Section 2's reflection does. Until the participant has viewed that sort's comparison, as a `comparison_signpost`'s "Viewed" counts it, the block is drawn disabled with its message beside it and the server refuses an answer to it; once viewed it stays answerable, even if withdrawals later unfreeze collection. The hub's next step passes over a section whose only open work waits this way; while nothing else is open, it says the section's `next_step` `waiting` sentence, where `{section}` is what the hub calls the section ("Section 1") and `{minimum}` the pathway's minimum number of observer answers. The schema refuses `after_comparison` on any other block, and the linter one naming anything but a sort.

A section with `part_of` naming another section is a part of it, as *Whatever You Do*'s Strengths evaluation is a part of Section 1, where the original prototype keeps it. The hub and the sidebar list a part within its section's entry. A part has no completion of its own: it is complete once its gate passes, worked out from the answers rather than stored, so the hub, locks and links count it as complete as soon as the sort is in, and a completion posted for it is refused. A section is in progress once its part is begun, even with nothing of its own answered. A part opens only once the participant reaches its section's signpost to it, so the faithful port's Strengths assessment waits until Section 1's reading is confirmed, and *Whatever You Do*'s, behind passages with nothing to confirm, opens with Section 1; one whose section has no signpost to it opens with that section, and one whose section is outside the track by its own `requires`. Its page's "← Back", its results page and the end of its comparison lead to the section it is a part of. The linter refuses a `part_of` naming no section, the section itself, or a section that is itself a part, and a part with no gate, which would be complete before it was begun.

A section's `number`, such as `"01"`, is shown beside it in the hub's list; without one, none is. A section with a `side_card`, holding its `sentence`, is drawn as a card beside the hub's list, below it on a phone, with its title, that sentence and its status, and is not in the list; the sidebar lists the side cards after the sections, with their statuses, as it lists everything the hub lists, a comparison signpost's row among them, in the hub's order. The hub's header counts the track's numbered sections complete, out of how many there are, as an organisation's admins see it too: *Whatever You Do*'s reads "0 of 6 sections complete", leaving out its part, its side cards and Before we begin. A pathway that numbers no section, as the faithful port, counts every section the hub lists, parts and side cards among them. Like a part, a side card has no completion of its own: it is complete once it is open and its gate passes, as *Whatever You Do*'s are once the coach has a link and once three people have links (`links_issued`). Unlike a part's, that completion is stored the first time it is seen, so it stays complete when the links later expire or are revoked or people are taken off the list, and never locks again what it opened; completing or reopening one by hand is refused. A locked section's entry on the hub says what is left in the sections it still waits for, each by its `to_finish`, the phrase for what finishing it takes, as *Whatever You Do*'s Section 3 says "Opens once you've completed Section 1, sent a coach their link in *Walk with a coach* and added at least 3 people in *Five trusted voices*." In a phrase, `{title}` is the section's title, shown in italics, `{section}` what the hub calls it ("Section 1"), and `{min}` the minimum of the section's own `links_issued` clause, as in Five trusted voices' "added at least {min} people in {title}"; the linter refuses a `{min}` in a section without exactly one such clause, a number in the phrase other than that minimum (other numbers are spelt in words), and any other placeholder, such as a mistyped `{titel}`. A note names what is left in the order of the section's `requires`; sections next to each other there sharing a phrase are named together, as in "Opens once you've completed Sections 1, 2 and 3", never moved ahead of a section between them. Sections without one are named together as "finished" and their titles, as all of the faithful port's are: "Opens once you've finished *Before we begin*." Every section title a note names is in italics, a part's "Opens from *How you've been designed*." among them. The linter refuses a number or a side card on a part, and a side card on a section with parts.

A section may also carry `opens_when`, whose `clauses`, from the same set as a gate's, must all pass before it first opens, beside the sections it `requires` (ADR 0019). While one fails the section is locked and the hub's note under it gives that clause's message. Its opening is stored the first time, and from then on it stays open whatever happens to those clauses. While sections it requires are unfinished too, the note is `with_sections`, saying what is left in them where it says `{sections}`, as Section 4's "Opens once you've {sections}, and your coach has accepted."; without it, the note names only the sections. A `coach_accepted` clause names a coach checklist and passes once the coach chosen through it has accepted on their current link, even if that link has since expired; a decline, no link, a revoked or reissued link, or another coach chosen since, does not count. *Whatever You Do*'s Section 4 waits on its coach this way. An opening condition may name a block in any section, since nothing in its own is reachable before it opens; the linter refuses one naming no block, or a block its clause cannot read.

A section with `"wizard": true`, as *Whatever You Do*'s Before we begin is, is where the hub sends a participant who has not completed it, at the page they have reached. Until it is complete its pages are drawn without the header, the sidebar or any link to the hub, beside the section's photo; completing it leads to the hub, which from then on lists it, and it is reread as any other section. *Whatever You Do*'s has two pages, the reason and then the five opening ratings; its coach and contacts are the side cards Walk with a coach and Five trusted voices, last in the document so neither becomes the next step.

A wizard may also be `"once_only": true`, as *Whatever You Do*'s Before we begin is (the faithful port's is not). Once it is complete the participant never sees it again: it leaves the hub, the sidebar and the hub's count of sections, and so an organisation's admins' count too, and its pages, its answers (with or without JavaScript) and its completion all lead to the hub, changing nothing, so neither the reason nor the opening ratings can be seen or changed. The linter refuses `once_only` on a section that is not a wizard, since one might never be seen at all.

The hub's next step shows the section's `next_step` `heading` and `sentence` while that section is next, or, without them, its title and time estimate; a `next_step` may carry its `waiting` sentence alone, as *Whatever You Do*'s Section 2 does. The document's `photos`, keyed by section, name a file in `pathways/files` (such as `grass.jpg`) with its `credit`; the next step is drawn over the photo of the section it points at. A credit's `kind` is `required` (its licence asks for it), `courtesy` (its licence does not, as Unsplash's does not) or `none` (public domain, or the author's own); the first two carry the `text` the credits page lists. The credits page lists every required credit, the courtesy ones only while the document's `show_courtesy_credits` is on, and nothing for `none`. The linter refuses a photo named for no section, and a credit of any other kind.

A `scripture_reading` block shows its authored passages and a confirm control. The activity beneath it is decided by the server too: until the confirmation is saved, the blocks after it are not sent to the browser and will not accept an answer. A `scripture_passages` block shows passages, with its `heading` and `note`, the same way, with nothing to confirm: it takes no answer and holds nothing back, as *Whatever You Do*'s Section 1 "Scripture on gifts".

Every passage is from a translation the document declares under `translations`, keyed by its abbreviation, with its `name` and the `notice` its publisher asks for, word for word. The document's `translation` is the one a passage is from unless it names its own `translation`. The linter refuses a translation that is named but not declared, and a passage with no translation to fall back on. A passage from a translation other than the document's shows that translation's abbreviation beside its reference. Every declared notice is on the credits page, which every page links to. The homepage's verse (Colossians 3:23, NIV) belongs to no pathway, so the credits page carries its notice itself; a document declares only the translations its own passages use. The document's own translation's notice therefore begins "Unless otherwise indicated", and each other notice names the passages it covers ("marked NIV"). A passage's text is the translation's word for word: a cut is marked with an ellipsis (…), or, where a passage stops partway through its last verse, its reference may say so instead ("Psalm 37:3–7a"). The publishers' free allowance is 500 verses of each translation, quoting no complete book (the ESV: no more than half of any one book), with scripture under 25% of the work's text.

## Answers

Each answer saves by itself as the participant types or chooses, and only that answer is written. A block type is defined in one place, `engine/document/blocks.py`: its authored text, what it captures and whether an answer to it puts its section in progress all follow from that entry. Answers are checked on the server against their block, and a participant signing in anywhere sees them all. Whether a response is test data is recorded on the server (`Response.is_test_data`), never set by a browser.

A `long_text` block may carry a `placeholder`: ghost text in the empty box, such as the letter's "Dear me,". It is a hint only; the prompt stays the box's label, and the placeholder is never saved as the answer.

A `single_select` block is a drop-down of authored `options`, each an `id` and a `label`, and saves as soon as one is chosen. The answer is the option's `id`, so a label can be reworded without changing what earlier answers mean; the server refuses anything that is not one of the block's own options, and the linter refuses two options sharing an `id`. An empty choice always leads the list, showing the optional `placeholder` ("Select..."), so an unanswered select never looks answered; choosing it again takes the answer back, as emptying a text box does. Onboarding asks the reason for taking the course this way, and its gate requires it.

A `contact_list` block asks for people who know the participant, a first name and an email address per row. It opens with `needed` rows marked "Needed" and then `optional` rows marked "Optional" (none needed and five optional unless the author says), and once those are filled, one more row, up to 50 people. Each row is a form of its own: an empty row's "Add and get their link" adds that person and issues their observer's link in the same act, and a person's "Save" changes them alone, so nobody is listed without having had a link, and a page left open can never drop someone added since (ticket 51a). The server refuses a person without both a name and an email, or with an email address Django would not accept, and the page comes back as typed, the field at fault marked. These are other people's details, so they are kept as `Contact` records against the response, not among its answers. The gate and the section's status still read the list as the block's answer; the faithful port's onboarding gate uses `entry_count` with `allow_none`, so the list may be left empty for later, as the prototype's "I'll do this later →" allowed, but not started short. The faithful port marks the prototype's five as needed; *Whatever You Do* marks three needed and two optional, while its gate asks for two for now.

A `contact_list` block may carry a `more_note`, one sentence above "Add another person" saying more people can be added than its rows ask for, as *Whatever You Do*'s "Five is a good number, but you can add more." It is drawn only while the list offers "Add another person": not once it shows the most rows it may hold, nor while answer collection is frozen.

A `coach_checklist` block helps the participant choose a coach, as the content owner's coach-selection prototype does: why the choice matters, the candidate's first name, then the authored questions, each answered Yes, Not sure or No. The rule turning the answers into going ahead, a second thought or trying someone else is engine code (`engine/document/coach.py`). None of the answers is stored or logged: they are opinions about another person, including their faith, so they travel only in the form, screen to screen, and the outcome is worked out again from what was posted. Going ahead asks only for a tick, on the verdict card, that the participant has spoken to them; saving keeps only the name given at the start, as a `Contact` with the coach role and no email address (ADR 0022), makes the coach's link, and is refused past a stop. Once saved, the block shows the coach, with "Back to the hub", "Choose someone else" (the coach is kept until another is saved, which the intro says, with "Keep Sam" to go back to them) and "Remove". It puts no section in progress, no gate may name it, and it can be left without choosing anyone.

Long-text answers are limited to 20,000 characters. The text box carries the same limit and says how much room is left near it. Line breaks are stored as `\n`, although forms send them as `\r\n`. This is the one change made to a participant's text on input, and it keeps the server's count the same as the browser's.

The long-text, single-select and 1–10 scale forms also save without JavaScript, through a Save button that is hidden once JavaScript loads. This was added in passing during ticket 03 and is not a standard: later blocks, especially the interactive ones such as the sort and the timeline, need not work without JavaScript, and this fallback may be removed.

## Scoring and results

A `sort_assessment` block's answer is the whole sort, sent as JSON: every item of the pathway's instrument, each with the `bucket` it was placed in and a whole `value` from 0 to 100. The server checks it against that pathway version's own items and buckets. The linter refuses a pathway with a sort but no buckets, items, frameworks or scoring method, and a sort whose section's gate has no `has_answer` clause for it. Until the sort is in, its section offers no way to complete it, as in the prototype.

A sort is scored once, when it is submitted, by the method the document names in `measurement.scoring` (ADR 0003). There is one method, `compositional_share`, the prototype's: each construct's share of the grand total, rounded half up as JavaScript rounds, ranked with ties kept in declaration order. A method is frozen once any response has been scored with it, so a change in behaviour is a new name. The result is stored with the answer and never recomputed, and a second sort is refused because retake does not exist yet.

The sort itself is a JavaScript widget, `frontend/src/sort.js`: one card at a time into the buckets, with undo, then a slider per item seeded from its bucket. It sends the whole sort once, and the server answers by sending the browser to the results. Its own wording around the items (headings, the instruction, the slider ends, the submit button) is the document's `presentation.sort_wording`, keyed by role like any text, with the engine's own (`SORT_WORDING` in `engine/document/blocks.py`) for any field left out. For an observer, `{name}` in it, and in the items and bucket labels, is the participant's name.

The results page, `/results/<block_id>/`, shows the stored result in the wording of the document's `presentation`: a heading and subtitle per framework, a description, persona and tone per construct, the disclaimer, and a title in which `{name}` is the participant's username. Colours stay in the stylesheet: a construct names a tone for its item scores, and each bar and its standing take the standing's colour, by its band's place in `presentation.standing`, so a colour never disagrees with the word beside it.

The golden fixtures in `tests/core/golden/` are the prototype's own scoring output. To add a case, edit `prototype_scoring.mjs` and run `node tests/core/golden/prototype_scoring.mjs` from the repository root.

## Inviting observers

The contact list's own page (in *Whatever You Do*, Five trusted voices', which the hub's card leads to; `/invitations/` leads there too) lists the people on it, each with a link of their own to act as an observer (ADR 0005). Adding a person issues their link; the participant copies it and sends it themselves; nothing is emailed. The hub's Five trusted voices card says where things stand, and counts people with a working link as invited and observer evaluations sent as answered, naming nobody. A link carries a token of 32 random bytes, of which only a SHA-256 hash is kept as an `Invitation`, so the link is shown only in the page that comes back after issuing it; a lost link is reissued ("Make a new link"). Issuing redirects back to that page, so a reload never issues again, and the link travels there in a signed, HttpOnly cookie that lasts a minute and is deleted as it is read, never in the address or the session. With JavaScript, htmx follows the same redirect and swaps in that person's row alone, so the page stays put. Each contact has at most one live link: reissuing stops the previous one, and revoking deletes it. A link works for the document's `observers.link_lifetime_days` (30 when left out), and a wrong, expired or revoked link at `/observe/<token>/` gets one refusal, the same for all three, naming nobody. The coach's link is ticket 13c's.

A live link opens the privacy notice (the document's `observers.privacy_notice`, in the observer's wording, or, for a document without one, a stand-in marked as a draft, in `engine/document/observers.py`) and "I'm answering for …", which claims it: the invitation keeps the hash of a new secret of 32 random bytes, which goes to the observer in an `observer` cookie (HttpOnly, path `/observe/`) and once, as a link of their own, `/observe/<secret>/`. The participant's copy then says "already used" (410), so if they claimed it first, the observer notices and asks for a new one. `/observe/` reaches the observer's page by the cookie, which only the claim (a POST) sets, so no other site can plant one; the observer's pages are sent `no-store`. Reissuing replaces the invitation record, so nothing claimed through the old link carries over. Observers have no account; the participant's name is their username until accounts hold one.

The page also shows the pathway's contact list, so a participant who skipped it in onboarding can add people there. Each row of a contact list sends back its contact's id, so a save edits that person in place and their link keeps working; an id that is not one of this list's own is taken as a new person, and someone taken off the list is deleted with their link.

An observer's answers are kept as an `ObserverResponse` (an observer evaluation and written answers), attached to the participant's response and never to a contact or invitation. Only submitted ones reach the observer average.

The observer's page runs the same sort widget in observer wording. It sends the observer evaluation once, to `/observe/assessment/` by the cookie or to `/observe/<secret>/assessment/` from their own link; the participant's copy of the link is refused there as any wrong link is. The `ObserverResponse` keeps a hash of the claimed secret, prefixed so it never equals the invitation's, so it outlives the link and only the secret finds it again (ADR 0007, ADR 0009). A second send from the same secret is refused (409), and after sending the page only says thank you.

To show the comparison without three real observers, `python manage.py seed_observers --observers 3` creates a fake participant, `seed-participant-<n>@example.com` with the password `information.` (`--password` sets another) and consent already given, with a strengths evaluation and self-result of their own and that many submitted test observers, their values the same on every run. Everything it creates is marked as test data on the server; it needs a published pathway with an assessment block.

To build on organisations without walking twelve pathways, `python manage.py seed_cohort` creates Example Church with an Autumn cohort of twelve fake members and an admin holding `manage` on Example Church, and prints the admin's email, the password `information.` and the cohort's join link. Of the members, three have not started, five are part-way and four have finished, with self-results, closing ratings and observer answers sent through real invitations; one part-way member has withdrawn consent. Every account is at `example.com` and everything it creates is marked as test data on the server. It runs only with `DEBUG` on, needs a published pathway, and a second run says Example Church already exists and adds nothing.

To try each way through the tie-break without sorting by hand, `python manage.py seed_tie_break --profile <profile> --answers <answers>` creates a fake participant, `seed-tie-break-<n>@example.com` with the password `information.` (`--password` sets another), signed up, consented and past Before we begin, with a sort already sent from that starting profile: `tied-apest` (tied on APEST(d) only), `tied-pep` (tied on PEP only), `tied-both` (tied on both, not flat; the pairs alternate), `just-leading` (one role just Leading, the rest Present or Strong) or `flat` (flat on both: a generalist with no pairs). `--answers` says how the pairs are to be answered: `leader` (the leader each time: separated, the same one on top), `behind` (the one behind each time: separated, a new one on top), `one-each-way` (genuinely balanced; with `just-leading`, a generalist after the pairs), `skip`, or, with `tied-both` only, `separate-apest-skip-pep` or `separate-pep-skip-apest`. `flat` takes no `--answers`, and every other profile needs it; a pair that does not fit stops with an error saying why. It prints a sign-in link that opens the first pair, which statement to choose or skip for each pair, and what the results should then show, worked out from the two choices through the real scoring and re-weighting, and stops with an error if the published pathway no longer gives them. Its response is marked as test data. It runs only with `DEBUG` on or `ANVILLE_DEMO_NOTICE` set, as on staging, and never touches an existing participant; `docs/manual-checks.md` says which pair suits each tie-break check.

## Settings for a deployed environment

Everything a deployed copy needs is read from the environment, so one build serves every deployment (ADR 0002). [docs/server-approach.md](docs/server-approach.md) describes how a deployment is run. Development needs none of these: left unset, each keeps the behaviour described above.

| Variable | Unset | Set |
|---|---|---|
| `DJANGO_HTTPS` | No forwarded header is trusted and plain HTTP is served | `true` behind a proxy that ends TLS: its `X-Forwarded-Proto` is trusted, plain HTTP is redirected to HTTPS, and the session, CSRF and observer cookies are marked Secure. Never set it without such a proxy in front, or anyone can claim to be on HTTPS |
| `DJANGO_HSTS_SECONDS` | No `Strict-Transport-Security` header | How long browsers should refuse plain HTTP. Only read when `DJANGO_HTTPS` is on |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | None | Further origins allowed to post forms, comma-separated. Not needed when the proxy passes the `Host` header on |
| `DJANGO_SECRET_KEY_FALLBACKS` | Only `DJANGO_SECRET_KEY` is accepted | Old keys being rotated out, comma-separated: what they signed (sessions, signed cookies) is still accepted, but nothing new is signed with them. [deploy/README.md](deploy/README.md) gives the steps |
| `DATABASE_CONN_MAX_AGE` | A database connection per request | Seconds to keep a connection for reuse |
| `CACHE_URL` | Each process keeps its own cache | The cache every worker shares, where allauth counts sign-in and sign-up attempts. The chart sets `dbcache://anville_cache`, Django's database cache; `python manage.py createcachetable` makes its table, and the chart runs it after the migration |
| `EMAIL_URL` | Email is fake: each message is printed in the server's output and nothing is delivered | The provider, as `smtp+tls://key:secret@host:587` |
| `DEFAULT_FROM_EMAIL` | `webmaster@localhost` | The address messages come from |
| `SERVER_EMAIL` | The same as `DEFAULT_FROM_EMAIL` | The address Django's own messages come from, such as errors sent to `ADMINS`. Django's own default, `root@localhost`, is refused by providers. The chart sets it from `email.from` |
| `ANVILLE_SITE_URL` | `http://localhost:8000` | Where the site is reached, for the links in email sent with no request behind it: the observers' reminders. The chart sets it from `hostname` |
| `ANVILLE_EMAIL_DISCLAIMER` | Messages go as written | For a test system that can reach real mailboxes: every message has `[TEST]` put before its subject and this text at the top of its body, plain and HTML alike. The chart sets it on every staging environment |
| `ANVILLE_DEMO_NOTICE` | Nothing is said | For a demo deployment: this text is shown on the homepage, the account pages (sign up, sign in), the hub and the pages observers' and coaches' links lead to, saying it is a demo; every other page shows a short fixed line saying the same. The chart sets it on every staging environment |
| `ANVILLE_COMMIT` | `unknown` | The commit the code was built from. The image sets it |

`/healthz` answers `{"status": "ok", "commit": "…"}` when the database can be reached, and 503 when it cannot. It still wants a `Host` header that `DJANGO_ALLOWED_HOSTS` lists.

With `DJANGO_DEBUG` off, errors are printed to the server's output with any observer's or coach's link redacted, since whoever holds such a link can answer as them. The visitor sees Anville's own page for not found, server error, forbidden and bad request (`engine/templates/404.html` and its neighbours), which names nothing of the address asked for.

The admin's sign-in at `/admin/` refuses repeated wrong passwords as the site's sign-in does: five for one account in five minutes, or ten from one address in a minute.

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
