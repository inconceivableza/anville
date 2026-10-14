# 28b: Google sign-in

**What to build:** A participant may sign up and sign in with their Google account, alongside email and password, in any environment given a Google client. Split from ticket 28; password reset is 28a.

**Blocked by:** C1-28a (Password reset)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Participants, access and consent (ADR 0004); Out of Scope; Legalities are parked, not forgotten

- [ ] A participant can sign up and sign in with Google, alongside email and password
- [ ] The Google button appears only in an environment given both a client ID and a secret; an environment without them is unchanged, so one may offer Google sign-in while another does not
- [ ] Signing up through Google still asks for the 18+ confirmation, and for the enrolment code where the deployment asks for one (ticket 37); a Google sign-up without either gets no account
- [ ] A Google account passes the consent step before any answer is stored, as any other account does (ADR 0004)
- [ ] The deployment instructions say how to set up Google sign-in for an environment, beside how to set up email, holding the steps below, and list the client pair among the environment's optional secrets

**Setting up the Google project**

One Google Cloud project for Anville, and one OAuth client within it per environment. The project needs a Google account to own it, but no billing account and no API to enable: signing in uses OpenID Connect, which is not a billed API, so nothing here is charged. A plain Google account is enough; a Workspace account is needed only for the "Internal" audience, which Anville cannot use, since participants are not members of an organisation.

The account that owns the project controls sign-in for every environment that uses it. It should be an account the church holds, not a volunteer's personal one, and a second owner should be added so that it survives one person leaving.

The console's names for these pages have moved: what follows is under **Google Auth Platform**, which was "APIs & Services → OAuth consent screen", and clients are also still listed under "APIs & Services → Credentials". The labels quoted are the console's own, in its spelling.

1. **The project.** In the Cloud Console, the project picker, then "New project". Name it for Anville, not for one environment, since every environment's client lives in it.
2. **Get started.** Google Auth Platform asks for the app name, a user support email, the audience and a developer contact address before it will show anything else. The app name is what a participant sees on Google's consent page: "Sign in to continue to <app name>". Choose **External** as the audience; "Internal" is offered only to a Workspace organisation.
3. **Branding.** The same app name and support email, and the links Google shows beside them. Give the home page, the privacy notice and the terms, all on a domain listed under "Authorized domains" — for staging, `vabl.dev`. The links are optional while the app is in testing, and required to publish it. **Leave the app logo empty:** a logo is the one thing on this page that sends the app for brand verification, which is a review measured in days, and the consent page reads perfectly well without one.
4. **Audience.** It starts in "Testing", which admits only the accounts listed as test users — at most 100 — and whose sign-ins expire after about a week. That is the right state for staging, with the testers' own addresses listed. "Publish app" moves it to production, for anyone with a Google account; with only the scopes in step 5 that needs no review from Google and takes effect at once.
5. **Data access.** Add `openid`, `.../auth/userinfo.email` and `.../auth/userinfo.profile`, which is all allauth's Google provider asks for and all Anville needs. All three are non-sensitive, which is what keeps the app out of verification. Anything more — a sensitive or restricted scope — would need a review, and none of it is wanted here.
6. **Clients.** "Create client", of type **Web application**, named for the environment it belongs to. Under "Authorized redirect URIs" give exactly `https://<hostname>/accounts/google/login/callback/` — `https://anville.vabl.dev/accounts/google/login/callback/` for `whatever-you-do-staging`. Google matches these exactly, so the trailing slash matters. "Authorized JavaScript origins" stays empty: the exchange is made by Django, not by the browser.
7. **The secret.** Creating the client shows the client ID and the client secret, and the secret is shown in full only then. Put both straight into the environment's GitHub Environment (below). A secret that has been lost is replaced, not recovered.
8. **A client for development,** if wanted: a second client in the same project, with `http://localhost:8000/accounts/google/login/callback/` as its redirect URI. Google allows plain HTTP for `localhost` alone, and the port must match what `runserver` is using.

Repeat steps 6 and 7 for each new environment. One client could carry every environment's redirect URI instead, but a client per environment follows the rule `secrets.example.yaml` already states — every secret generated afresh for the environment, none reused — and means a staging leak does not reach production. Keep them in the one project: separate projects would mean a second branding page and a second domain verification for no gain.

**Where each choice goes**

| What | Where |
|---|---|
| The client ID and secret | `ANVILLE_GOOGLE_CLIENT_ID` and `ANVILLE_GOOGLE_CLIENT_SECRET`, secrets in the environment's GitHub Environment, listed as optional in its `secrets.example.yaml`. Both absent, there is no Google button; both present, there is |
| The redirect URI | The client itself, in the Cloud Console, from the environment's `hostname` in `values.yaml`. A hostname that changes needs the client changed to match |
| The app name, the support email and the links | The project's Branding page, once for every environment that shares the project |
| Who may sign in before the app is published | The project's Audience page, as test users |

**Context**

- Trying it on staging needs a Google OAuth client for the environment, which an operator creates by hand ("Setting up the Google project" above). The code and its tests do not wait on it
- Google may process participants' sign-in data, by their own choice each time (ADR 0015)
- Through allauth's social accounts. Its social sign-up form is built on the sign-up form's own class (`access/forms.py`), which holds the 18+ confirmation and the enrolment code, but by default allauth skips the form altogether (`SOCIALACCOUNT_AUTO_SIGNUP = True`): turn that off, or otherwise make social sign-up show it
- The consent step guards the engine's views (`access/consent.py`), not sign-up, so it holds for a Google account either way
- The button follows the pattern by which `EMAIL_URL` turns real email on (`config/settings.py`). The instructions go in `deploy/README.md` beside "Set up email", and the pair in `secrets.example.yaml`
- Participants need their own Google account to use the button. Nobody is shut out by that, since email and password stays alongside it
- The authorised domains on the Branding page have to be verified in Search Console by the account that owns the project, before the app can be published. Doing that for `vabl.dev` once covers every environment under it
- A domain verification and a brand verification are different things. The first is needed to publish; the second only if a logo is set, which step 3 avoids
- Not in this ticket: Google as a processor in Anville's privacy notice, which follows from the ADR, and belongs with the legalities the spec parks
