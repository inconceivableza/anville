# Server deployment approach for Anville

> ✨ Drafted with AI assistance. Status: the approach ticket 26 follows, not a runbook. What it describes for the first staging environment is now built under `deploy/` and `.github/workflows/`, and has not yet met a real host: [deploy/README.md](../deploy/README.md) says how to do each thing and what has been tested. Production, Ubicloud and point-in-time recovery remain proposals.
> It adapts [livepace-server-approach.md](livepace-server-approach.md) to Anville, and reads best beside it: the section order is the same.
> Sizing and prices are in [infrastructure-sizing.md](infrastructure-sizing.md); ticket 26 is the first use of this.

## 1. The stack in one paragraph

Anville is built into **one Docker image** by a **GitHub Actions** build workflow and pushed to **GitHub Container Registry**, tagged with the commit SHA. A **Helm chart** describes one environment: the Django service, its PostgreSQL (or a pointer to a managed one), its ingress and its backup job. A separate **deploy workflow** resolves the image digest, opens an SSH tunnel to a single-node **k3s** host on **Hetzner Cloud**, applies that environment's secrets, and runs `helm upgrade --install` into that environment's namespace. k3s supplies **Traefik**; **cert-manager** issues TLS from Let's Encrypt. Each host is created once from a **cloud-init** template and never hand-edited afterwards. Development is unchanged: `docker compose` for PostgreSQL, Django on the developer's machine.

Two words are used precisely below:

- **Host**: one Hetzner Cloud server running k3s.
- **Environment**: one installed copy of Anville, with its own namespace, hostname, database, secrets and published pathway. It is what [ADR 0002](adr/0002-one-deployment-per-organisation.md) calls a deployment, at one tier (staging or production). A host carries one or more environments of the same tier.

Proposed layout:

```
Dockerfile
compose.yaml                          # development, as now
deploy/
  chart/anville/                      # the environment chart
  chart/anville-bootstrap/            # cert-manager and issuers, once per host
  environments/<environment>/
    values.yaml                       # the deltas only
    secrets.example.yaml              # the shape of the secrets, no values
  infra/
    cloud-init.yaml.template
    hcloud-create.sh                  # firewall + server, from the template
    install-k9s.sh                    # k9s for the operator, carried by the template
  resolve-image-digest.sh             # the four steps of a deploy, each a script
  tunnel.sh
  deploy.sh
  assert-version.sh
  publish-pathway.sh                  # a pathway document into one environment
  check.sh                            # shellcheck and helm over all of deploy/
  README.md                           # how to do each thing
.github/workflows/build.yml
.github/workflows/deploy.yml
.github/workflows/publish-pathway.yml
```

## 2. What carries over from LivePace, and what does not

| LivePace | Anville | Why |
|---|---|---|
| Several services, a build workflow each | One image, one build workflow | One Django service |
| Multi-arch build, merged manifest list | amd64 only, no merge job | Hetzner's x86 line is the cheaper one (sizing doc); nothing runs the image on ARM. Local builds on an ARM Mac are native and never pull this image |
| Push by digest, deploy by digest | Kept | The core of the approach |
| Docker Hub, with its own credentials | GitHub Container Registry | The workflow's own token pushes; no registry account to manage |
| Umbrella chart with subcharts | One flat chart, PostgreSQL as a conditional part of it | Two workloads do not need an umbrella |
| Separate bootstrap chart | Kept, installed once per host | Environments come and go without touching cert-manager |
| `deploy/<env>/values.yaml` overlays | Kept, one directory per environment | This is what makes many environments cheap |
| One fixed staging and one production | Any number of environments, each a namespace | The requirement here |
| GitHub Environment per tier | GitHub Environment per environment | Secrets are scoped the same way |
| SSH tunnel to a localhost-only k8s API | Kept | No public cluster API |
| cert-manager with Cloudflare DNS-01 | cert-manager with HTTP-01 by default | It works whoever hosts the DNS, which production's is not yet decided, and keeps a zone-editing token off the host. Cloudflare DNS-01 stays available for staging (section 10) |
| Keypair consistency assertion | A version assertion: `/healthz` must report the commit just deployed | Same idea, the check that fits this app |
| Four traceability scripts | Pod annotations plus `/healthz` | One image; a compare script is not needed |
| Firewall rules in the chart, synced to the host | Dropped. Hetzner Cloud Firewall and UFW, both fixed at 22, 80, 443 | No per-service ports that change |
| OCI A1 ARM node, `oci-create.sh` | Hetzner CX, `hcloud-create.sh` | The host provider |
| SQLite on a volume | PostgreSQL, in-cluster or managed | See section 7 |
| — | One PostgreSQL server per environment, in the environment's chart, not one per host in the bootstrap chart | Isolation, recovery and upgrades stay per environment, at the price of some memory per environment. Section 7 gives the reasons, and what sharing one server would take |
| Redis subchart, off | Not included | Add when a worker exists (email, PDF export) |

