# Server deployment approach (baseline for other projects)

> Status: internal note, not part of the shipped docs set. Do not commit.
> It distills how LivePace's server side is built and deployed so the same
> shape can be lifted into other projects. Where it says "LivePace does X",
> read it as "here is a pattern that worked; reuse or adapt it".

## 1. What the stack is, in one paragraph

Several small services are each built into a **multi-arch Docker image** by a
per-service **GitHub Actions** workflow, pushed to Docker Hub by digest, and
stitched into a manifest list tagged with the commit SHA and `latest`. A single
**Helm umbrella chart** describes the whole application; a separate **deploy
workflow** resolves the exact image digests, SSHes to a single-node **k3s**
host over a port-forward tunnel, materializes secrets, and runs `helm upgrade
--install`. k3s brings its own **Traefik** ingress and load balancer;
**cert-manager** issues TLS via Let's Encrypt DNS-01. The host itself is
provisioned once from a **cloud-init** template and never hand-configured
again. The result is a cheap (Oracle Always Free A1 ARM node), reproducible,
auditable deployment driven entirely from git + GitHub Actions.

Key directories:

- `srv/<service>/` — each service plus its `Dockerfile` (`api`, `broker`, `coap`, `keypair-mint`); `web/` is the SPA.
- `srv/charts/` — Helm charts (umbrella `livepace` + subcharts, plus `livepace-bootstrap`).
- `srv/deploy/<env>/` — per-environment Helm value overrides + secret examples.
- `srv/deploy/*.sh` — digest resolution, image traceability, host firewall sync/probe.
- `srv/infra/` — one-time OCI node provisioning.
- `.github/workflows/srv-*.yml` — build + deploy pipeline.

## 2. The services (container shape)

Each service is a small, single-responsibility container built as a multi-stage
image, running as a non-root user, with a health check and a single exposed
port. The variety of runtimes below is deliberate — the deployment machinery
doesn't care what's inside the image.

| Service | Runtime | Base images (build -> run) | Port | Health |
|---|---|---|---|---|
| `livepace-api` | Bun + Hono | `oven/bun:1.3-alpine` (deps -> run) | 8080/tcp | `GET /healthz` |
| `livepace-broker` | Mosquitto + mosquitto-go-auth | `golang:1.24-bookworm` -> `debian:bookworm-slim` | 1883 (MQTT), 8083 (WS) | none |
| `livepace-coap-receiver` | JVM 21 (Californium) | `gradle:8.10-jdk21` -> `eclipse-temurin:21-jre` | 5683/udp | `pgrep` |
| `livepace-keypair-mint` | Alpine + openssl + kubectl | `alpine:3.20` (single stage) | n/a (Job) | none |
| `livepace-web` | Vite build -> nginx | `node:22-alpine` -> `nginx:1.27-alpine` | 80/tcp | `GET /healthz` |

Reusable conventions worth copying:

- **Multi-stage builds** keep runtime images lean (no toolchain in the final layer).
- **Non-root runtime user** in every long-running service image.
- **`/healthz` endpoint** on HTTP services, wired to both the Docker `HEALTHCHECK` and the k8s liveness/readiness probes.
- **Config injected at container start, not baked in.** The web image writes `API_ORIGIN`/`LIVE_ORIGIN`/`HOME_ORIGIN` into `/config.js` from env at boot, so one built image serves every environment. Prefer this over per-env image builds.

## 3. Image build pipeline (GitHub Actions)

One workflow per service: `srv-api-build.yml`, `srv-broker-build.yml`,
`srv-coap-build.yml`, `srv-keypair-mint-build.yml`, `srv-web-build.yml`. They
are near-identical, which is itself the pattern — copy one to add a service.

Shared shape:

- **Trigger:** `workflow_dispatch` (with an explicit push true/false choice) and auto-push on `main` or `v*` tags. Non-main/non-tag runs build but don't push.
- **Multi-arch without QEMU:** amd64 on `ubuntu-latest`, arm64 on `ubuntu-24.04-arm` — each arch builds natively on its own runner, in parallel. (arm64 is the real target; the host is an ARM node.)
- **Push by digest, then merge:** each arch pushes with `push-by-digest=true` (no tag). A `merge` job runs `docker buildx imagetools create` to assemble the per-arch digests into one manifest list, tagged `:<git-sha>` and `:latest`.
- **Provenance:** the git commit is stamped into the image as the OCI `org.opencontainers.image.revision` annotation, so a running image can be traced back to source.
- **Pre-build tests where cheap:** e.g. the broker workflow runs `node --test test/` before building. Add service tests here, not in the deploy path.
- **Registry auth:** Docker Hub via `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` repo secrets.

