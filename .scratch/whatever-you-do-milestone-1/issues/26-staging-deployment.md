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
- [ ] The instance holds fake data only, using reserved example domains; nothing real is ever loaded. Since sign-up is open (ticket 37), sign-up and the homepage say plainly that this is a demo, that visitors should use made-up details, and that data may be wiped
- [ ] A short runbook records how the instance was stood up, so another deployment can be created the same way (ADR 0002)
- [ ] Email on the instance starts as fake: nothing is delivered, and the operator can read what would have been sent
- [ ] Later (part 2, below): the instance sends actual email from a temporary staging domain, so coach and observer links can be emailed on staging, and every message carries a disclaimer that it comes from a test system not intended for production use; a lasting email set-up for the real service is separate (2 Oct demo)
- [ ] A smoke test passes on the deployed instance: sign up (with the enrolment code if the deployment turns it on), log in, complete a section, resume
- [ ] Open, and not decided by this ticket: who the controller is, retention and the data protection impact assessment (see spec Further Notes). Confirm the arrangement works for everyone involved before any real participant is added

**Carried from 13b**

- [ ] Behind the TLS proxy, set `SECURE_PROXY_SSL_HEADER` so the observer cookie is marked Secure
- [ ] Observers' links carry their token or secret in the path: keep them out of the web server's access logs

**Carried from 37**

- [ ] The enrolment code is required unless the environment turns it off: staging's environment and the runbook turn it off, or nobody can sign up

**Carried from 32a**

- [ ] The deployment builds the frontend (`npm run build` in `frontend/`) before collecting static files: the homepage's forest video and its still frame reach the served files only through that build

**Carried from 03**

- [ ] Password reset stays hidden and refused on staging until ticket 28a, even once staging sends email; the runbook says how the operator resets a password (`manage.py changepassword`). Re-enabling reset is ticket 28a

**Steps**

In order. Section numbers are those of docs/server-approach.md, where the detail and the reasons are. Steps marked *human* need an account, a credential or a console; the rest can be built and reviewed in the repository.

1. **Make the application deployable** (section 3). gunicorn, WhiteNoise and `STATIC_ROOT`, `/healthz` reporting the commit, proxy and cookie settings from the environment, `EMAIL_URL` and `DEFAULT_FROM_EMAIL` (unset, so email is fake), `CONN_MAX_AGE`. Both items carried from 13b are settled here. Everything keeps its present behaviour when the new variables are unset, and `.env.example` and the README gain the new variables.
2. **The image** (sections 3 and 12). The `Dockerfile`, and the optional `app` profile in `compose.yaml`. Check the image locally against the compose database before anything is pushed.
3. **Build workflow** (section 4). `build.yml`: tests, then one amd64 image to GitHub Container Registry.
4. *Human.* **Push a first image and make the package public** (section 4).
5. *Human.* **Hetzner** (section 9). A project in an EU region, an API token from it in an `hcloud` context named after the project, an SSH key for the interactive account and one for deploys, and a Storage Box with a sub-account for this environment (section 7).
6. **Host provisioning** (section 9). `cloud-init.yaml.template` and `hcloud-create.sh`, with the Hetzner project, the host's canonical name and the tier as parameters.
7. *Human.* **Create `anville-staging-01.vabl.dev`** with the script, in the Anville project. Make the A record for that name in Cloudflare by hand, DNS-only, with the address the script prints. Confirm k3s is up with both node labels, and that 6443 is not reachable from outside.
8. *Human.* **DNS** (section 10). A CNAME from `anville.vabl.dev` to `anville-staging-01.vabl.dev` in Cloudflare, DNS-only, and no AAAA record for either: the host serves over IPv4 only for now. It must resolve before the first deploy.
9. **The charts** (section 5). `anville-bootstrap` and `anville`, with in-cluster PostgreSQL and the backup CronJob; `helm lint` and `helm template` run in the build workflow.
10. **The environment** (section 6). `deploy/environments/whatever-you-do-staging/` with its `values.yaml` and `secrets.example.yaml`: staging tier, backup level A, the `letsencrypt-prod` issuer from the first deploy, since `.dev` is HTTPS-only in browsers (section 10).
11. *Human.* **GitHub Environment** `whatever-you-do-staging` with the secrets in section 6's table, as `deploy/environments/whatever-you-do-staging/secrets.example.yaml` lists them. Generate a fresh secret key, enrolment code and database password; none is reused from a development `.env`.
12. **Deploy workflow** (section 8). `deploy.yml`, ending with the `/healthz` version assertion.
12a. **The demo notice** (carried into this ticket with ticket 37). Sign-up is open on staging, so sign-up and the homepage say plainly that this is a demo, to use made-up details, and that data may be wiped. Turned on from the environment, as the email disclaimer is, so the chart can set it for every staging-tier environment and production never shows it.
13. *Human.* **First deploy.** Run the workflow. Through the tunnel, create the operator's superuser, and optionally run `seed_observers`. Then publish `pathways/whatever-you-do.json` with the `publish-pathway` workflow. The deploy itself never loads a pathway (section 8).
14. *Human.* **Fake email** (section 11). With no `EMAIL_URL` set, run `manage.py sendtestemail` and find the message in the pod's log, marked `[TEST]` and opening with the disclaimer. Nothing is delivered.
15. *Human.* **Backup and restore** (section 7). Confirm a nightly dump has reached the Storage Box, then restore it into a scratch namespace on `anville-staging-01` and check the restored data.
16. *Human.* **Smoke test** on `https://anville.vabl.dev`: from the homepage, sign up (no enrolment code: staging turns it off), log in, complete a section, resume. Also confirm the demo notice shows on the homepage and the sign-up page, the observer cookie is marked Secure, and that neither Traefik nor gunicorn is logging request paths.
17. **Runbook.** A short record of steps 4 to 16 as actually performed, with the commands used and anything that differed from docs/server-approach.md, plus how the operator resets a password and reads fake email. Correct that document where it turned out wrong.