## 3. The image

One multi-stage `Dockerfile`:

1. `node:22-alpine`: `npm ci && npm run build` in `frontend/`, producing `frontend/dist` and its manifest.
2. `python:3.13-slim-trixie`: install `requirements.txt`, copy the code, `pathways/` and `frontend/dist`, run `collectstatic`, switch to a non-root user, and start gunicorn on 8000. It also carries Debian's PostgreSQL 17 client and OpenSSH client, so the nightly backup (section 7) runs in this same image, and the operator has `psql` and `pg_restore` in the pod.

The image is public, as the project is open source. So it must contain nothing that the repository does not already publish: no `.env`, no secrets at build time, and only the pathway documents that are in `pathways/`.

The application needs these changes first. They are step 1 of ticket 26, and the README's "Settings for a deployed environment" lists the variables:

- **A WSGI server.** `gunicorn` in `requirements.txt`. Access logging stays off, which also keeps observers' link tokens out of logs (ticket 26, carried from 13b). Traefik's access log is off by default in k3s and should stay off for the same reason.
- **Static files.** `STATIC_ROOT`, and WhiteNoise to serve it, so there is no second nginx container. Vite's hashed filenames suit WhiteNoise's far-future caching.
- **`/healthz`.** It answers 200 with the commit SHA, read from `ANVILLE_COMMIT`, which the image sets when it is built, and checks the database with one trivial query. The Kubernetes probes must send the environment's `Host` header, or Django refuses the pod-IP request with `DisallowedHost`.
- **Proxy and cookie settings from the environment.** One switch, `DJANGO_HTTPS`, sets `SECURE_PROXY_SSL_HEADER` (ticket 26), the redirect to HTTPS, and secure session and CSRF cookies; `DJANGO_HSTS_SECONDS` and `DJANGO_CSRF_TRUSTED_ORIGINS` sit beside it. All default to the safe development behaviour when unset.
- **Email from the environment.** `EMAIL_URL` and `DEFAULT_FROM_EMAIL`, read with django-environ, defaulting to the console backend, and `ANVILLE_EMAIL_DISCLAIMER`, which marks every outgoing message when set. See section 11.
- **Database connection reuse.** `CONN_MAX_AGE` from the environment, as `DATABASE_CONN_MAX_AGE`. It matters little in-cluster and a good deal with a managed database reached over TLS.

- **Errors in the log, without observers' or coaches' links.** With debug off Django logs nothing by default, so errors are sent to the server's output, with the token or secret of any observer's or coach's link redacted.

`config/settings.py` already takes the secret key, debug flag, allowed hosts, database URL and enrolment code from the environment, so one image serves every environment (ADR 0002).

One known limit to record, not fix now: Django's default cache is per process, so allauth's rate limits are counted per gunicorn worker.

## 4. Build workflow (`build.yml`)

- **Trigger:** push to `v*` tags, and `workflow_dispatch`. Other branches build without pushing container images.
- **Tests first:** `pytest` against a PostgreSQL 17 service container. A red test run builds nothing.
- **Build and push:** one amd64 image, tagged `:<git-sha>` and `:latest`, with the commit stamped in as `org.opencontainers.image.revision` and passed as a build argument for `/healthz`.
- **Registry:** GitHub Container Registry, as `ghcr.io/inconceivableza/anville`. The workflow pushes with its own `GITHUB_TOKEN` (`packages: write`), so there are no registry credentials to store for the build. The image carries `org.opencontainers.image.source`, which links the package to the repository.
- **The package is public.** k3s pulls it with no credentials, so there is no image-pull secret in any environment, and the deploy workflow resolves digests anonymously. A new package on GitHub Container Registry is expected to start private, so making it public is a one-time manual step after the first push; confirm this when it happens.

## 5. The chart

`deploy/chart/anville` renders one environment into one namespace:

