# Deploying Anville

> ✨ Written with AI assistance. The scripts and charts here have been tested as far as they can be without a host (see "What has been tested"), and nothing has yet been run against a real one. Ticket 26's runbook will record what actually happened, and this file should be corrected from it.

How a deployment is put together, and why, is in [docs/server-approach.md](../docs/server-approach.md). This file is how to do each thing.

Two words are used as that document uses them. A **host** is one Hetzner Cloud server running k3s. An **environment** is one installed copy of Anville: a namespace on a host, with its own hostname, database and secrets.

## What is here

| Path | What it is |
|---|---|
| `infra/hcloud-create.sh` | Creates a host, with `infra/cloud-init.yaml.template` as its first boot and `infra/firewall-rules.json` in front |
| `infra/install-k9s.sh` | Installs k9s on a host, with the operator's `k9` alias: run by its first boot, and by hand to change the version |
| `chart/anville/` | The Helm chart for one environment |
| `chart/anville-bootstrap/` | The Let's Encrypt issuers, installed once per host |
| `environments/<environment>/values.yaml` | What differs for that environment |
| `environments/<environment>/secrets.example.yaml` | What its GitHub Environment must hold. No values |
| `resolve-image-digest.sh` | Turns an image tag into a digest and the commit it was built from |
| `tunnel.sh` | Opens and closes the SSH tunnel to a host's k3s API |
| `deploy.sh` | Deploys one environment through that tunnel |
| `assert-version.sh` | Confirms from outside that the commit just deployed is the one being served |
| `publish-pathway.sh` | Publishes a document from `pathways/` to one environment through that tunnel |
| `check.sh` | Checks all of the above that can be checked without a cluster |

`.github/workflows/build.yml` builds the image, `.github/workflows/deploy.yml` runs the four deploy scripts in order, and `.github/workflows/publish-pathway.yml` opens the tunnel and runs `publish-pathway.sh`.

## Create a host

Each host has a **canonical name**, such as `anville-staging-01.vabl.dev`: `anville-<tier>-<number>` under a domain the operator controls, with the number never reused. It is the server's name in Hetzner, the host's own hostname and its reverse DNS, a label on its k3s node, and the name every environment on it uses to reach it. Its A record is made by hand.

Needs the `hcloud` CLI with a context for the Hetzner project the host belongs in, and two key pairs: the operator's own, and one made for the deploy workflow alone. Name the context after the project. The script uses only the context it is given, whichever is active, and refuses to run while `HCLOUD_TOKEN` is set, since that would override the context's token.

```sh
hcloud context create anville      # asks for an API token: in the Hetzner Console, that project's Security, API tokens, Read & Write
ssh-keygen -t ed25519 -N "" -C "anville deploy" -f ~/.ssh/anville-deploy

ADMIN_USER=<your account name> \
ADMIN_SSH_KEY_FILE=~/.ssh/id_ed25519.pub \
DEPLOY_SSH_KEY_FILE=~/.ssh/anville-deploy.pub \
deploy/infra/hcloud-create.sh anville anville-staging-01.vabl.dev staging
```

`hcloud-create.sh --render anville anville-staging-01.vabl.dev staging` prints the cloud-init and creates nothing. Before creating anything, the script refuses a name that already resolves, or that a server in the project already has. When it finishes it prints the next steps: the A record to make, how to wait for the first boot, how to confirm that 6443 is closed, and what each environment on the host needs.

The host's tier is fixed when it is created, and its first label must name it. A deploy refuses an environment of the other tier, and one whose values name another host.

## Add an environment

1. Copy an existing directory of `environments/` to `environments/<deployment>-<tier>/` and edit its `values.yaml`: the tier, the host (its canonical name), the hostname.
2. Create a GitHub Environment of the same name, holding what `secrets.example.yaml` lists. Generate each secret afresh. Give a production environment a required reviewer.
3. Point the hostname at the host: a CNAME to the host's canonical name, or an A record with its address where the hostname is a zone's apex and the DNS provider cannot flatten a CNAME (Cloudflare can). In Cloudflare, DNS-only, not proxied. No AAAA record: a host serves over IPv4 only for now. The record must resolve before the first deploy, or no certificate can be issued.
4. For the backup, create a Storage Box sub-account for this environment alone and give it the public half of `BACKUP_SSH_KEY`.
5. Deploy.

Removing one is deleting its namespace, its directory and its GitHub Environment.

## Deploy

The image must exist first. `build.yml` pushes one for a `v*` tag or a manual run, and the package must be public: after the first push, set its visibility to public in the package's settings on GitHub, once.

