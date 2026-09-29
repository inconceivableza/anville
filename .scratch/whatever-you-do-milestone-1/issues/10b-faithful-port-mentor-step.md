# 10b: Faithful port: the mentor step

**What to build:** The original prototype's "Walking with a mentor" screen in `pathways/whatever-you-do-faithful-port.json`, which ticket 10a left out while building the content owner's coach-selection flow in `pathways/whatever-you-do.json`. Split from ticket 10.

**Not necessarily needed.** This is only worth doing if the faithful port is still being compared with the pathway when the coach step matters. It may never be done. It has no sprint.

**Blocked by:** 10a (Onboarding completion)

**Status:** needs-triage

**Parent:** whatever-you-do-milestone-1 spec

- [ ] The faithful port's onboarding has the original prototype's mentor step: its heading and "What does a mentor do?" text, the mentor's name and email, the confirmation box, and a way to skip, using ticket 10a's coach block without its checklist
- [ ] Decide whether the port says "mentor", as the original prototype does, or "coach", as the spec asks of migrated wording
- [ ] Decide whether the original's email preview is kept: it promises an email the app does not send (the spec's story 61)
- [ ] The drift test in `tests/journeys/test_whatever_you_do.py` stops setting the coach block aside and expects the two documents' coach steps to differ only as intended