Separately, `srv-races-upload.yml` shows a **content-only deploy** that needs no
cluster access: on changes under `srv/seed/**` it `curl`s a PUT to a public
admin API with a bearer token. Not every "deploy" needs Helm — data/seed
changes can go straight through an idempotent API endpoint.

## 4. The Helm chart layout

`srv/charts/livepace` is an **umbrella chart** whose `Chart.yaml` declares the
services as local-path subchart dependencies plus one external dependency
(Bitnami Redis, disabled by default):

```
livepace (umbrella)
├── livepace-api              (Deployment + Service + optional PVC)
├── livepace-web              (Deployment + Service)         [conditional]
├── livepace-broker           (Deployment + Service + optional PVC + logging CM)
├── livepace-coap-receiver    (Deployment + LoadBalancer Svc + pre-install keypair Job)  [conditional]
└── livepace-redis (bitnami)  [conditional, off until api scales past 1 replica]
```

The umbrella also owns the cross-cutting resources: the Ingresses (one per
hostname), a Traefik `IngressRouteTCP` for native MQTTS on 8883, and ConfigMaps
for the rendered host-firewall rules, the image manifest (traceability), the
CoAP public key, and the AASA/assetlinks deep-link manifests.

A second, separately-installed chart `livepace-bootstrap` holds **cluster
prerequisites**: it pulls in cert-manager (Jetstack subchart) and defines the
`letsencrypt-staging` / `letsencrypt-prod` `ClusterIssuer`s (Cloudflare DNS-01).
Keeping cluster-level bootstrap out of the app chart means the app chart can be
upgraded freely without touching cert-manager.

Reusable conventions:

- **Umbrella + subcharts** gives one `helm upgrade` for the whole app while keeping each service's templates self-contained and independently reusable.
- **Conditional subcharts** (`<name>.enabled`) let staging and production enable/disable pieces (Redis, CoAP, web) from values alone.
- **Recreate strategy** on stateful single-replica services (SQLite on an RWO volume; long-lived MQTT connections) avoids multi-attach and connection-storm problems that a rolling update would cause on one node.
- **pre-install/pre-upgrade Job** (`keypair-mint`) for one-time secret material, made **idempotent** (skips if the Secret already exists) and **RBAC-scoped** to exactly the one Secret it manages.
- **Resource requests/limits on everything**, sized for a 2-OCPU/12 GiB node, so the single node can't be starved by one pod.

## 5. Environments (staging vs production)

`srv/deploy/staging/values.yaml` and `srv/deploy/production/values.yaml` are
thin overlays on top of the chart's base `values.yaml`. Only the deltas live
here: hostnames, TLS issuer, image tags, persistence sizes, replica counts,
resource caps, and the mobile-app deep-link allow-lists. The deploy workflow
layers them: `-f charts/livepace/values.yaml -f deploy/<env>/values.yaml`.

Design points to copy:

- **Base chart ships safe defaults** (e.g. ingress disabled / `letsencrypt-staging`) so a misconfigured deploy fails closed rather than claiming a real hostname.
- **Promotion is explicit, not automatic.** Production is reached by re-running the deploy workflow with `environment: production`; there's no auto-promote from staging. The GitHub Environment scopes the secrets.
- **Secrets never live in git.** `secrets.example.yaml` documents the shape; real values are GitHub Environment secrets, materialized into the cluster at deploy time (see below). Per-environment secrets (e.g. `JWT_HMAC_SECRET`) must not be reused across environments.

## 6. The deploy workflow (`srv-deploy.yml`)

Manual `workflow_dispatch` with `environment` (staging/production) and a per-image
tag input each (default `latest`). Steps:

