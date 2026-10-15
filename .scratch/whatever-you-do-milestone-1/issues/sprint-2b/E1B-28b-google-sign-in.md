# 28b: Google sign-in

**What to build:** A participant may sign up and sign in with their Google account, alongside email and password, in any environment given a Google client. Split from ticket 28; password reset is 28a.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Participants, access and consent (ADR 0004); Out of Scope; Legalities are parked, not forgotten

- [ ] A participant can sign up and sign in with Google, alongside email and password
- [ ] The Google button appears only in an environment given both a client ID and a secret; an environment without them is unchanged, so one may offer Google sign-in while another does not
- [ ] Signing up through Google still asks for the 18+ confirmation, and for the enrolment code where the deployment asks for one (ticket 37); a Google sign-up without either gets no account
- [ ] A Google account passes the consent step before any answer is stored, as any other account does (ADR 0004)
- [ ] The deployment instructions' "Set up Google sign-in", already written, matches what is built: the setting names, where the client pair goes, and the line saying it arrives with this ticket goes. The client pair is listed among the environment's optional secrets

**Context**

- Trying it on staging needs a Google OAuth client for the environment, which an operator creates by hand, as `deploy/README.md`, "Set up Google sign-in", describes. The code and its tests do not wait on it
- Google may process participants' sign-in data, by their own choice each time (ADR 0015)
- Through allauth's social accounts. Its social sign-up form is built on the sign-up form's own class (`access/forms.py`), which holds the 18+ confirmation and the enrolment code, but by default allauth skips the form altogether (`SOCIALACCOUNT_AUTO_SIGNUP = True`): turn that off, or otherwise make social sign-up show it
- The consent step guards the engine's views (`access/consent.py`), not sign-up, so it holds for a Google account either way
- The button follows the pattern by which `EMAIL_URL` turns real email on (`config/settings.py`). The pair goes in `secrets.example.yaml`
- Participants need their own Google account to use the button. Nobody is shut out by that, since email and password stays alongside it
- The authorised domains on the Branding page have to be verified in Search Console by the account that owns the project, before the app can be published. Doing that for `vabl.dev` once covers every environment under it
- A domain verification and a brand verification are different things. The first is needed to publish; the second only if a logo is set, which the instructions avoid
- Not in this ticket: Google as a processor in Anville's privacy notice, which follows from the ADR, and belongs with the legalities the spec parks
