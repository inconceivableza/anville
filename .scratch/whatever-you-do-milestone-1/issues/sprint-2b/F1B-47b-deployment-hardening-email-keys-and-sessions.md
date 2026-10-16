# 47b: Deployment hardening: Django's sending address, key rotation and clearing sessions

**What to build:** The rest of the changes from Django's deployment checklist (https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) against the staging set-up of ticket 26. Split from ticket 47 on 14 Oct; 47a holds the admin's sign-in, error pages and the shared cache.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 2b (12–16 Oct); before any real participant data

**Spec:** Implementation Decisions; Delivery and hosting

- [x] **A real environment names its sending address.** Done: `whatever-you-do-staging` sends from `noreply@mail.anville.vabl.dev`, and the deploy refuses an environment that has real email but no sending address
- [x] **Django's own messages have a sending address too,** taken from the environment and defaulting to the one above, so a provider is never handed an address it will refuse
- [x] **The secret key can be rotated** without signing everyone out or breaking signed cookies such as the one that shows a link just issued: old keys stay valid as fallbacks until removed, and the deployment instructions give the steps
- [x] **Expired sessions are cleared every night,** in the application's image, beside the backup and outside its hour
- [x] The deployment instructions, the README's settings for a deployed environment and the server approach describe whatever is added

**Context**

- Sending address: `SERVER_EMAIL`, by default `root@localhost`, which providers refuse. Read it from the environment like `DEFAULT_FROM_EMAIL`, defaulting to it, and set it in the chart from the same `email.from`. Nothing sends such messages while `ADMINS` is unset
- Key rotation: `SECRET_KEY_FALLBACKS` from `DJANGO_SECRET_KEY_FALLBACKS` (comma-separated, empty by default), passed by the chart from an optional secret. The steps in `deploy/README.md`: move the old key to the fallbacks, deploy, and remove it once sessions signed with it have expired, two weeks by default; with the checklist's warning to remove old keys promptly
- Sessions are stored in the database and nothing removes the expired ones, so they accumulate, each tied to an account. A nightly CronJob in the chart runs `manage.py clearsessions`. Once 47a's database cache is in, cached database sessions (`cached_db`) are worth considering too, as the checklist suggests
- The docs are `deploy/README.md`, the README's "Settings for a deployed environment" and `docs/server-approach.md`, sections 3, 5 and 11
