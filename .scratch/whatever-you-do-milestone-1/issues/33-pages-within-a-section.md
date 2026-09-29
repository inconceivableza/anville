# 33: Pages within a section

**What to build:** An author can split a section into pages, so a section plays as the prototype's screens do, one after another with "Continue →" between them, while the hub still shows it as one section. Onboarding is the first to use it: the reason and the starting ratings, then "Walking with a coach" (in `whatever-you-do.json` only), then "Who knows you best?", each on a page of its own, as the original prototype goes from its baseline screen to its mentor screen to its contacts screen.

**Blocked by:** none (04 is resolved)

**Status:** claimed

**Sprint:** 1 (ends 2 Oct)

**Parent:** ticket 10a (the developer's call, 2026-09-29, after the coach checklist landed on one long onboarding page)

- [ ] A section's pages are authored content in the pathway document, checked by the schema and the linter; a section without any is one page, exactly as now
- [x] Each page but the last ends in "Continue →" to the next; the last ends in the section's own completion button (`complete_label`), as now
- [x] Going on from a page needs that page's gate clauses to pass, checked on the server; its unmet clauses show beneath its "Continue →" as the section's checklist does now. Completing the section still checks the whole gate
- [x] A page cannot be reached, shown or answered before the pages ahead of it have been gone through, whatever the address typed, as a lock or an unconfirmed reading holds what follows it now
- [x] The hub shows one entry per section, as now, and leads to the page the participant has reached
- [x] A participant can go back to an earlier page of a section they have not completed
- [x] Works without JavaScript: each page is a plain page with its own address, and going on is a plain form
- [ ] Onboarding is split into pages in both pathway documents; the drift test in `tests/journeys/test_whatever_you_do.py` still holds them together
- [ ] Progress, estimates and fixed answers are unchanged: a section's estimate covers all its pages, and progress counts its blocks wherever they sit
- [ ] Manual checks and the README cover pages

**To decide at the start**

- How pages are authored: a `page_break` block between blocks, or a `pages` list in place of `blocks`. The first changes no existing document; the second states each page whole and may suit the studio's forms better (tickets 11 and 24)
- Whether a page has a title of its own, and whether the page counts ("1 of 3") are shown
- Whether a gate clause belongs to the page of the block it names (so nothing new is authored), or a page carries its own clauses
- Whether having gone on from a page is stored, or worked out from the answers each time. Working it out keeps nothing new, but a page whose clauses pass with nothing on it (the coach step, a contact list left empty) would then never hold anyone back, so a participant could land on the last page directly. Storing it follows the prototype's screens more closely
- Whether going on from the ratings' page fixes them, as the prototype's baseline screen cannot be returned to after "Continue" (ticket 29), or they stay changeable until the section is completed, as now
- Where the coach checklist's steps and its no-JavaScript fallback land once it has a page of its own (ticket 10a's `/coach/<block>/` returns the whole section page)
- Whether the reason for taking the course gets a page of its own, as it had the prototype's account screen, or shares the first page with the ratings

## Comments

- Decided with the developer (2026-09-29): pages are authored as a `page_break` block between blocks, so no existing document changes. Having moved past a page is stored, not worked out, so the coach step and an empty contact list still hold the participant until "Continue →". The start ratings stay changeable until the section is completed, as now. A page has no title of its own and no page count; the section's title heads every page. Taken as defaults: a gate clause belongs to the page of the block it names, and one naming a block in another section to the last page; the coach checklist's no-JavaScript fallback renders the page it is on; the reason shares the first page with the ratings; page 1 is `/sections/<id>/` and each page is also `/sections/<id>/pages/<n>/`.
- First step: the `page_break` block in the schema, and the linter's refusal of a break that would leave a page empty. The gate can be checked page by page, with the last page's checklist also listing anything left unmet on an earlier one, since completing still checks the whole gate. The hub works out the page each participant has reached from the pages they have moved past. Nothing is stored or shown yet.
- Second step: each page has its own address (`/sections/<id>/pages/<n>/`, page 1 staying `/sections/<id>/`) and, but for the last, ends in "Continue →", a plain form posted to `…/continue/` and checked on the server against that page's clauses ("This page is not finished yet." when refused). Moving past a page is stored on the response as `pages_moved_past` (named by the developer). A page not reached is shut to a typed address, an autosave, a coach checklist step and completion alike, each leading back to the page reached; earlier pages stay open, with "← Back" beneath the way on rather than beside it as in the prototype, so the primary button stays put. The hub, section links and a result's way back lead to the page reached. Still open: `move_past_page` checks only the page's clauses, so a hand-made request could move past a page whose scripture reading is unconfirmed (the button is not offered there, and what the reading holds stays shut on the next page); a test and refusal come in the third step.
