# 26: Staging deployment

**What to build:** A private staging instance for the 9 Oct demo and the content owner's own use, at `https://anville.vabl.dev`: Hetzner in an EU region, holding fake data only. It is the first environment, `whatever-you-do-staging`, of the approach in [docs/server-approach.md](../../../docs/server-approach.md), which this ticket follows and does not repeat. Needs a human for account and access steps (the wizard skill fits).

**Blocked by:** 05 (Slice 1 content: baseline and calling-statement section)

**Status:** ready-for-human

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

This can start as soon as ticket 05 lands, so hosting surprises surface early.

- [ ] A Hetzner project exists in an EU region and holds the staging host. One operator holds the project, the repository and its secrets for now; an account owned by the content owner with the developer deploying into it is deferred, and not handled by this ticket
- [ ] The application runs there behind HTTPS at `anville.vabl.dev`, configured entirely from the environment, and deployed only by the deploy workflow
- [ ] The database has backups and a restore has been tried once
- [ ] The instance holds fake data only, using reserved example domains; nothing real is ever loaded
- [ ] A short runbook records how the instance was stood up, so another deployment can be created the same way (ADR 0002)
- [ ] The instance sends email from a temporary staging domain, so coach and observer links can be emailed on staging; a lasting email set-up for the real service is separate (2 Oct demo)
- [ ] A smoke test passes on the deployed instance: sign up with the enrolment code, log in, complete a section, resume
- [ ] Open, and not decided by this ticket: who the controller is, retention and the data protection impact assessment (see spec Further Notes). Confirm the arrangement works for everyone involved before any real participant is added

**Carried from 13b**

- [ ] Behind the TLS proxy, set `SECURE_PROXY_SSL_HEADER` so the observer cookie is marked Secure
- [ ] Observers' links carry their token or secret in the path: keep them out of the web server's access logs

**Carried from 03**

- [ ] Password reset stays hidden and refused on staging until ticket 28a, even once staging sends email; the runbook says how the operator resets a password (`manage.py changepassword`). Re-enabling reset is ticket 28a

**Steps**

In order. Section numbers are those of docs/server-approach.md, where the detail and the reasons are. Steps marked *human* need an account, a credential or a console; the rest can be built and reviewed in the repository.

1. **Make the application deployable** (section 3). gunicorn, WhiteNoise and `STATIC_ROOT`, `/healthz` reporting the commit, proxy and cookie settings from the environment, `EMAIL_URL` and `DEFAULT_FROM_EMAIL`, `CONN_MAX_AGE`. Both items carried from 13b are settled here. Everything keeps its present behaviour when the new variables are unset, and `.env.example` and the README gain the new variables.
2. **The image** (sections 3 and 12). The `Dockerfile`, and the optional `app` profile in `compose.yaml`. Check the image locally against the compose database before anything is pushed.
3. **Build workflow** (section 4). `build.yml`: tests, then one amd64 image to GitHub Container Registry.
4. *Human.* **Push a first image and make the package public** (section 4).
5. *Human.* **Hetzner** (section 9). A project in an EU region, an API token for `hcloud`, an SSH key for the interactive account and one for deploys, and a Storage Box with a sub-account for this environment (section 7).
6. **Host provisioning** (section 9). `cloud-init.yaml.template` and `hcloud-create.sh`, with the tier as a parameter.
7. *Human.* **Create `staging-1`** with the script, and confirm k3s is up and 6443 is not reachable from outside.
8. *Human.* **DNS** (section 10). A and AAAA records for `anville.vabl.dev` in Cloudflare, DNS-only, pointing at the host. They must resolve before the first deploy.
9. **The charts** (section 5). `anville-bootstrap` and `anville`, with in-cluster PostgreSQL and the backup CronJob; `helm lint` and `helm template` run in the build workflow.
10. **The environment** (section 6). `deploy/environments/whatever-you-do-staging/` with its `values.yaml` and `secrets.example.yaml`: staging tier, backup level A, the `letsencrypt-prod` issuer from the first deploy, since `.dev` is HTTPS-only in browsers (section 10).
11. *Human.* **GitHub Environment** `whatever-you-do-staging` with the variable and secrets in section 6's table. Generate a fresh secret key, enrolment code and database password; none is reused from a development `.env`.
12. **Deploy workflow** (section 8). `deploy.yml`, ending with the `/healthz` version assertion.
13. *Human.* **First deploy.** Run the workflow, then through the tunnel: create the operator's superuser, load `pathways/whatever-you-do.json`, and optionally `seed_observers`. The deploy itself never loads a pathway (section 8).
14. *Human.* **Email** (section 11). A Mailjet API key for this environment, a sending address at `anville.vabl.dev` validated with records in Cloudflare, `EMAIL_URL` added to the GitHub Environment, a redeploy, and `manage.py sendtestemail` to a real mailbox. Check that password reset is still refused afterwards.
15. *Human.* **Backup and restore** (section 7). Confirm a nightly dump has reached the Storage Box, then restore it into a scratch namespace on `staging-1` and check the restored data.
16. *Human.* **Smoke test** on `https://anville.vabl.dev`: sign up with the enrolment code, log in, complete a section, resume. Also confirm the observer cookie is marked Secure, and that neither Traefik nor gunicorn is logging request paths.
17. **Runbook.** A short record of steps 4 to 16 as actually performed, with the commands used and anything that differed from docs/server-approach.md, plus how the operator resets a password. Correct that document where it turned out wrong.

Steps 1 to 3, 6, 9, 10 and 12 have no dependency on the human steps and can be done first, or alongside them. Step 14 can slip behind the rest without holding up the demo of anything that does not send email.

**Context**

- Not in this ticket: a production host or environment, Ubicloud, point-in-time recovery, automatic deploys to staging, and a second environment. docs/server-approach.md covers each; none is needed for one staging environment
- Staging's accounts use reserved example domains, which cannot receive mail. A coach's or observer's link that is to be emailed on staging goes to a real test mailbox the operator controls, and that is the only real address staging holds
- Unverified assumptions in docs/server-approach.md that this ticket will test first: that a new package on GitHub Container Registry starts private, that Hetzner leaves outbound port 587 open, and that Mailjet allows one API key per environment
