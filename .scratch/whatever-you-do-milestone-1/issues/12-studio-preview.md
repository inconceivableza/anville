# 12: Studio: preview

**What to build:** Preview for drafts. An author sees an unpublished draft rendered as a participant would, using synthetic participant state, without ever creating a real response, consent or observer record.

**Blocked by:** 04 (Hub, locks, gates and explicit completion), 11 (Studio: draft, validate and publish)

**Status:** ready-for-agent

**Parent:** whatever-you-do-milestone-1 spec (Demo 2, 2 Oct)

- [ ] An author can open any draft in preview and move through it as a participant would, including the hub, locks and gates
- [ ] Preview uses synthetic state held only for the preview; it creates no response, consent or observer records
- [ ] A persistent banner says the view is a preview of an unpublished draft, with a way to clear the synthetic state
- [ ] Preview refuses a draft that fails validation and shows the errors with document paths
- [ ] A journey test asserts that using preview creates no response rows