- **Deployment** `anville`: one replica, `Recreate` strategy, resource requests and limits, liveness and readiness on `/healthz`.
- **Migrations** run as an init container (`manage.py migrate`) in that same pod. With one replica and `Recreate` there is exactly one migrator, it works the same for an in-cluster or a managed database, and a failed migration fails `helm --wait` and so the deploy. A pre-upgrade hook Job would not work on first install, because the in-cluster database does not exist yet when hooks run. Move to a Job if replicas ever exceed one.
- **Service** and **Ingress** (Traefik, TLS from cert-manager) for the environment's hostname.
- **PostgreSQL**, when `postgres.enabled`: a StatefulSet on the official `postgres:17` image, the same one `compose.yaml` uses, with a local-path volume and a cluster-internal Service. Never exposed outside the cluster, and a NetworkPolicy admits only this environment's own pods, since environments of one tier share a host.
- **Backup CronJob**, when `backup.enabled`: see section 7.
- **Secret references** only. The chart never contains a secret value. The deploy workflow applies one Secret per environment and passes a hash of it, so that changing a secret restarts the pods.

Base `values.yaml` ships safe defaults: no hostname, which means no ingress, and the `letsencrypt-staging` issuer, so an environment without its overlay claims no real hostname and no real certificate. `values.schema.json` refuses an unknown tier or issuer, and the chart refuses to render without an image digest.

`deploy/chart/anville-bootstrap` holds the two `ClusterIssuer`s (`letsencrypt-staging` and `letsencrypt-prod`, both HTTP-01 through Traefik), installed once per host. cert-manager itself is not vendored into it: the deploy workflow installs cert-manager's own chart at a pinned version first, because the issuers cannot be created until its definitions and webhook exist. "Staging" in an issuer's name is Let's Encrypt's test service and has nothing to do with an environment's tier: every real environment, staging tier included, uses `letsencrypt-prod`.

## 6. Environments

An environment is a directory, a GitHub Environment and a namespace, all with the same name: `<deployment>-<tier>`.

```
deploy/environments/
  whatever-you-do-staging/       # now
  whatever-you-do-production/    # later
  <next-pathway>-staging/        # later still
```

Its `values.yaml` holds only the deltas:

```yaml
tier: staging                       # staging | production
host: anville-staging-01.vabl.dev   # the canonical name of the host that carries it (section 9)
hostname: anville.vabl.dev
issuer: letsencrypt-prod
postgres:
  enabled: true                     # false = use the DATABASE_URL secret (managed database)
  storage: 5Gi
backup:
  enabled: true
  schedule: "15 2 * * *"
resources: { ... }
```

Its GitHub Environment holds:

| Kind | Name | Notes |
|---|---|---|
| Secret | `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`, `KUBECONFIG` | Access to the host its values name. Environments on one host repeat them. The deploy reaches the host by its canonical name, so `DEPLOY_KNOWN_HOSTS` is scanned by that name |
| Secret | `DJANGO_SECRET_KEY` | Never shared between environments |
| Secret | `ANVILLE_ENROLMENT_CODE` | Per environment, and only where its values turn `enrolment.required` on. The chart turns it on unless told otherwise, as the application does; `whatever-you-do-staging` turns it off (ticket 37) |
| Secret | `POSTGRES_PASSWORD` | In-cluster database; the chart composes `DATABASE_URL` from it, so it must be safe inside a URL: letters, digits, `-` and `_` only. It is read when the database is first created, and changing it later does not change the database's password |
| Secret | `DATABASE_URL` | Managed database only, in place of the above |
| Secret | `BACKUP_SSH_KEY`, `BACKUP_TARGET`, `BACKUP_KNOWN_HOSTS` | Storage Box sub-account for this environment: its private key, its address as `sftp://user@host:23/directory/`, and the Storage Box's host key as `ssh-keyscan` prints it |
| Secret | `EMAIL_URL` | Mailjet SMTP credentials; absent while the environment's email is fake (section 11) |

Production environments get GitHub's required-reviewer rule. Staging environments do not.

**Adding an environment** is then: copy a directory and edit four lines, create the GitHub Environment and its secrets, point a DNS record at the host, run the deploy workflow. No workflow or chart change. **Removing one** is deleting the namespace, the directory and the GitHub Environment.

### How the three stages map to hosts

| Stage | Hosts | Environments |
|---|---|---|
| Now | `anville-staging-01.vabl.dev` (CX23) | `whatever-you-do-staging` at `anville.vabl.dev` |
| Later | plus `anville-production-01` (CX33) | plus `whatever-you-do-production` at `whateveryoudo.org` |
| Several pathways under test | the same two, until one fills | more namespaces on the host of the matching tier, each with its own hostname |

