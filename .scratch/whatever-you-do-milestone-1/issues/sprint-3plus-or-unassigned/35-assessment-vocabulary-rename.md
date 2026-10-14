# 35: Assessment vocabulary rename

**What to build:** The code, tests, spec and tickets use the agreed words for the instrument's answers (CONTEXT.md, Measurement and Responses): an assessment made by placing and then fine-tuning, a self-assessment and observer assessments, a self-result, observer results and the observer average. "Sort" no longer names a stored answer. Nothing a participant or observer sees changes.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3 or later

**Spec:** The instrument and scoring; Responses, answers and results; Observers (ADR 0005)

- [ ] Code names, docstrings and comments say assessment, placement, placing, self-result, observer result and observer average where they now say sort, sorted answer or aggregate; "sort" stays only for ordering
- [ ] Test names and helpers follow the same words, and the suite passes before and after unchanged in what it asserts
- [ ] The spec and open tickets use the same words
- [ ] Pathway versions already loaded, and the answers stored against them, keep working unchanged
- [ ] Authored wording shown to participants and observers (such as "Sort your strengths") is left to the content owner