```sh
gh workflow run build.yml --ref main
gh workflow run deploy.yml -f environment=whatever-you-do-staging -f tag=latest
```

`tag` may be a commit, a `v*` tag or `latest`. The workflow resolves it to a digest, opens the tunnel, checks the host's tier, applies the environment's secrets, installs cert-manager and the issuers if the host lacks them, installs or upgrades the environment, and then asks `https://<hostname>/healthz` which commit is answering. It fails if that is not the commit it deployed.

A deploy runs migrations. It does not publish a pathway: see "Publish a pathway" below.

## After the first deploy

On the host, as the operator. `k` is short for `sudo k3s kubectl -n <environment>`.

```sh
k exec -it deployment/anville -- python manage.py createsuperuser
k exec deployment/anville -- python manage.py seed_observers --help    # staging only
```

Then publish the environment's pathway, as below.

## Publish a pathway

```sh
gh workflow run publish-pathway.yml --ref main -f pathway=whatever-you-do.json -f environment=whatever-you-do-staging
```

Or on GitHub: Actions, `publish-pathway`, Run workflow. Choose the branch to publish from in "Use workflow from" (`--ref` above), then the pathway and the environment. The document is the one in `pathways/` on that branch, not the copy in the deployed image. The branch must hold the workflow, and the pathway list offered is the one in that branch's copy of it; GitHub cannot offer a list of branches any other way. It is sent into the environment's running pod and loaded there with `load_pathway`, so the deployed version checks it: a document that version cannot read is refused, and nothing changes. Publishing content that is already published changes nothing either. Each run waits for any deploy to finish first.

The pathway list is fixed in the workflow, since GitHub cannot list a directory for it. When a file is added to or removed from `pathways/`, change the workflow's `options` too: `check.sh`, and so the build workflow, fails until they match. The environment list is the repository's GitHub Environments, and one with no directory in `environments/` is refused.

Publishing is always this deliberate step. `load_pathway` publishes whatever file it is given, so run on every deploy it would overwrite a version published another way. Without GitHub, the same is `deploy/publish-pathway.sh <environment> <pathway>` with a tunnel and kubeconfig of your own, or on the host, with a copy of the document there:

```sh
k exec -i deployment/anville -c web -- sh -c 'cat > /tmp/p.json && python manage.py load_pathway /tmp/p.json' < pathways/whatever-you-do.json
```

## Day to day

```sh
k get pods
k logs deployment/anville                 # errors, and fake email
k logs deployment/anville -c migrate      # the last migration
k exec -it deployment/anville -- python manage.py changepassword <username>
k exec -it deployment/anville -- python manage.py dbshell
```

**k9s.** A terminal view of everything on the host: pods, logs, events, a shell in a container. After `ssh <operator>@<host>`, as the operator:

```sh
k9                              # every namespace
k9 --readonly                   # the same, changing nothing
```

`k9` is an alias in the operator's `~/.bashrc`, for `sudo k9s --kubeconfig /etc/rancher/k3s/k3s.yaml -A`. It runs through `sudo` since the kubeconfig is root's alone, and names the kubeconfig because `sudo` drops `KUBECONFIG` and root has no `~/.kube/config`; `k3s kubectl` finds it by itself, k9s does not.

Inside, `:ns` lists the namespaces (Enter on one narrows the view to it), `:pods` the pods, `l` shows a pod's logs, `s` opens a shell, `?` lists the keys and `:q` quits.

A host gets k9s and the alias on its first boot, from `infra/install-k9s.sh`. A host made before that, such as `anville-staging-01.vabl.dev`, gets them the same way, from a checkout on your own machine:

```sh
ssh <operator>@<host> 'sudo bash -s' < deploy/infra/install-k9s.sh
```

It installs the pinned release after checking its checksum, unless that version is already there, and gives the account that ran `sudo` the alias, replacing an earlier `k9` alias rather than adding a second. Unattended upgrades do not update it: to change the version, edit the version and the two checksums at the top of the script and run it on each host the same way.

**Fake email.** An environment with no `EMAIL_URL` secret delivers nothing: each message is written to the pod's log. On a staging environment it is written with the test-system disclaimer it would carry if it were sent: `[TEST]` before the subject, and the disclaimer at the top of the body. To see one, run `k exec deployment/anville -- python manage.py sendtestemail someone@example.com` and read the log. The log then holds whatever links the messages carried, which is acceptable only where the data is fake. A production environment cannot be deployed without `EMAIL_URL`.

**Resetting a password.** Password reset is refused until ticket 28a. Until then the operator runs `changepassword`, as above. allauth derives the username from the start of the email address; the admin shows it.