Rules that keep this safe:

- **Tiers never share a host.** Staging holds fake data only (spec, story 87); production holds special-category data. A staging host is also where experiments with the cluster itself happen.
- **Environments of the same tier may share a host.** Each still has its own database, secrets and namespace, so ADR 0002's isolation holds at the data level. A rough guide: each environment costs 300–500 MB of RAM (two gunicorn workers and a small PostgreSQL) on top of roughly 1 GB for k3s, Traefik and cert-manager, so a CX23 carries three or four staging environments. That figure is an estimate and should be measured on the first one.
- **An organisation that needs its own Hetzner account gets its own host**, from the same cloud-init template. Moving an environment between hosts is a restore plus a change of `host` in its values, and of the three access secrets.

For now one operator holds the Hetzner project, the repository and its GitHub Environments. Ticket 26 expects the Hetzner account to belong to the content owner with the developer deploying into it; that split is deliberately not handled yet. Nothing above prevents it later, since the workflow reaches a host only through an SSH key and a kubeconfig.

## 7. The database and its backups

Three levels, chosen per environment from its values. The chart and the deploy workflow are the same for all three.

| Level | Database | Recovery | Use for |
|---|---|---|---|
| **A** | In-cluster PostgreSQL | Nightly `pg_dump` to a Storage Box, plus Hetzner's server backups | Staging |
| **B** | In-cluster PostgreSQL | A, plus WAL archiving with pgBackRest for point-in-time recovery | Production, self-managed |
| **C** | Ubicloud managed PostgreSQL | Ubicloud's own point-in-time recovery, plus the same nightly `pg_dump` as an independent copy | Production, managed |

**The nightly dump** is the common piece. The CronJob runs `pg_dump --format=custom` against whatever `DATABASE_URL` the environment has, checks that the dump can be read back, and sends it over SFTP to a Storage Box sub-account that can see only that environment's directory. It refuses a target whose host key is not the one it was given, and keeps the newest 30 dumps. Because it only needs a connection string, it runs unchanged against an in-cluster or a Ubicloud database. This is the copy that depends on neither the host nor Ubicloud's account continuing to exist.

**Level A** satisfies ticket 26 ("the database has backups and a restore has been tried once"). Hetzner's server backups (20% of the server price) are a convenience for rebuilding the host; they are crash-consistent disk images, not a database backup, and are not counted as one.

**Level C, Ubicloud, is optional per environment.** Set `postgres.enabled: false` and supply `DATABASE_URL`. Nothing else changes:

- The connection must use TLS (`sslmode=require` or stricter in the URL), since it leaves the host.
- Ubicloud's firewall for the database should admit only the host's addresses.
- Put the host in the Hetzner location nearest the Ubicloud region, and set `CONN_MAX_AGE`, because every new connection now costs a TLS handshake across a network.
- An environment can start at level A or B and move to C later with a dump and restore and a change of two values.
- It adds a second processor of special-category data. That belongs on the open legal list in the spec before a production environment uses it.
- Ubicloud's pricing, regions and firewall behaviour were not verifiable when the sizing doc was written and are still unverified here.

**Level B** is the alternative if Ubicloud is not wanted for production: more setup and a standing responsibility, as the sizing doc says. It need not be designed until a production environment is near.

**One server per environment, not one per host.** At levels A and B each environment runs its own PostgreSQL server in its own namespace. A single server per host, installed by the bootstrap chart with a database for each environment, would use less memory, but:

- **Isolation (ADR 0002).** Each environment has its own superuser and password, and its NetworkPolicy admits only its own pods. No environment can fill another's disk, use up its connections or slow it with a runaway query. A shared server puts every environment's data behind one superuser.
- **Recovery per environment.** A nightly `pg_dump` works per database either way, but pgBackRest's point-in-time recovery (level B) restores a whole server. On a shared server, one organisation could not be rolled back to 14:32 without rolling back every other one too.
- **Upgrades per environment.** A PostgreSQL major upgrade, a configuration change or a restart affects only the environment that wanted it. In the bootstrap chart, which is installed once and otherwise left alone, it would affect every environment at once.
- **Nothing to provision.** The chart's server creates its database from `POSTGRES_PASSWORD` on first start, and deleting the namespace removes it. A shared server needs a step, holding its superuser password, that creates each environment's role and database before the first deploy, and drops them when the environment goes.
- **Each environment moves alone.** It can go to another host, or to level C, by changing only its own values.

