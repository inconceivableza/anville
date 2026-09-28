# 08: Age confirmation and consent

**What to build:** Adults-only access and explicit consent (ADR 0004). A participant confirms they are 18 or over with a checkbox (no date of birth is stored) and gives explicit consent before any answer is stored, separately from enrolment. Declining stores nothing beyond the account, and consent can be withdrawn later.

**Blocked by:** 04 (Hub, locks, gates and explicit completion)

**Status:** resolved

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [x] An 18+ checkbox is required and no date of birth is collected or stored
- [x] A consent step precedes any pathway access; it records the version of the consent text and a timestamp, and is separate from the enrolment code
- [x] Declining consent stores nothing beyond the account and prevents answering
- [x] Consent can be withdrawn later from the participant's account
- [x] A change in the meaning of the consent text (a new version) asks participants again
- [x] Journey tests: declining stores no answers; enrolment alone never counts as consent; the 18+ confirmation is enforced
- [x] Note: until this ticket lands, earlier tickets store fake-data answers with no consent step. That is acceptable only on fake data; no real participant's data goes into any instance before consent, a named controller and a retention rule exist. The consent text itself needs writing before real use (see spec Further Notes) (consent now precedes every answer; the firm line and writing the text stay on the spec's "Legalities are parked" list, where the text's draft status is now noted)

## Comments

- First step: the 18+ checkbox is on the sign-up form, beside the enrolment code, and is not stored. Asking at sign-up rather than at the consent step means an under-18 never gets an account, so nothing about them is kept, not even an email. Google sign-up (ticket 28b) can go through the same form, but only once allauth's automatic social sign-up is off (found in review; carried to 28b). The journey test for enforcing it is in; the other journey tests follow with consent. The box sits just above the button, without Django's colon; the sign-in "Remember me" lost its colon and title case to match.
- Second step: the consent page at `/consent/`, and every engine view waits for it beneath `login_required`. Agreeing records a `Consent` row with the text's version and time, and is refused if the version the page showed is no longer current. Declining records nothing, not even the decision. The version lives beside the text in `access/consent.py`. The text is a marked draft with no controller, retention period or withdrawal effect, since all three are undecided. The journey tests' shared sign-in fixtures now give consent, and the tests clear the cache before each test, because allauth's 20-a-minute sign-up limit outlived the database and refused a later test's sign-up.
- Third step: withdrawing and a new version. There is no account page yet, so "Your consent" at the foot of the hub leads to `/consent/`, which offers "Withdraw my consent" once agreed. Withdrawing stamps `withdrawn_at` on every standing agreement and the pathway waits for consent again. Stored answers are kept (Ryan's call): what withdrawal does to them is open, and a test pins today's behaviour so a change to it is deliberate. Raising `CONSENT_TEXT_VERSION` in `access/consent.py` asks everyone again, and the page says which version they last agreed to.
- Review (`/code-review` over the three steps): the draft text said "the app", which the glossary avoids, and docstrings said "agreement" for consent; both now use the glossary's words. The declining test now also pins that no consent row is written. The page looks up the current consent once. Left as they are: the two-line `_see_other` copied from the engine (Ryan's call), and, as recommended in review, the plain decision strings and the test that raises the version through `monkeypatch`, since no seam exists for "a release changes the text".

## Answer

All criteria are met. Nothing is handed over as unfinished work; two notes went elsewhere.

Built in `access/`: the 18+ field on the sign-up form (`forms.py`), the `Consent` model, `consent.py` (the text's version, the current consent, withdrawal, and the `consent_required` check every engine view carries beneath `login_required`), the `/consent/` view, and its two templates. The hub links to it. The README's "Age and consent" section describes the behaviour, and `docs/manual-checks.md` lists what to check by hand.

Decisions made along the way:

- The 18+ confirmation is asked at sign-up, not at the consent step, so an under-18 never gets an account and nothing about them is kept. It is not stored.
- Declining records nothing, not even the decision.
- Consent is to the version of the text the page showed. If the version changed while the page was open, agreeing is refused and the text shown again.
- Each consent is its own row, so consenting to a new version keeps the earlier record, and withdrawal stamps the rows rather than deleting them.
- Withdrawing keeps the participant's stored answers for now (Ryan's call), because what it should do to them is open. The page says so plainly, and a test pins it.
- Withdrawal is reached from "Your consent" at the foot of the hub, since there is no account page.
- The consent text is a visible draft, written for fake data, naming no controller or retention period.

Carried:

- 28b: Google sign-up must show the sign-up form, so the enrolment code and the 18+ confirmation apply to it too
- Spec, beside the consent decision: the "Your consent" link moves to an account page when one exists
- Spec, "Legalities are parked": withdrawal keeps answers until deletion on withdrawal is decided; the consent text is a marked draft, and replacing it means raising `CONSENT_TEXT_VERSION`
