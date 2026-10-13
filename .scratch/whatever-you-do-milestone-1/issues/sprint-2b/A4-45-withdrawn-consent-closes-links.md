# 45: Withdrawn consent closes observers' and the coach's links

**What to build:** While a participant's consent is withdrawn, the links they gave out stop working: an observer can neither open, claim nor send through theirs, and the coach's link shows nothing, the results and comparison included. Today withdrawing only closes the pathway to the participant. An observer can still claim a link and send an assessment, which stores new data about someone who has withdrawn, and a coach whom the participant had let see their results still sees them (checked on 6 Oct).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct); before any real participant data

**Spec:** Consent (user story 6); Observers (ADR 0005); Coach (ADR 0011); Legalities are parked, not forgotten

- [ ] While the participant has withdrawn, an observer's link and an observer's own link, by address or by cookie, get the one refusal a wrong, expired or revoked link gets, naming nobody: no landing page, no claim, no assessment sent
- [ ] While the participant has withdrawn, the coach's link gets the same refusal: no commitments to accept or decline, and no results or comparison, whatever the participant had ticked
- [ ] Giving consent again opens the links again, as they were: an unexpired link that was not revoked works, a claim made before still holds, and answers already sent still count. Withdrawing changes no link's expiry
- [ ] Journey tests cover each of the above, beside the existing ones in `tests/journeys/test_consent.py`, `test_observer_landing.py`, `test_coach_link.py` and `test_coach_sees_results.py`
- [ ] The consent page says, where it offers withdrawal, that the participant's observers and coach can no longer use their links until consent is given again

**Decide while building** (record the call in the spec, as other developer's calls are)

- **Withdrawn, or merely not current?** A participant also has no current consent when the consent text's version is raised and they have not yet agreed again. Closing their links then too would cut off observers mid-answer whenever the text changes. Suggested: links close only when the participant's latest consent is withdrawn, not when it is merely out of date
- **Does the coach's sharing survive?** The consent to show the coach the results lives on the coach's link (ADR 0011). Suggested: it survives a withdrawal and a return, since the participant gave it separately and can untick it; the alternative is to clear it on withdrawal, so that returning asks again
- **The observer's own withdrawal.** When ticket 15b lets an observer withdraw their answers through their link, that must still work while the participant's consent is withdrawn: closing the link must never stop an observer taking back what they gave

**Context**

- Out of scope: what withdrawal does to stored answers, results, contacts and observers' assessments. Until a retention rule is decided, withdrawing keeps them all, and `test_withdrawing_keeps_the_answers_already_stored` pins that (spec, Legalities are parked; ticket 08)
- The refusal must look the same as for a dead link, so that a link reveals nothing about the participant's consent to whoever holds it
- `Invitation.live` and `Invitation.claimed_by` in `engine/models.py` are the two places every observer's and coach's view finds its invitation; `access.consent` says whether consent stands