1. **Resolve + verify digests.** For each image tag, `srv/deploy/resolve-image-digests.sh` queries Docker Hub for five facts: manifest-list digest, arm64 manifest digest, arm64 config-blob digest, the tag, and the embedded commit SHA. Missing image -> fail fast, before touching the cluster.
2. **Open an SSH tunnel to the k3s API.** The host exposes **no** k8s API port publicly — 6443 stays bound to localhost. The workflow uses `webfactory/ssh-agent`, pins the host key (`DEPLOY_KNOWN_HOSTS` or `ssh-keyscan`), and opens `ssh -N -f -L 6443:127.0.0.1:6443 ubuntu@$DEPLOY_HOST`. The kubeconfig (from the `KUBECONFIG_ACCESS` secret) keeps its `127.0.0.1:6443` server URL and works through the tunnel.
3. **Materialize secrets** via `kubectl create secret ... --dry-run=client -o yaml | kubectl apply -f -`: the app secret bundle (`livepace-secrets`: JWT HMAC, admin/race/CoAP tokens), the `cloudflare-api-token` (cert-manager namespace), and the `livepace-dockerhub` image-pull secret.
4. **`helm upgrade --install livepace-bootstrap`** (cert-manager + issuers), then **`helm upgrade --install livepace`** (the app), passing each resolved digest in as `--set <svc>.image.digest=...` plus the tag/commit/arch-manifest values, with `--wait --timeout 5m`.
5. **Consistency assertion.** Derives the CoAP public key from the private key in the cluster Secret and compares it to the advertised `livepace-coap-pubkey` ConfigMap; a mismatch **fails the deploy** rather than silently serving a stale key.
6. **Ship the host-firewall scripts** to the node and **tear down the tunnel** (an `always()` cleanup step).

Reusable conventions:

- **Pin by digest, not tag.** The tag (`latest`) is only a lookup key; what lands in the pod spec is the immutable digest. Because the digest is part of the pod template, Helm rolls the Deployment **iff** the image actually changed — same digest, no rollout.
- **No inbound cluster API.** Admin access is an SSH port-forward, so the only public ports are the ones the app needs (see firewall below).
- **Deploy-time correctness gates.** The keypair consistency check is a cheap assertion that turns a whole class of "silent desync" incidents into a red build.
- **Secrets flow GitHub Env -> `kubectl apply` at deploy time**; nothing sensitive is stored in the chart or the repo.

## 7. Image traceability

Every pod carries five annotations — `livepace.fit/image-{tag,commit,manifest-list,manifest-arm64,config-arm64}` — and the deploy writes the same set into a `livepace-image-manifest` ConfigMap. Four scripts close the loop:

- `resolve-image-digests.sh` — the five OCI facts for one image.
- `image-traceability-hub.sh` — dumps what Docker Hub currently has, as JSON.
- `image-traceability-cluster.sh` — dumps what the ConfigMap says was deployed and what the pods are actually running (`containerStatuses[].imageID`).
- `image-traceability-compare.sh` — diffs hub -> deployed -> running and prints OK / STALE / NO-POD per image.

This collapses "is the running pod on the build I think it is?" into one
command, keyed on git commit. Worth copying wholesale for any registry-backed
deploy.

## 8. The host and the firewall

Provisioned once, declaratively:

- `srv/infra/oci-setup.sh` + `oci-create.sh` launch a `VM.Standard.A1.Flex` (2 OCPU / 12 GiB, within Oracle Always Free) and inject the cloud-init template.
- `srv/deploy/cloud-init.cfg.template` does all first-boot setup: two accounts (`ubuntu` = passwordless automation with no sudo; `vabl` = interactive sudoer), base packages, 2 GiB swap, `vm.swappiness=10`, SSH hardening (no passwords), UFW, unattended-upgrades, then installs **k3s** (server mode, bundled Traefik, kubeconfig readable by `ubuntu`), Helm, kubectl, and k9s — arch-aware so the same template works on amd64 or arm64.
- UFW opens only 22/tcp, 80/tcp, 443/tcp, 8883/tcp (MQTTS), 5683/udp (CoAP). **6443 is deliberately not opened** — the k8s API is reached only via the SSH tunnel. Plain MQTT (1883) and WS (8083) stay cluster-internal behind Traefik TLS.