Steps 1 to 3, 6, 9, 10, 12 and 12a have no dependency on the human steps and can be done first, or alongside them.

**Progress.** Steps 1, 2, 3, 6, 9, 10, 12, 12a and 18 are built, on the branch `26-staging-deployment`, and 12a too. The items carried from 37 and 32a are met in the repository: `whatever-you-do-staging` turns the enrolment code off, and the image builds the frontend, the homepage's video included, before gathering the static files. None has met a real host, registry or Docker build yet: [deploy/README.md](../../../deploy/README.md) lists what each was tested against and what only the human steps can prove, and says how to do each of them. Every remaining step is a human one, then the runbook (17).

**Part 2: actual email, with a disclaimer**

Not needed for 9 Oct. It is kept in this ticket because tickets 28a and 43 wait on it for email delivery on staging; split it out if that is tidier.

18. **The disclaimer** (section 11). `ANVILLE_EMAIL_DISCLAIMER`, applied to the subject and body of every outgoing message by a wrapping email backend, with tests; the chart sets it for every staging-tier environment.
19. *Human.* **Mailjet.** A subaccount API key for this environment and the sending domain `mail.anville.vabl.dev`, validated with records in Cloudflare (`anville.vabl.dev` is a CNAME, so cannot hold the SPF record). `email.from` is already set. deploy/README.md, "Set up email (Mailjet)", gives the steps.
20. *Human.* **Switch over.** Add `EMAIL_URL` to the GitHub Environment, redeploy, and run `manage.py sendtestemail` to a real mailbox. Check that the message arrives with the disclaimer, and that password reset is still refused.

**Context**

- Not in this ticket: a production host or environment, Ubicloud, point-in-time recovery, automatic deploys to staging, and a second environment. docs/server-approach.md covers each; none is needed for one staging environment
- Staging's accounts use reserved example domains, which cannot receive mail. Once part 2 is done, actual email goes only to the real addresses of people who know they are testing. Those addresses are then real data on staging, the one exception to "fake data only", to be kept small and agreed
- Unverified assumptions in docs/server-approach.md that this ticket will test first: that a new package on GitHub Container Registry starts private, that Hetzner leaves outbound port 587 open, and that Mailjet allows one API key per environment
