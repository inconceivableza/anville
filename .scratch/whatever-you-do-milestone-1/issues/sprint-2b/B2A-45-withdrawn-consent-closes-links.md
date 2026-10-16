# 45: Withdrawn consent closes observers' and the coach's links

**What to build:** While a participant's consent is withdrawn, the links they gave out stop working: an observer can neither open, claim nor send through theirs, and the coach's link shows nothing, the results and comparison included. Today withdrawing only closes the pathway to the participant. An observer can still claim a link and send an assessment, which stores new data about someone who has withdrawn, and a coach whom the participant had let see their results still sees them (checked on 6 Oct).

**Blocked by:** B1A-15b (The observer's relationship and withdrawal)

**Status:** resolved

**Sprint:** 2b (12–16 Oct); before any real participant data

**Spec:** Participants, access and consent (ADR 0004); Observers (ADR 0005); Implementation Decisions › Coach; Legalities are parked, not forgotten

- [x] While the participant has withdrawn, an observer's link and an observer's own link, by address or by cookie, get the one refusal a wrong, expired or revoked link gets, naming nobody: no landing page, no claim, no assessment sent. An observer can still withdraw their own answers through their claimed link
- [x] While the participant has withdrawn, the coach's link gets the same refusal: no commitments to accept or decline, and no results or comparison, whatever the participant had ticked
- [x] Giving consent again opens the links again, as they were: an unexpired link that was not revoked works, a claim made before still holds, answers already sent still count, and the coach still sees what the participant had shared. Withdrawing changes no link's expiry
- [x] Only a withdrawal closes the links: a participant whose consent is merely out of date, because the consent text changed and they have not yet agreed again, keeps them working
- [x] The consent page says, where it offers withdrawal, that the participant's observers and coach can no longer use their links until consent is given again

**Context**

- Out of scope: what withdrawal does to stored answers, results, contacts and observers' assessments. Until a retention rule is decided, withdrawing keeps them all, and `test_withdrawing_keeps_the_answers_already_stored` pins that (spec, Legalities are parked; ticket 08)
- The refusal must look the same as for a dead link, so that a link reveals nothing about the participant's consent to whoever holds it
- Where answer collection is also frozen (B2B-55), this refusal shows, never the frozen page. Whichever of 45 and 55 lands second makes it so
- `Invitation.live` and `Invitation.claimed_by` in `engine/models.py` are the two places every observer's and coach's view finds its invitation; `access.consent` says whether consent stands
- The journey tests go beside the existing ones in `tests/journeys/test_consent.py`, `test_observer_landing.py`, `test_coach_link.py` and `test_coach_sees_results.py`