Firewall rules are themselves **declared in the chart** (rendered into the
`livepace-host-firewall` ConfigMap) and reconciled onto the host out-of-band by
`host-firewall-sync.sh` (dry-run by default, `--apply` to change; needs sudo).
`host-firewall-probe.sh` does an **outside-in** reachability check that also
catches cloud-provider (OCI VCN security-list) misconfigurations that UFW alone
can't see. Keeping the desired firewall state in the chart means it's reviewed
and versioned like everything else.

## 9. Request topology (how traffic reaches the pods)

k3s's bundled Traefik is the single ingress; cert-manager supplies the certs.

| Public endpoint | Fronted by | Backend |
|---|---|---|
| `https://api.livepace.fit` | Traefik Ingress (TLS) | api :8080 |
| `https://live` / `track.livepace.fit` | Traefik Ingress (TLS) | web / aasa nginx :80 |
| `wss://mqtt.livepace.fit/mqtt` (443) | Traefik Ingress (TLS upgrade) | broker :8083 |
| `mqtts://mqtt.livepace.fit:8883` | Traefik `IngressRouteTCP` (TCP+TLS) | broker :1883 |
| `coap://coap.livepace.fit:5683` | Service `LoadBalancer` (k3s klipper-lb) | coap-receiver :5683/udp |

One DNS point of rotation: every hostname CNAMEs to the node's FQDN. TLS is one
cert per host via cert-manager + Cloudflare DNS-01; the MQTT cert is shared
between the WSS (443) and native MQTTS (8883) routes. UDP (CoAP) can't go
through Traefik, so it uses a `LoadBalancer` Service that k3s's klipper-lb maps
to the host port — the pattern for any non-HTTP/non-TCP ingress on k3s.

## 10. Why this is stable — the load-bearing decisions

Lift these wholesale; the specific services are incidental.

1. **Everything is in git and runs from CI.** No hand-run `kubectl`/`helm` in the normal path; the host is never hand-edited after cloud-init. A rebuild from scratch is `oci-create.sh` + set GitHub secrets + run the deploy workflow.
2. **Immutable digests in the pod spec.** Deploys are idempotent and roll only on real change; `latest` is a convenience lookup, never the thing that's deployed.
3. **Build and deploy are separate workflows.** Building an image doesn't touch prod; deploying picks already-built, already-tested digests. Promotion staging -> production is an explicit manual dispatch.
4. **Secrets live in GitHub Environments, applied at deploy time.** Nothing sensitive in the repo or chart; per-env isolation enforced by convention.
5. **Fail-fast gates before and during deploy.** Missing image -> stop before the cluster; keypair desync -> red build, not a silent outage.
6. **Least-exposure host.** No public k8s API; only the five ports the app needs; firewall state declared in-chart and probed from outside.
7. **Config injected at runtime** so one image serves all environments — no env-specific image sprawl.
8. **Traceability as a first-class feature.** Pod annotations + ConfigMap + compare script answer "what's actually running?" deterministically.
9. **Cheap, single-node, honest about it.** Single replicas, `Recreate` strategy, local-path storage, resources sized to the node. HA levers (Redis, replicas>=2) exist in values and are switched on only when needed, not prematurely.

## 11. Checklist to adapt this to a new project

1. One `srv/<svc>/Dockerfile` per service: multi-stage, non-root, `/healthz`, runtime config from env.
2. Copy a `srv-<svc>-build.yml` per service: dual-arch native build, push-by-digest, merge to a SHA+latest manifest, stamp the commit annotation, run unit tests before build.
3. One umbrella Helm chart with a subchart per service; a separate bootstrap chart for cert-manager/issuers. Resource limits and probes on everything. Idempotent pre-install Jobs for one-time secret material.
4. `deploy/<env>/values.yaml` overlays for the deltas only; safe defaults in the base chart.
5. A `srv-deploy.yml`: resolve digests -> SSH-tunnel to the k8s API -> apply secrets from GitHub Env -> `helm upgrade --install` bootstrap then app with digests `--set` in -> post-deploy assertions -> teardown.
6. Provision the node once from a cloud-init template that installs k3s + Helm + kubectl and leaves the API bound to localhost; open only the app's ports.
7. Add the image-traceability trio (hub / cluster / compare) so you can always answer what's running.