The cost is memory: the chart requests 192 MiB for each environment's PostgreSQL, part of the 300–500 MB per environment in section 6. That is affordable for the few environments a host carries now.

**If many small environments are to share a host**, for instance short-lived staging environments where memory runs out first, one shared server per host can be added without reworking the chart, because the level C path already takes any `DATABASE_URL`. It needs:

- A PostgreSQL StatefulSet in its own namespace, with its own volume and a superuser password kept off the environments' secrets: in the bootstrap chart, or better a separate chart, so the bootstrap chart's cert-manager and issuers are not upgraded with it.
- A provisioning step per environment, run by the operator or a Job in that namespace: `CREATE ROLE` with the environment's password and `CREATE DATABASE ... OWNER` that role, then `REVOKE CONNECT ... FROM PUBLIC` on each database, so no environment's role can open another's. A matching step drops both when the environment is removed.
- A NetworkPolicy on the shared server admitting the namespaces of the environments that use it, by namespace label, in place of the per-environment policy.
- In each such environment's values, `postgres.enabled: false`, and in its secrets, a `DATABASE_URL` naming its own role and database on the shared Service (`<release>-postgres.<namespace>.svc.cluster.local`). No TLS is needed, since the connection stays on the host.
- The nightly dump, unchanged: it already runs `pg_dump` against the environment's `DATABASE_URL`, and the environment's role owns its database, so the dump stays per environment and goes to the environment's own Storage Box directory.
- One server's limits and tuning for all of them: `max_connections` above the sum of every environment's gunicorn workers plus the backups (each worker holds a connection while `CONN_MAX_AGE` lasts), and a memory limit sized for the total.

Point-in-time recovery for a shared server stays all-or-nothing, so shared servers suit staging, and production keeps one server per environment.

**Restores are rehearsed.** A dump is restored into a scratch namespace with no ingress, on a host of the same tier, and the smoke test run against it by port-forward. Production dumps are never restored onto a staging host: the sizing doc calls that a data-protection event, and it is.

## 8. Deploy workflow (`deploy.yml`)

`workflow_dispatch` with two inputs: `environment` (a string, checked against `deploy/environments/`) and `tag` (default `latest`). The job runs in that GitHub Environment. Deploys run one at a time, whatever the host, so two never touch one host together; a queue per host would need the host's name before the GitHub Environment is in reach.

Each step below is a script under `deploy/`, which the workflow calls in order. That is what lets them be run and tested without GitHub, and lets an operator run one by hand.

1. **Resolve the digest** for the tag from the registry, and the commit it was built from. A missing image stops the run before the host is touched.
2. **Open the SSH tunnel** to the k3s API on `127.0.0.1:6443`, with the host key pinned.
3. **Check the secrets and the host.** Every secret the environment needs, by what its values say it is, must be present before anything is applied. The environment's `tier` must match the tier label on the k3s node; a production environment aimed at a staging host fails here.
4. **Create the namespace and apply the secrets** with `kubectl create secret --dry-run=client -o yaml | kubectl apply -f -`.
5. **`helm upgrade --install`** three times: cert-manager's own chart at a pinned version, `anville-bootstrap`, then `anville -n <environment>` with the chart's values, the environment's values and `--set image.digest=…`, with `--wait`. The same digest and the same secrets mean no rollout. A deploy that fails is left as it is, not rolled back, with the pods, the migration's log and the latest events printed.
6. **Assert the version.** `GET https://<hostname>/healthz` must return the commit resolved in step 1. This catches a wrong DNS record, a failed certificate and a pod that never became ready, from the outside.
7. **Tear the tunnel down**, always.

Promotion stays explicit: production is a deliberate run of the same workflow with the tag that was tested on staging. Staging may be deployed automatically after a successful pushed build by having `build.yml` call `deploy.yml`; that is a convenience to add once the manual path is trusted.

**Pathway documents are not loaded by the deploy.** `load_pathway` publishes whatever file it is given, so running it on every deploy would overwrite a version published from the studio once the studio exists. Loading is a separate, deliberate step: the `publish-pathway` workflow, run by hand with a pathway and an environment chosen from lists. It sends the document from `pathways/` on the branch chosen in GitHub's "Use workflow from" list, not the image's copy, into the environment's pod and runs `manage.py load_pathway` on it there, so the deployed version checks it. It shares the deploy workflow's concurrency group. A pathway that must not be public cannot travel in the repository or the image; it would be sent into the pod the same way from elsewhere, or published from the studio. The same route serves `createsuperuser`, `changepassword` (the staging password-reset procedure, ticket 26) and `seed_observers`, which is for staging only.

