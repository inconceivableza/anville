# Runbook for staging deployment

## Overview

Running on macos host eochaid
Going through deploy/README.md and .scratch/whatever-you-do-milestone-1/issues/26-staging-deployment.md human steps in parallel

From the 26-staging-deployment git branch
Starting with commit a7b90b94f6 - docs: say why each environment has its own PostgreSQL, and what sharing one would take

_Phase 1: 2026-10-07 19:25 SAST_

## Initial machine creation

* Manual step: Created Anville project in Hetzner Console
* hcloud install:
  - `brew install hcloud  # 1.70.1`
* keygen
  - `ssh-keygen -t ed25519 -N "" -C "anville deploy" -f ~/.ssh/anville-deploy`
* Created hetzner cloud token:
  - console.hetzner.com -> project Anville -> security -> create API token -> Read & Write
  - `HCLOUD_TOKEN=....`
* Stored HCLOUD_TOKEN and anville-deploy key in bitwarden

Decided to use Anville project and canonical hostname

Moved to commit dfd8402bb7 - feat: give each host a canonical name, and create it in a named Hetzner project

* Creation of server:
  - `hcloud context create anville`
  - `ADMIN_USER=vabl ADMIN_SSH_KEY_FILE=~/.ssh/id_ed25519.pub DEPLOY_SSH_KEY_FILE=~/.ssh/anville-deploy.pub deploy/infra/hcloud-create.sh anville anville-staging-01.vabl.dev staging`
  - Output: anville-staging-01.vabl.dev is created in the Hetzner project anville, at 46.225.157.209
  - Created anville-staging-01.vabl.dev record on cloudflare, pointing to 46.225.157.209
  - `host anville-staging-01.vabl.dev` or `dig +short anville-staging-01.vabl.dev @beau.ns.cloudflare.com` gives 46.225.157.209
  - can ssh into vabl@anville-staging-01.vabl.dev
  - `sudo kubectl get pods` gives _No resources found in default namespace._

## Environment Setup

* Existing `environments/whatever-you-do-staging/values.yaml` is already correct
* Created StorageBox backup account on Hetzner
* Filled in GitHub secrets based on secrets.example.yaml

## Build

* Pull request and merge into main
* Ran build workflow

## Deploy

* Ran deploy workflow
* Had to add environment variable (not secret) `DEPLOY_HOST` set to `anville-staging-01.vabl.dev`
* Also set `ACME_EMAIL` to `beta@vabl.dev`
* Had to publish anville package as public
  - Had to set https://github.com/organizations/inconceivableza/settings/packages to allow public packages
  - Changed visibility at https://github.com/orgs/inconceivableza/packages/container/anville/settings
* Ran deploy workflow again
* Had to create CNAME for `anville.vabl.dev` pointing to `anville-staging-01.vabl.dev`
* Ran deploy workflow again
* Don't have `k9s` on the host; it would be useful for inspecting pods etc

## Testing

* Checked that Anville is reachable at https://anville.vabl.dev/
* Signing up with fake email address worked as expected; no pathway loaded yet

## Publish Pathway

_Phase 2: 2026-10-08 10:30 SAST_

* There wasn't an automated way to publish the pathway, so that was added during this run
* Pull request #2 was merged containing this feature
* Now working from "d8e371eefb - Merge pull request #2 from inconceivableza/26-staging-deployment"
* Deleted `DEPLOY_HOST` environment variable from `whatever-you-do-staging` environment as no longer needed
* Ran the `publish-pathway` workflow through GitHub actions
* Verified that that pathway is now active on the web interface at https://anville.vabl.dev/hub/

## Supporting k9s

* k9s is convenient for the operator
* In "253dccffb7 - feat: install k9s on each host for the operator", a script was added to auto-install in cloud-init
* Ran this manually with `ssh vabl@anville-staging-01.vabl.dev 'sudo bash -s' < deploy/infra/install-k9s.sh`
* Also manually set `alias k9='sudo k9s --kubeconfig /etc/rancher/k3s/k3s.yaml'` and added to vabl's .bashrc

## Create the operator superuser

* ssh into the host as vabl@anville-staging-01.vabl.dev
* `sudo k3s kubectl -n whatever-you-do-staging exec -it deployment/anville -- python manage.py createsuperuser`
* Created superuser as `anville`, with developer's email address
* Password in Bitwarden
* Tested login to https://anville.vabl.dev/admin/ works
* Decided afterwards that the operator's account should reach the admin only, so it wants no email address at all: sign-in to the site is by email, so a blank one leaves `/admin/` reachable, where Django's own backend takes the username, and the hub not. That keeps the operator out of the participants' consent and answers, and leaves developer's address free to sign up with, since no participant can use an address another user already holds
* So `deploy/README.md` now says to create it as `createsuperuser --username operator --email ""`
* Cleared the email address that was set for the superuser through the admin interface

## Email Setup

* Ran on server: `sudo k3s kubectl -n whatever-you-do-staging exec -it deployment/anville -- python manage.py sendtestemail someone@example.org`
* That shows test output as expected
* Cleared the email address on the `anville` superuser, so it reaches the admin only (see "Create the operator superuser")
* Set up `EMAIL_URL` as a GitHub secret in the envioronment, and set `email.from` and `email.disclaimer` in the staging environment's `values.yaml` in this repository
* Tested email works via /accounts/email/ (which isn't obvious)

## Backup and Restore

* Database backup was failing when run on schedule, with
  - pg_dump: error: connection to server at "anville-postgres" (10.42.0.16), port 5432 failed: Connection refused
  - Is the server running on that host and accepting TCP/IP connections?
* Adjusted to wait until the pod can get through for up to two minutes
* Deployed new version: still dies with "Connection closed", but does run the backup OK
* Had to turn on SSH on main box, and also for better security, Need to still:
  - Add subaccount
  - Set up password
  - Copy new public key to password
  - Set new private key in GitHub secret
* Above not working yet