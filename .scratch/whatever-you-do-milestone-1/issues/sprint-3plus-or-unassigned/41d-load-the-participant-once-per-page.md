# 41d: Load the participant once per page

**What to build:** A participant page reads the participant's progress from the database once, however many parts of it show that progress, so the header's sidebar adds no queries of its own and the hub is derived once.

**Blocked by:** 41a (A header with sign out, and a pathway sidebar)

**Status:** needs-triage

**Sprint:** 3 or later

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress

- [ ] Each participant page loads the participant's progress once, the sidebar included
- [ ] The hub page derives the hub once, for both its list and the sidebar
- [ ] Pages look and behave exactly as before

**Context**

- Found in 41a's code review. The sidebar's template tag looks the participant up again on every participant page, a few small queries more, and on the hub derives the hub a second time. Unnoticeable at the current scale; worth doing before the number of participants grows
