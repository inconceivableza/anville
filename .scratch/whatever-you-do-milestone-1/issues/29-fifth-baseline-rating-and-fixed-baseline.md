# 29: Fifth baseline rating, and baseline answers fixed once given

**What to build:** Two changes the content owner asked for after the first demo (25 Sept). First, a fifth baseline rating, "I am at peace with God's plan for my life", asked at the start and again at the end, to see whether a participant trusts God's plan more, not less, once they have been through the pathway. This deliberately diverges from the original prototype. `pathways/whatever-you-do.json` takes the change, and the faithful port (`pathways/whatever-you-do-faithful-port.json`) keeps the prototype's four, so the two can be compared once everything is built. Second, a participant cannot change their baseline ratings once given, as in the prototype, whose baseline screen cannot be returned to after "Continue".

**Blocked by:** none

**Status:** claimed

**Parent:** content owner's feedback on Demo 1 (25 Sept); not in the spec's slices

**Fifth rating**

- [x] `whatever-you-do.json` adds `bl-peace` after the four start ratings and `pl-peace` after the four end ratings, with the same anchors; the prototype-faithful document moves to `whatever-you-do-faithful-port.json`
- [x] Both gates need all five, with the message "Answer all five to continue"
- [x] A test fails if the two documents differ in anything but the fifth rating, so a change to one (such as restoring Section 3's `requires`) cannot silently miss the other

**Baseline fixed once given**

- [ ] An author can mark a rating as fixed once its section is complete; the `bl-*` ratings are marked so in both documents
- [ ] Completing the section fixes those answers; before then they can still be changed, as the prototype allows until "Continue"
- [ ] Reopening the section leaves them fixed, while its other blocks stay editable (ticket 10 adds the coach and contact list to onboarding, and a participant must be able to correct those)
- [ ] The server refuses a save to a fixed answer, whatever the page offered
- [ ] The section shows a fixed rating as chosen but not changeable, and no longer says "You can still change your answers here" where that is untrue
- [ ] The `pl-*` end ratings stay changeable unless the content owner asks otherwise

**Naming**

- [x] The glossary defines prototype (now general), original prototype, faithful port and content owner, and the pathway documents are named after them