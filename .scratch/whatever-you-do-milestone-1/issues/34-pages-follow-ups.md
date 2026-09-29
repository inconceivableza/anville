# 34: Pages follow-ups

**What to build:** What ticket 33's code reviews left: stop a held link on an earlier page from leaving a participant on a blank page, test the routes to the page reached that only the hub's covers, and tidy the views and gate code around pages. Nothing a participant sees in a shipped pathway today changes.

**Blocked by:** none (33 is resolved)

**Status:** ready-for-agent

**Sprint:** not yet placed

**Parent:** ticket 33 (its code reviews, 2026-09-29)

**Carried from 33**

- [ ] A held link on an earlier page can leave a blank page. Section X is a link holding for section Y, a page break, then an activity; the participant passes Y's gate, continues past X's page 1, then changes Y so its gate fails. The hub still leads to X's page 2, which `open_blocks` leaves with only the title and "← Back": no blocks, no way on, and no reason. Send the participant to the page of the block holding them instead, with a test. No shipped section has a held link before a page break
- [ ] Before there is a result, `results()` redirects to the section's first page, not to the page the sort is on; fix it when a pathway puts a sort past a first page, with a test. (Once there is a result, its "← Back" leads to the sort's own page, which is right: a participant with a result has reached it)
- [ ] Only the hub's way to the page reached is tested; a section link (`section_link.html`) and completion's next step (`complete_section`) lead there too, untested. Scenario: complete section A while section B is reopened at page 2
- [ ] The last page's checklist lists messages left unmet on earlier pages after its own, not in the order authored (cosmetic; `test_going_back_to_select_asks_for_a_reason_again` records the current order)
- [ ] The lock and page-reached guard is repeated in `section`, `move_past_page`, `complete_section` and `_is_open` (`engine/views.py`); `moved_past.get(…, ())` is spelled out four times there and once in `hub_for`. Gather it in one place
- [ ] `_section_page` and `_saved` take eight positional arguments each, and `_participant` returns a five-tuple unpacked as `_, _, _`; a small participant-state object would carry them
- [ ] `clauses_of` and `checklist` in `engine/document/gates.py` each work out a clause's page (`page_of(section, clause["block"]) or last`); give that rule one home. The view also picks the last page for `unmet` while `checklist` picks it inside the gates
- [ ] `block["type"] == "page_break"` is checked in `pages_of`, `open_blocks` (which splits pages itself rather than calling `pages_of`), `_empty_pages` and the test helper `without_the_coach_step`; and `len(pages_of(section))` is repeated across views, gates and hub, which a `page_count(section)` could replace
- [ ] `page` means a page number almost everywhere, but still names the template's content in `coach_checklist` and `results`; rename those to `shown` as elsewhere. `offers_completion` now also means "offers Continue →"; a name such as `offers_way_on` would say so
- [ ] `page_url` lives in `engine/templatetags/section_pages.py` and is imported by the views; move it beside the views, with the tag wrapping it
- Judgement calls from the review, to weigh rather than do: `pages_moved_past` keys are `"<section>/<page>"` strings split apart again with `rpartition` (a nested `{section: [pages]}` would avoid the encoding, but needs a migration of stored rows); `page_break` is registered as a block type though it is never shown, takes no estimate and no clause may name it
- Answers and coach checklist steps on a page not reached are refused (403), as behind a lock or an unconfirmed reading, not led back to the page reached as a typed address and completion are. Decided with the developer after the review: the README says "refused"; ticket 33's second-step comment said otherwise
- A refused "Continue →" stays on the `…/continue/` address, as a refused completion does, so refreshing offers to resend the form; the manual checks say so