## 9. The host

**Each host has a canonical name**, `anville-<tier>-<number>` under a domain the operator controls, such as `anville-staging-01.vabl.dev`. The number is never reused, so a name always means one machine. The name is the server's name in Hetzner, the host's hostname and its reverse DNS, and a node label (`anville-host`) beside the tier. Each environment's `host` value holds it: the deploy workflow reaches the host by that name, and `deploy.sh` refuses a node labelled with another. The A record for the name is made by hand once the script has printed the address, like every other record here (section 10), so no DNS credentials are needed to create a host.

**Each host is created in a named Hetzner project.** The script is given an `hcloud` context, named after the project and holding an API token made in it, and uses only that context, whichever is active. It refuses to run while `HCLOUD_TOKEN` is set, since that token would override the context's and could belong to any project. A token cannot be asked which project it belongs to, so the context's name is only as true as the token put in it.

Created once by `deploy/infra/hcloud-create.sh <project> <host> <tier>`, which first refuses a name that is not fully qualified, does not name its tier, already resolves, or is already a server's in the project, and then uses the `hcloud` CLI to:

1. create a Hetzner Cloud Firewall admitting 22, 80 and 443 over TCP, and ICMP, unless the project already has it;
2. add the operator's public key to the project, so that Hetzner sets no root password and emails none;
3. create the server, named with the host's canonical name, in an EU location (FSN1, NBG1 or HEL1) from the Ubuntu LTS image, passing the rendered cloud-init as user data, attaching the firewall and enabling Hetzner backups;
4. set the reverse DNS of its IPv4 address to the canonical name.

It ends by printing what to do next: the A record to make, how to wait for the first boot, and what each environment on the host needs. `hcloud-create.sh --render` prints the cloud-init and creates nothing.

The host's tier and canonical name are parameters of the template, which sets the hostname from the name, and both as k3s node labels for the deploy workflow to check.

`cloud-init.yaml.template` is LivePace's with the provider-specific parts changed:

- two accounts: `deploy` for the workflow, and a named interactive sudoer. The deploy key is restricted in `authorized_keys` to one thing, forwarding a port to the k3s API on the host: it has no shell, no sudo and cannot read the kubeconfig, a copy of which the workflow holds as a secret. Root login over SSH is disabled; Hetzner images otherwise leave root as the login;
- base packages, 2 GiB swap, `vm.swappiness=10`, SSH without passwords, and unattended upgrades, which restart the host at 03:30 UTC when an update needs it;
- UFW admitting 22, 80 and 443, with the k3s pod and service networks allowed. **6443 is not opened**;
- k3s in server mode with its bundled Traefik and kubectl, with secrets encrypted at rest. Helm is not installed on the host: it runs in the deploy workflow, through the tunnel;
- k9s, for the operator to look at the cluster in a terminal (`sudo k9s --kubeconfig /etc/rancher/k3s/k3s.yaml`), a pinned release checked against its checksum by `infra/install-k9s.sh`, which the template carries whole. It is not in an apt repository, so unattended upgrades leave it alone; the same script, run over SSH, installs it on an older host or changes its version.

Nothing in the template depends on the architecture, so an ARM host remains possible: k9s is fetched for the host's.

The outside-in check that LivePace does with a probe script is done here by step 6 of the deploy.

## 10. Request topology

| Public endpoint | Fronted by | Backend |
|---|---|---|
| `https://<environment hostname>` | Traefik Ingress, TLS | `anville` :8000 in that environment's namespace |

PostgreSQL has no public endpoint at levels A and B.

### Hostnames and DNS

| Environment | Hostname | DNS |
|---|---|---|
| `whatever-you-do-staging` | `anville.vabl.dev` | Cloudflare |
| `whatever-you-do-production` | `whateveryoudo.org` (envisaged) | Not yet determined |
| Further staging environments | Suggested: `<deployment>.anville.vabl.dev` | Cloudflare |

Each host has an A record for its canonical name (section 9), made by hand once it is created. Each environment's hostname is a CNAME to that name, so rebuilding a host changes one record, not one per environment. A zone's apex cannot be a CNAME: there, an A record with the host's address, unless the DNS provider flattens a CNAME, as Cloudflare does. With HTTP-01 the record must exist, and resolve to the host, before the first deploy, or the certificate cannot be issued.

