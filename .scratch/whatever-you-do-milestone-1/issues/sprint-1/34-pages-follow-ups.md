# 34: Pages follow-ups

**What to build:** What ticket 33's code reviews left: stop a held link on an earlier page from leaving a participant on a blank page, test the routes to the page reached that only the hub's covers, and tidy the views and gate code around pages. Nothing a participant sees in a shipped pathway today changes.

**Blocked by:** none (33 is resolved)

**Status:** resolved

**Sprint:** 1 (ends 2 Oct)

**Parent:** ticket 33 (its code reviews, 2026-09-29)

**Carried from 33**

- [x] A held link on an earlier page can leave a blank page. Section X is a link holding for section Y, a page break, then an activity; the participant passes Y's gate, continues past X's page 1, then changes Y so its gate fails. The hub still leads to X's page 2, which `open_blocks` leaves with only the title and "← Back": no blocks, no way on, and no reason. Send the participant to the page of the block holding them instead, with a test. No shipped section has a held link before a page break
- [x] Before there is a result, `results()` redirects to the section's first page, not to the page the sort is on; fix it when a pathway puts a sort past a first page, with a test. (Once there is a result, its "← Back" leads to the sort's own page, which is right: a participant with a result has reached it)
- [x] Only the hub's way to the page reached is tested; a section link (`section_link.html`) and completion's next step (`complete_section`) lead there too, untested. Scenario: complete section A while section B is reopened at page 2
- [x] The last page's checklist lists messages left unmet on earlier pages after its own, not in the order authored (cosmetic; `test_going_back_to_select_asks_for_a_reason_again` records the current order)
- [x] The lock and page-reached guard is repeated in `section`, `move_past_page`, `complete_section` and `_is_open` (`engine/views.py`); `moved_past.get(…, ())` is spelled out four times there and once in `hub_for`. Gather it in one place
- [x] `_section_page` and `_saved` take eight positional arguments each, and `_participant` returns a five-tuple unpacked as `_, _, _`; a small participant-state object would carry them
- [x] `clauses_of` and `checklist` in `engine/document/gates.py` each work out a clause's page (`page_of(section, clause["block"]) or last`); give that rule one home. The view also picks the last page for `unmet` while `checklist` picks it inside the gates
- [x] `block["type"] == "page_break"` is checked in `pages_of`, `open_blocks` (which splits pages itself rather than calling `pages_of`), `_empty_pages` and the test helper `without_the_coach_step`; and `len(pages_of(section))` is repeated across views, gates and hub, which a `page_count(section)` could replace
- [x] `page` means a page number almost everywhere, but still names the template's content in `coach_checklist` and `results`; rename those to `shown` as elsewhere. `offers_completion` now also means "offers Continue →"; a name such as `offers_way_on` would say so
- [x] `page_url` lives in `engine/templatetags/section_pages.py` and is imported by the views; move it beside the views, with the tag wrapping it
- Judgement calls from the review, to weigh rather than do: `pages_moved_past` keys are `"<section>/<page>"` strings split apart again with `rpartition` (a nested `{section: [pages]}` would avoid the encoding, but needs a migration of stored rows); `page_break` is registered as a block type though it is never shown, takes no estimate and no clause may name it
- Answers and coach checklist steps on a page not reached are refused (403), as behind a lock or an unconfirmed reading, not led back to the page reached as a typed address and completion are. Decided with the developer after the review: the README says "refused"; ticket 33's second-step comment said otherwise
- A refused "Continue →" stays on the `…/continue/` address, as a refused completion does, so refreshing offers to resend the form; the manual checks say so

## Comments

- First step: `page_reached` now also reads the answers and the track's sections, and stops at the page of a block holding the rest shut, so the hub and every view guard lead a participant held again by a link back to the link's page. Before there is a result, the results address leads to the page the sort is on. The last page's checklist lists its messages and those left unmet on earlier pages in the order authored. A section link and completion's next step are tested leading to the page reached; the scenario is onboarding left part-way at page 2 beside an open calling section, since a reopened section has been completed and so has reached its last page. `test_going_back_to_select_asks_for_a_reason_again` compares a dict, which ignores order, so only the core checklist test records it.
- Second step: a `ParticipantState` in `engine/views.py` replaces `_participant`'s five-tuple and carries the fixed answers too; `_section_page`, `_saved` and `_is_open` take it. Its `reached(section)` is the one lock and page-reached guard, None while locked, and `stored_response(user)` begins a response on the first thing stored. `page_reached` now takes the pages moved past by section and looks up its own, so `moved_past.get(…, ())` is spelled out nowhere else; the core page-reached tests' helper passes it that way.
- Third step: `clauses_of` is the one place a clause's page is worked out, and the view takes `unmet` from the page's checklist, which on the last page already covers the whole gate. `page_count(section)` in `blocks.py` replaces each `len(pages_of(…))`, and `open_blocks` goes through `pages_of`. The linter's `_empty_pages` still checks `page_break` itself, since it reports each break's path, and so does the test helper `without_the_coach_step`. `shown` names the template's content in `coach_checklist` and `results`, `offers_completion` is `offers_way_on`, and `page_url` lives in `engine/views.py` with `section_pages.py` registering it as the tag.
- Code review: "Continue →" and completion on a section whose link holds again are tested leading back to the link's page. A participant's sections and a gate's last page are each worked out once. `unmet` no longer takes a page and always checks the whole gate; what a page needs comes from its checklist, and the page tests now read `clauses_of`.

## Answer

All ten carried items done. Decided with the developer: a participant held again by a link goes back to the link's page from the hub, a typed address, "Continue →" and completion alike, so completion is refused too, though the section's own gate passes. The section-link and completion tests use onboarding left part-way at page 2 rather than a reopened section, which has reached its last page.

Left as judgement calls from the review, with no owning ticket: the template tag imports `page_url` from `engine.views`, as this ticket asked; `engine/views.py` holds handlers, `ParticipantState` and `page_url`; `hub.py` still takes a participant's state in pieces.

This ticket's own two judgement calls were weighed with the developer and kept. `pages_moved_past` keeps its flat `"<section>/<page>"` keys: jsonb `||` merges top-level keys only, so the flat shape lets moving past a page stay one UPDATE, and the decoding lives in `moved_past_by_section` alone; a nested shape would need a different write and a migration of stored rows. `page_break` stays a registered block type: it gets the schema, unique identifiers and linting for free and changes no existing document, and the editor grows a block type at a time; pages as section structure would change the document format. Revisit if a second nested per-section record appears, or if the visual editor wants pages as their own thing.