**Changing a secret.** Change it in the GitHub Environment and deploy again. The pods restart only when a secret has changed. `POSTGRES_PASSWORD` is the exception: PostgreSQL reads it once, when its data is first created.

## Backups

With `backup.enabled`, a CronJob dumps the database each night, checks that the dump can be read back, and sends it over SFTP to `BACKUP_TARGET`, keeping the newest 30. To run one now:

```sh
k create job --from=cronjob/anville-backup backup-now
k logs job/backup-now --follow
```

### Rehearse a restore

Into a scratch namespace on a host of the same tier. A production dump is never restored onto a staging host.

```sh
# 1. Fetch a dump from the Storage Box onto the host.
sftp -P 23 <sub-account>@<sub-account>.your-storagebox.de:<environment>-<time>.dump /tmp/restore.dump

# 2. A scratch environment: the same image, no hostname, so no ingress and no certificate.
DIGEST=$(sudo k3s kubectl -n <environment> get deployment anville -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d@ -f2)
sudo k3s kubectl create namespace restore-test
sudo k3s kubectl -n restore-test create secret generic anville \
  --from-literal=DJANGO_SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -hex 32)"
```

The chart is installed with Helm, which is not on the host. From your own machine, with a copy of the host's kubeconfig and a tunnel of your own (`ssh -N -L 6443:127.0.0.1:6443 <you>@<host>`):

```sh
helm install anville deploy/chart/anville --namespace restore-test --set image.digest=$DIGEST \
  --set enrolment.required=false --wait
```

Then, on the host again:

```sh
# 3. Restore over the empty tables the migration made.
r="sudo k3s kubectl -n restore-test"
$r cp /tmp/restore.dump anville-postgres-0:/tmp/restore.dump
$r exec anville-postgres-0 -- pg_restore --clean --if-exists --no-owner -U anville -d anville /tmp/restore.dump

# 4. Look at it. From your own machine, through the tunnel: http://localhost:8000
kubectl -n restore-test port-forward service/anville 8000:80

# 5. Remove it, and the dump.
sudo k3s kubectl delete namespace restore-test
rm /tmp/restore.dump
```

Sign in as someone who exists in the dump and check that their answers are there.

## Check before committing

```sh
deploy/check.sh
```

It needs `shellcheck` 0.11 (`pip install shellcheck-py==0.11.0.1`; versions differ in what they flag), `helm` and `yq`. It renders the chart with every environment's values, and checks that `publish-pathway.yml` offers exactly the files in `pathways/`. The build workflow runs it, with that same shellcheck, before building an image. That check deploys nothing.

## What has been tested

Without a host, a registry push or Docker, as far as each piece allows:

- `hcloud-create.sh`: run end to end against a local stand-in for the Hetzner API, through a named context, including each refusal (no such context, `HCLOUD_TOKEN` set, a name that resolves, a name already a server's, a name that is not fully qualified or does not name its tier); the rendered cloud-init passes cloud-init's own schema check.
- The charts: installed into a real Kubernetes API server with no node, so every object was accepted and no pod ran.
- `deploy.sh`: run against that same API server, including each refusal (missing secrets, wrong tier, a node labelled as another host or not at all, values naming no host, a password unfit for a URL). Its cert-manager step pulled the pinned chart from quay.io and installed it there: the six definitions and three deployments were accepted. It could go no further without a node, since cert-manager's own start-up check is a job, and the issuers were refused, as they should be, while its webhook was not running.
- `tunnel.sh`: run through a local SSH server to that API server, including a wrong host key and a wrong key.
- `resolve-image-digest.sh`: run against another public image on GitHub Container Registry.
- `assert-version.sh`: run against gunicorn serving this repository.
- `publish-pathway.sh`: run with `kubectl` stubbed to run the pod's command here, against a throwaway database: a first publish, the same again (no change), another document, a broken one (refused, nothing published), and names that are not an environment or a pathway. `kubectl exec` carrying the document to a real pod is not yet proven.
- `install-k9s.sh`: run with `apt-get` stubbed, through `bash -s` as above: it fetched the pinned arm64 package, checked it, and left standard input to the script; it refused a wrong checksum, a user other than root and an operator with no account; it added the alias once, replaced an earlier one, and did nothing the second time. The amd64 package's checksum was checked by hand. The rendered cloud-init carries the script byte for byte.
- The backup script: run against a local SFTP server, with `pg_dump` stubbed.

Not yet proven anywhere: the `Dockerfile` as a Docker build, the cloud-init on a real first boot, the deploy key's restriction in `authorized_keys`, cert-manager starting and issuing a certificate, a pod starting, a real dump, and the restore above.