- **No AAAA record for now.** k3s is installed with an IPv4-only pod network, and its load balancer then publishes 80 and 443 on the host's IPv4 address only. An AAAA record would send IPv6 visitors, and Let's Encrypt's validation, which prefers IPv6, to an address where nothing answers. Serving over IPv6 means installing k3s dual-stack, a change to the cloud-init template to make when it is wanted. This is reasoned from how k3s works and has not been tried on a host.

- **Cloudflare records are DNS-only, not proxied.** Proxying would end TLS at Cloudflare, break the plain HTTP-01 path unless configured around, and put a further processor in front of participants' answers. Traefik on the host is the only TLS endpoint.
- **`.dev` is HTTPS-only in browsers.** The whole top-level domain is HSTS-preloaded, so a browser will not load `anville.vabl.dev` over plain HTTP and will not let anyone click past a certificate warning. The first deploy must therefore go straight to `letsencrypt-prod`; trying it out with Let's Encrypt's test issuer produces a site no browser will open. Use `curl -k` against `/healthz` if the test issuer is wanted for a dry run.
- **Production does not depend on the DNS decision.** HTTP-01 needs only that `whateveryoudo.org` resolves to the host. The apex needs an A record there, or a flattened CNAME; if `www.whateveryoudo.org` is wanted, it is a second hostname on the same Ingress and certificate, redirected to the apex, and both go in `DJANGO_ALLOWED_HOSTS`.
- **Cloudflare DNS-01 is the alternative for staging only**, as LivePace does it: a certificate before the records point anywhere, and one wildcard for `*.anville.vabl.dev` covering every later staging environment. It costs a Cloudflare API token on the staging host that can edit the `vabl.dev` zone, which holds more than Anville. It is left out until the number of staging environments makes the wildcard worth that.

A staging environment is private in the sense ticket 26 means: an unadvertised hostname and fake data only. Its sign-up is open, since ticket 37 turned the enrolment code off there, so the chart sets `ANVILLE_DEMO_NOTICE` on every staging-tier environment, as it sets the email disclaimer: the homepage and the account pages say it is a demo, to use made-up details, and that data may be wiped. The wording is `demo.notice` in its values, and may be changed but not emptied. The enrolment code can still be turned back on per environment (`enrolment.required`). If that is not enough, Traefik can put basic authentication in front of a staging environment from its values; note that observers following a link would meet it too.

## 11. Email delivery

Initial delivery is through **Mailjet**, over SMTP, with Django's own SMTP backend. No mail runs on the host.

- **Configuration is one URL.** `EMAIL_URL=smtp+tls://<api key>:<secret key>@in-v3.mailjet.com:587`, a per-environment secret, plus `DEFAULT_FROM_EMAIL` in the environment's values. Changing provider later is a change of that secret, not of the image. Port 587 is the one to use: Hetzner blocks outbound 25 and 465 on new accounts.
- **No new dependency.** django-environ already parses the URL. A provider package such as django-anymail is only worth adding if delivery webhooks (bounces, complaints) are wanted.
- **Unset means fake email.** Without `EMAIL_URL` the console backend is used: each message is written to the pod's log and nothing leaves the host. Password reset stays refused until ticket 28a turns it on; a deploy must not enable it merely because the secret is present.
- **One Mailjet API key per environment**, so a staging key can be revoked without touching production and each environment's sending is visible apart. Mailjet's sub-accounts are the likely way to do this; that should be confirmed against the plan in use.
- **A validated sending domain per production environment**, with SPF, DKIM and DMARC, on a subdomain used for nothing else: for *Whatever You Do*, a subdomain of `whateveryoudo.org`. Mailjet's validation records go in whichever DNS host that domain ends up with. The sizing doc's point stands: deliverability of observer invitations to consumer mailboxes is the risk, not cost.
- **Staging goes in two stages** (below).
- **It is another processor**, receiving participants' and observers' addresses and the text of each message. It joins Ubicloud on the open legal list before production use.

### Email on staging

**First, fake email.** A staging environment starts with no `EMAIL_URL`. Anything the application sends appears in the pod's log, where the operator reads it through the tunnel with `kubectl logs`. That puts links and their tokens in a log, which is acceptable only because staging holds fake data. If reading logs becomes tedious, a mail catcher such as Mailpit in the environment's namespace is the next step up, still delivering nothing.

