# 47a: Deployment hardening: the admin's sign-in, error pages and a shared cache

**What to build:** Changes found by going through Django's deployment checklist (https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) against the staging set-up of ticket 26: the points the deployment check does not catch. Split from ticket 47 on 14 Oct; 47b holds the rest.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 2b (12–16 Oct); before any real participant data

**Spec:** Implementation Decisions; Delivery and hosting

- [ ] **The admin's sign-in is rate-limited** as sign-in is: repeated wrong passwords at the admin are refused as they are at sign-in
- [ ] **Error pages are Anville's own,** in the site's style, for not found, server error, forbidden and bad request, in place of Django's bare pages. The server error page needs no context and no database, since it is shown when something has failed. Each says nothing of the request, and nothing that names a link's token
- [ ] **The cache is shared by every worker,** so sign-in and sign-up limits count across all of them, without a new service. Development and tests may keep a per-process cache
- [ ] The deployment instructions, the README's settings for a deployed environment and the server approach describe whatever is added

**Context**

- The admin is public at `/admin/`, and allauth's limits cover only allauth's own sign-in. One way: send the admin's login through allauth's (`admin.site.login = login_required(admin.site.login)`, with `LOGIN_URL` at allauth's sign-in). Optionally, the admin's path comes from the environment, so it is not at the address every scanner tries
- Error pages: `404.html`, `500.html`, `403.html` and `400.html` in the root template directory; consider `403_csrf.html` too, for a form sent after its page went stale. Tests render each with `DEBUG` off
- Cache: Django's default is per process, so with two gunicorn workers allauth's limits are counted separately in each and are looser than configured (`docs/server-approach.md`, section 3, already notes this). Django's database cache needs no new service: `createcachetable` runs where migrations run (the chart's init container, and the README's first-time set-up). Choose it from the environment so development can keep the local-memory cache
- The docs are `deploy/README.md`, the README's "Settings for a deployed environment" and `docs/server-approach.md`, sections 3, 5 and 11
- `manage.py check --deploy` with staging's settings reports only the two HSTS warnings. Both are harmless for `anville.vabl.dev`, since `.dev` is already preloaded; for `whateveryoudo.org` neither should be turned on until its subdomains are known. Decide them, and silence the warnings with the reason, when production is set up
- Not in this ticket: running `check --deploy` in CI with staging's settings, failing on warnings
- Already met, checked against the checklist: secret key, debug and allowed hosts from the environment; Traefik routes only the environment's hostname to Django; persistent database connections; the database reachable only from the environment's own pods, and backed up; static files through WhiteNoise; HTTPS enforced with Secure cookies and HSTS; the cached template loader (automatic with `DEBUG` off); logging of errors, with link tokens redacted; no uploaded media
- `ADMINS` stays unset on purpose: error emails would carry request data, which may be personal. Alerting on errors is a later choice, and a hosted error tracker would be another processor
