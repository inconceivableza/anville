# 05: Slice 1 content: baseline and calling-statement section

**What to build:** *Whatever You Do* content, authored in the pathway document from the prototype reference, that makes Demo 1 real: the four baseline ratings, one full section (scripture read-confirm, a long-text activity, a gate, then complete), and all five sections visible on the hub with server-enforced locks. This is the "demo 1 is ready" checkpoint.

**Blocked by:** 04 (Hub, locks, gates and explicit completion)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 1, 25 Sept)

- [ ] The four baseline statements (Bible, gifts, call, plan) render as 1–10 agreement scales with the prototype's anchor labels and wording; all four must be answered to continue
- [ ] The calling-statement section uses the prototype's scripture passages, hint text and statement prompt, with a long-text activity in place of the sentence builder
- [ ] The section's gate requires a statement of at least ten characters and shows an authored message when unmet
- [ ] All five sections appear on the hub; locks and status are enforced by the server
- [ ] In the full pathway the calling statement (Section 3) requires Sections 1 and 2, which have no content yet. So in the slice-1 document it requires only onboarding, and the lock is demonstrated on Sections 4 and 5, which require it. This is a document setting, not code, and is restored when Sections 1 and 2 exist
- [ ] Section 5 holds the prototype's letter-to-your-future-self prompt as a long-text block, followed by the four baseline statements again as separate "after" rating blocks (same wording and anchors)
- [ ] Section 5's gate requires the letter (minimum length) and all four after-ratings, so the letter cannot be sent (the section completed) without them; delivery is not built
- [ ] The gate message for the after-ratings reuses the prototype's "Answer all four to continue" wording
- [ ] Progress survives a reload and a second device
- [ ] Wording is migrated verbatim from the prototype reference; nothing is invented
- [ ] Demo check: editing a prompt in the document file and loading it again changes the running app for a fresh participant

**Notes handed over from ticket 04**

- **This ticket needs no new code.** Every block and clause it asks for exists: `agreement_scale` for the ratings, `scripture_reading` for the read-confirm, `rich_text` with `variant: "hint"` for the big-question text, `long_text` for the activity and the letter, and the `has_answer` and `min_text_length` clauses for both gates. It is document authoring plus content migration. Treat a need for new code as a signal that something has been misread.
- **"Answer all four to continue" is four clauses and one sentence.** Write four `has_answer` clauses carrying that same message; `unmet()` de-duplicates identical messages, so the participant reads it once. This was fixed at the end of ticket 04 specifically for this criterion.
- **Where the content is.** `Prototype for reference/vibe-coded-prototype.html`, with `docs/prototype/` as the map. The calling section's five passages are `s2a-reading` (L2458) and the baseline block is `renderBaselineButtons` (L2978); the baseline ids are `bl-bible`, `bl-gifts`, `bl-call`, `bl-plan`, and the closing copies are `pl-*`. Wording is migrated verbatim — the ticket says nothing is invented, and that includes anchor labels.
- **Locks need no code either.** Sections 4 and 5 demonstrate the lock through their `requires` lists, which is a document setting, as this ticket's own fourth criterion says.
- **Check the demo on a fresh participant.** A participant is pinned to the pathway version they started, so reloading the document does not change what someone already in progress sees. That is the behaviour, not a bug, and it is what the last criterion is testing.
- **Fake data only.** Consent does not exist until ticket 08, and the spec allows storing answers before it for slice 1 on that condition alone.
