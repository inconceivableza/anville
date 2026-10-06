# 44: Deployment hardening from Django's checklist

**What to build:** Changes found by going through Django's deployment checklist (https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) against the staging set-up of ticket 26. `manage.py check --deploy` with staging's settings reports only the two HSTS warnings (see Context). These are the checklist's points that the check does not catch.

**Blocked by:** None (can start immediately). Item 4 must land before part 2 of ticket 26 (actual email on staging)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct); before any real participant data

**Spec:** Implementation Decisions; docs/server-approach.md, sections 3, 5 and 11

- [ ] **The admin's sign-in is rate-limited.** `/admin/` is public, and its login has no limit on attempts: allauth's limits cover only allauth's own sign-in. Send the admin's login through allauth's, so the same limits apply (`admin.site.login = login_required(admin.site.login)`, with `LOGIN_URL` at allauth's sign-in), or limit it another way. A journey test shows that repeated wrong passwords at the admin are refused as they are at sign-in. Optionally, the admin's path comes from the environment, so it is not at the address every scanner tries
- [ ] **Error pages are Anville's own.** `404.html`, `500.html`, `403.html` and `400.html` in the root template directory, in the site's style, in place of Django's bare pages ("Server Error (500)"). `500.html` needs no context and no database, since it is shown when something has failed. Consider `403_csrf.html` too, for a form sent after its page went stale. Each says nothing of the request, and nothing that names a link's token. Tests render each with `DEBUG` off
- [ ] **The cache is shared by every worker.** Django's default cache is per process, so with two gunicorn workers allauth's sign-in and sign-up limits are counted separately in each, and are looser than configured (docs/server-approach.md, section 3, already notes this). Use Django's database cache: `createcachetable` runs where migrations run (the chart's init container, and the README's first-time set-up), so no new service is needed. Development and tests may keep the local-memory cache if the database cache is chosen from the environment
- [ ] **A real environment names its sending address.** The chart sets `DEFAULT_FROM_EMAIL` only from `email.from`, which `whatever-you-do-staging` leaves empty, so mail would come from Django's `webmaster@localhost`, which Mailjet refuses. `deploy.sh` refuses an environment that has `EMAIL_URL` but no `email.from`. Fake email (no `EMAIL_URL`) needs neither
- [ ] **`SERVER_EMAIL` is set too.** It is the address Django's own messages come from, by default `root@localhost`, which providers also refuse. Read from the environment like `DEFAULT_FROM_EMAIL`, defaulting to it, and set by the chart from the same `email.from`. Nothing sends such messages while `ADMINS` is unset, but a provider must never be handed an address it will refuse
- [ ] **The secret key can be rotated.** `SECRET_KEY_FALLBACKS` from the environment (`DJANGO_SECRET_KEY_FALLBACKS`, comma-separated, empty by default), so a new `DJANGO_SECRET_KEY` can be deployed without signing everyone out or breaking signed cookies such as the one that shows a link just issued. The chart passes it from an optional secret; `deploy/README.md` gives the steps (move the old key to the fallbacks, deploy, and remove it once sessions signed with it have expired, two weeks by default) and the checklist's warning to remove old keys promptly
- [ ] **Expired sessions are cleared regularly.** Sessions are stored in the database and nothing removes the expired ones, so they accumulate, each tied to an account. A nightly CronJob in the chart runs `manage.py clearsessions`, in the application's image, beside the backup and outside its hour. With the database cache above, cached database sessions (`cached_db`) are worth considering too, as the checklist suggests
- [ ] `deploy/README.md`, the README's "Settings for a deployed environment" and docs/server-approach.md describe whatever is added

**Context**

- From the same checklist, not in this ticket: running `check --deploy` in CI with staging's settings, failing on warnings
- `check --deploy` warns that `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` are off. For `anville.vabl.dev` both are harmless, since `.dev` is already preloaded; for `whateveryoudo.org` neither should be turned on until its subdomains are known. Decide them, and silence the warnings with the reason, when production is set up
- Already met, checked against the checklist: secret key, debug and allowed hosts from the environment; Traefik routes only the environment's hostname to Django; persistent database connections; the database reachable only from the environment's own pods, and backed up; static files through WhiteNoise; HTTPS enforced with Secure cookies and HSTS; the cached template loader (automatic with `DEBUG` off); logging of errors, with link tokens redacted; no uploaded media
- `ADMINS` stays unset on purpose: error emails would carry request data, which may be personal. Alerting on errors is a later choice, and a hosted error tracker would be another processor
