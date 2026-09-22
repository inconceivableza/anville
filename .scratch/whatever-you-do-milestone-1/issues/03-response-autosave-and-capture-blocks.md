# 03: Response, autosave and first capture blocks

**What to build:** A participant's work is stored. A section renders rich text, long text and agreement scale blocks; each answer autosaves individually as it is entered, and the participant resumes exactly where they left off on a fresh session or another device.

**Blocked by:** 02 (Pathway document, versions and loader)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 1, 25 Sept)

- [ ] One response exists per participant per pathway version, recording the version it was answered against; answers are stored as JSON keyed by block identifier
- [ ] Rich text renders authored content with output escaped; long text captures free writing; agreement scale captures 1–10 with authored anchor labels
- [ ] Autosave writes one block's answer at a time and never re-serialises the whole response; saving one block leaves other blocks' answers untouched
- [ ] The server validates each answer against that block's answer schema and rejects unknown block identifiers and malformed values
- [ ] A participant logging in on a fresh session or another device sees every earlier answer
- [ ] Responses carry a test-data marker held on the server, never a client-side flag
- [ ] Journey tests cover autosave isolation, rejection of invalid answers, and resume

**Carried from 02**

- [ ] A participant already in progress stays on the version their response was started against when a later version is published. Today the hub always shows `Publication.current_version()`, and the README says this ticket changes that
- [ ] Replace the placeholder `_BLOCK_TEXT` rendering in `engine/views.py` with real block rendering. It raises `KeyError` for a block type it does not know
