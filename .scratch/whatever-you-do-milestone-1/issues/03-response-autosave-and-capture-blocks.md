# 03: Response, autosave and first capture blocks

**What to build:** A participant's work is stored. A section renders rich text, long text and agreement scale blocks; each answer autosaves individually as it is entered, and the participant resumes exactly where they left off on a fresh session or another device.

**Blocked by:** 02 (Pathway document, versions and loader)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 1, 25 Sept)

- [x] One response exists per participant per pathway version, recording the version it was answered against; answers are stored as JSON keyed by block identifier
- [x] Rich text renders authored content with output escaped; long text captures free writing; agreement scale captures 1–10 with authored anchor labels
- [x] Autosave writes one block's answer at a time and never re-serialises the whole response; saving one block leaves other blocks' answers untouched
- [x] The server validates each answer against that block's answer schema and rejects unknown block identifiers and malformed values
- [x] A participant logging in on a fresh session or another device sees every earlier answer
- [x] Responses carry a test-data marker held on the server, never a client-side flag
- [ ] Pages use the prototype's look: its colour variables and fonts (self-hosted through Vite, not Google Fonts) and the base styles for page, buttons, panels, hint boxes, scripture notes and the 1–10 scale, in one stylesheet; templates use the colour variables rather than raw colours. Done for the hub; the sign-in and sign-up pages still use allauth's own templates and do not load the stylesheet
- [x] Journey tests cover autosave isolation, rejection of invalid answers, and resume

**Carried from 02**

- [x] A participant already in progress stays on the version their response was started against when a later version is published. Today the hub always shows `Publication.current_version()`, and the README says this ticket changes that
- [x] Replace the placeholder `_BLOCK_TEXT` rendering in `engine/views.py` with real block rendering. It raises `KeyError` for a block type it does not know
