# 122: How many observers have answered is counted without reading their answers

**What to build:** Counting the observer answers that count toward the minimum becomes one database count, rather than loading and decoding every observer's assessment to count the ones that hold a card seen. Nothing anyone sees changes: the same answers count, toward the minimum, the freeze, the voices card and the comparison's numbers. Raised by the code review of sprint 3d (23 Nov); for after sprint 3d.

**Blocked by:** None (can start immediately)

**Status:** needs-triage

**Sprint:** 3 or later

**Spec:** Observers and the comparison (the minimum number of answers, "Haven't seen this", an observer who saw nothing has declined, ticket 120)

- [ ] `ObserverResponse.counted` is a single `COUNT` query, with no assessment loaded into Python
- [ ] It counts exactly what it counts today: sent answers with at least one card in a scored bucket, never a draft, a decline or a withdrawn answer
- [ ] That stays true for every way an observer answer is written: `ObserverResponse.send`, the demo shortcut (`engine/demo_shortcuts.py`), `seed_observers` and the migrations, so an answer with nothing seen can never be counted
- [ ] The comparison still reads the assessments themselves, through `assessments_for`, the one place that needs them
- [ ] A participant page shows the same counts with fewer queries; a test pins the number of queries the hub makes for a participant with several observers, as a guard

**Context**

- Today (`engine/models.py`, `ObserverResponse.counted`): `len(cls.assessments_for(response).assessments)`. `assessments_for` loads every sent assessment of the response, each a JSON sort of 72 cards in *Whatever You Do*, and keeps those that `counts()` (`engine/document/observers.py`): any card not in "Haven't seen this".
- It runs on every participant page, once in `Response.answers_with_contacts_and_visits` for the `observers_answered` clause, and again wherever a page shows the count through `_answered` (`engine/views.py`): the voices card, the comparison signpost and the results page's line about inviting people. It also runs in `look_at_comparison`, `freeze_collection`, `unfreeze_below_minimum` and the demo shortcut, often more than once a request. `MAX_CONTACTS` is 50, so a busy participant's page could decode dozens of assessments several times.
- Since ticket 120, `ObserverResponse.send` keeps an assessment with nothing seen as a decline (`declined_at` set, `submitted_at` and `assessment` empty), and migration `0032_observerresponse_declined_at` turned the earlier ones into declines. So every row sent through the app with `submitted_at` set already holds a card seen, and `filter(submitted_at__isnull=False).count()` would give today's number. The gap is the writers that skip `send`: `seed_observers` bulk-creates rows straight from `observer_assessment`, and the tests' `an_observer` helper does too.
- To weigh:
  - Rely on that invariant and route every writer through `send` (or check `counts()` in each), with a database constraint where one can be written; or store a `counts` flag beside the assessment when it is sent and count on it, which needs a migration to fill it for rows already stored.
  - Ticket 41d (load the participant once per page) would cut the repeated calls within a request too; the two can be done apart.
