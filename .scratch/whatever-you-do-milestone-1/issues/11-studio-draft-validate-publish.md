# 11: Studio: draft, validate and publish

**What to build:** The studio's core loop and its first face. An author creates a draft from a published version, edits it in a schema-validated JSON editor, sees errors that show where in the document the problem is, and publishes it as a new immutable pathway version. Participants are never affected by a draft.

**Blocked by:** 02 (Pathway document, versions and loader)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [ ] Only authors of the deployment can reach the studio; participants cannot. An author is an account marked as such on the server, created by a management command or Django admin; there is no self-service route to become one
- [ ] An author creates a draft from the current published version and edits it without changing what any participant sees
- [ ] The JSON editor validates against the document's schema as the author types (Monaco through a Vite module), with errors shown against document paths
- [ ] Publishing requires a passing schema validation and linter pass, and creates a new immutable version with its own content hash; previous versions are untouched
- [ ] An invalid draft cannot be published
- [ ] The behaviour of a participant already in progress when a new version is published follows the default in the spec (they stay on the version they started)
- [ ] Journey tests cover publish creating a new version, refusing an invalid draft, and leaving prior versions unmodified
