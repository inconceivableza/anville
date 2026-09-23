# 05: Slice 1 content: baseline and calling-statement section

**What to build:** *Whatever You Do* content, authored in the pathway document from the prototype reference, that makes Demo 1 real: the four baseline ratings, one full section (scripture read-confirm, a long-text activity, a gate, then complete), and all five sections visible on the hub with server-enforced locks. This is the "demo 1 is ready" checkpoint.

**Blocked by:** 04 (Hub, locks, gates and explicit completion)

**Status:** resolved

**Parent:** whatever-you-do-milestone-1 spec (Demo 1, 25 Sept)

- [x] The four baseline statements (Bible, gifts, call, plan) render as 1–10 agreement scales with the prototype's anchor labels and wording; all four must be answered to continue
- [x] The calling-statement section uses the prototype's scripture passages, hint text and statement prompt, with a long-text activity in place of the sentence builder
- [x] The section's gate requires a statement of at least ten characters and shows an authored message when unmet
- [x] All five sections appear on the hub; locks and status are enforced by the server
- [x] In the full pathway the calling statement (Section 3) requires Sections 1 and 2, which have no content yet. So in the slice-1 document it requires only onboarding, and the lock is demonstrated on Sections 4 and 5, which require it. This is a document setting, not code, and is restored when Sections 1 and 2 exist
- [x] Section 5 holds the prototype's letter-to-your-future-self prompt as a long-text block, followed by the four baseline statements again as separate "after" rating blocks (same wording and anchors)
- [x] Section 5's gate requires the letter (minimum length) and all four after-ratings, so the letter cannot be sent (the section completed) without them; delivery is not built
- [x] The gate message for the after-ratings reuses the prototype's "Answer all four to continue" wording
- [x] Progress survives a reload and a second device
- [x] Wording is migrated verbatim from the prototype reference; nothing is invented
- [x] Demo check: editing a prompt in the document file and loading it again changes the running app for a fresh participant

**Notes handed over from ticket 04**

- **This ticket needs no new code.** Every block and clause it asks for exists: `agreement_scale` for the ratings, `scripture_reading` for the read-confirm, `rich_text` with `variant: "hint"` for the big-question text, `long_text` for the activity and the letter, and the `has_answer` and `min_text_length` clauses for both gates. It is document authoring plus content migration. Treat a need for new code as a signal that something has been misread.
- **"Answer all four to continue" is four clauses and one sentence.** Write four `has_answer` clauses carrying that same message; `unmet()` de-duplicates identical messages, so the participant reads it once. This was fixed at the end of ticket 04 specifically for this criterion.
- **Where the content is.** `Prototype for reference/vibe-coded-prototype.html`, with `docs/prototype/` as the map. The calling section's five passages are `s2a-reading` (L2458) and the baseline block is `renderBaselineButtons` (L2978); the baseline ids are `bl-bible`, `bl-gifts`, `bl-call`, `bl-plan`, and the closing copies are `pl-*`. Wording is migrated verbatim — the ticket says nothing is invented, and that includes anchor labels.
- **Locks need no code either.** Sections 4 and 5 demonstrate the lock through their `requires` lists, which is a document setting, as this ticket's own fourth criterion says.
- **Check the demo on a fresh participant.** A participant is pinned to the pathway version they started, so reloading the document does not change what someone already in progress sees. That is the behaviour, not a bug, and it is what the last criterion is testing.
- **Fake data only.** Consent does not exist until ticket 08, and the spec allows storing answers before it for slice 1 on that condition alone.

## Answer

Built as `pathways/whatever-you-do.json`, with `tests/journeys/test_whatever_you_do.py` reading that
file rather than a test fixture, because what is under test is the content. No Python changed: every
block type and clause the ticket asked for already existed, as ticket 04 said it would.

The document has six sections — `onboarding` plus Sections 1–5. Prototype identifiers are kept where
the prototype has one (`bl-*`, `pl-*`, `s2a-reading`, `cl-statement`, `lt-message`) so a string can be
traced back to its source; the rest are new (`calling-task`, `lt-task`, `baseline-intro`, `pl-intro`).

Load it with `python manage.py load_pathway pathways/whatever-you-do.json`.

**Notes handed over to the sections that follow**

- **Sections 1, 2 and 4 carry their prototype hint box and nothing else.** Left empty they were blank
  pages with a working "Mark complete", and the hub's next-step banner pointed at one. The hint is
  verbatim ("The big question" for Section 1, "The task" for 2 and 4), carries no answer, and so counts
  towards no progress. When an activity is built for one of those sections, the hint stays above it.
- **Section 3 requires only `onboarding`, and that is temporary.** The fifth criterion says so. When
  Sections 1 and 2 have content, `calling` should require `["designed", "shape"]`. Nothing else has to
  change: Sections 4 and 5 already require `calling`.
- **The letter section is trimmed, and someone should decide whether to restore the rest.** The ticket
  asked for "the prototype's letter-to-your-future-self prompt as a long-text block", so it holds the
  task hint, the `Your letter` prompt and the four after-ratings. The prototype's letter screen also
  has a seven-item "Things you might want to include" list (L2597) and a Joshua 4:1–7 note about the
  twelve stones (L2589). Both were left out: the list is the `checklist_prompt` block (docs/prototype
  03-blocks.md, type 21) and no block type captures a bulleted list, and setting it as `rich_text`
  prose would lose its shape. The dropped `letter-hint` line, "Use as many of the prompts above as you
  like", only makes sense once the list is back.
- **Verse numbers are not in the passages.** The prototype interleaves `<span class="verse-num">` into
  the passage prose. A `scripture_reading` passage is plain text, so the numbers are dropped rather
  than left as bare digits in the middle of a sentence. If they should be shown, that is a block change.
- **Both gate messages come from the prototype.** "Write your calling statement to continue." is the
  `calling-gate` div (L4367) and "Write at least one part of your letter before sealing it." is the
  alert in `sealLetter()` (L7375). Neither was written here. The second still says "sealing", which is
  the prototype's word for completing the section; delivery is not built (trap 12).
- **A completed section can be reopened, including `onboarding`.** Reopening onboarding re-locks
  Section 3 only if it is not already complete — worth knowing before demonstrating anything live.