**Later, actual email with a disclaimer.** When staging needs to reach real mailboxes, it gets its own Mailjet API key, a sending address at `anville.vabl.dev` validated with records in Cloudflare, and a disclaimer on every message:

- The disclaimer is one setting, `ANVILLE_EMAIL_DISCLAIMER`. When set, a thin email backend wrapping the configured one puts a marker in the subject (`[TEST]`) and the disclaimer text at the top of the body, text and HTML alike. It works at the backend so that it covers every message whichever code sent it, allauth's included, and no template has to remember it. This is built (`config/email.py`), and applies to fake email as well, so the marked message can be seen in the pod's log before any real sending is set up.
- Suggested wording: "This message comes from a test system for Anville. It is not intended for production use. If you were not expecting it, please ignore it."
- **The chart sets it from the tier.** Every `tier: staging` environment gets the disclaimer; the wording can be overridden in its values (`email.disclaimer`), but not removed: the chart refuses to render a staging environment with an empty one. A staging environment therefore cannot send real mail without it, and a production environment never carries it.
- Mail to staging's reserved example addresses still bounces and counts against the sender's reputation. Real sending is for the real addresses of people who know they are testing, and those addresses are then real data on staging: the one exception to "fake data only", to be kept small and agreed.

**Production never runs on fake email.** The deploy workflow refuses a `tier: production` environment that has no `EMAIL_URL`, since the console backend there would write participants' and observers' links into a log and deliver nothing.

The sizing doc priced Scaleway TEM for this line; Mailjet replaces it for now and that figure has not been re-estimated.

Sending is in the request path until a worker exists. That is acceptable for sign-in and reset messages. Scheduled or bulk sending, such as invitation reminders, is when the worker and Redis left out in section 2 come back.

## 12. Development

Nothing here changes how Anville is developed:

- `compose.yaml` keeps providing PostgreSQL 17 on `localhost:5432`, and Django runs with `manage.py runserver` as the README describes.
- The `Dockerfile` adds one optional thing: an `app` service in `compose.yaml` under a Compose profile, built from the same `Dockerfile`, so `docker compose --profile app up --build` runs the real image against the compose database, at http://localhost:8001. That is the way to check gunicorn, WhiteNoise and the proxy settings without a cluster. Plain `docker compose up -d` still starts only the database.
- No developer needs k3s, Helm or kubectl locally. The chart can be checked with `helm lint` and `helm template` in the build workflow.

The image is the shared artefact. Compose and Helm are two ways of running it, and compose is never used on a host.

## 13. The load-bearing decisions

1. **Everything is in git and runs from CI.** Rebuilding a host is `hcloud-create.sh`, the GitHub Environment secrets, a deploy, and a restore.
2. **An environment is data, not code.** A directory and a GitHub Environment; no workflow or chart edits to add one.
3. **Immutable digests.** A tag is a lookup key; the digest is what runs.
4. **Build and deploy are separate,** and promotion to production is a deliberate act with a reviewer.
5. **One image for every environment,** configured from the environment (ADR 0002).
6. **Tiers never share a host;** environments of one tier may.
7. **The database's location is a per-environment value.** In-cluster and Ubicloud differ by two values, and the independent nightly dump runs against either.
8. **Least exposure.** Three public ports, no public cluster API, no public database.
9. **Single node and honest about it.** One replica, `Recreate`, local-path storage. A host failure is a rebuild and a restore, which the sizing doc accepts for a pathway completed over weeks.

k3s is more machinery than one Django service strictly needs. It is kept because it is the approach already proven on LivePace, and because namespaces are what make the many-environments stage a matter of adding a directory.

## 14. Order of work

The steps for the first environment, `whatever-you-do-staging`, are in ticket 26 (`.scratch/whatever-you-do-milestone-1/issues/26-staging-deployment.md`), and are not repeated here.

Later, each when needed: `anville-production-01` and the production environment; the choice between levels B and C; actual email on staging, with its disclaimer; a lasting email set-up for production; automatic staging deploys; a second environment on `anville-staging-01`.

## 15. Open questions

- **Who hosts DNS for `whateveryoudo.org`.** It does not block anything here: certificates use HTTP-01, and the host's records and Mailjet's validation records can be created at any DNS host.
- **Whether production is served at the apex, `www`, or both.**
- **Hostnames for later environments**, staging and production. `<deployment>.anville.vabl.dev` is a suggestion for staging; a second organisation's production hostname is theirs to choose.
