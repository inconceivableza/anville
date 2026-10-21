# 63: Production hardening

**What to build:** What ticket 47a left open for a production deployment: HSTS settled for production's domain, Django's deployment check run in CI, the admin's path taken from the environment, and error reports to the operator. Staging works without them; production should not.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3 or later; parked until a production environment is set up

**Spec:** Delivery and hosting

- [ ] HSTS's subdomains and preload are decided for production's domain once its subdomains are known, and any deployment-check warning left is silenced with the reason
- [ ] CI runs Django's deployment check with a deployment's settings, and fails on a warning
- [ ] The admin's path comes from the environment, and is `/admin/` when unset
- [ ] The operator learns of server errors without the report carrying request data, or `ADMINS` stays unset with the reason recorded in the spec

**Context**

- Listed in the sprint 2b end report and the spec's Delivery and hosting, 19 Oct
- Staging's `anville.vabl.dev` needs no HSTS change: `.dev` is preloaded

**Carried from 26**

- [ ] Every management command in the image warns `staticfiles.W004`: `STATICFILES_DIRS` names `frontend/img`, which the image does not hold. Nothing is missing, since the stylesheet's images reach the served files through the frontend build, but a check that fails on a warning would fail on this one. Drop the entry, or keep it only where the directory exists
