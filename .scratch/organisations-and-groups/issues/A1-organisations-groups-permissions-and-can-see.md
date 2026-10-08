# A1: Organisations, groups, membership and permissions, with can_see

**What to build:** The operator creates an organisation and its first organisation admin in one form in Django admin, adds groups (cohort or team) and members to it, and grants organisation or group admin rights. Any code can then ask `can_see(viewer, participant, "progress")` and get the same answer the pages will use.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Spec:** Shape (ADR 0012); Models; `can_see`; Testing Decisions

- [ ] In Django admin the operator can create an organisation with its first admin's permission on the same form, and add groups, memberships and permissions; a permission names exactly one of an organisation or a group
- [ ] A participant can be a member of groups in more than one organisation, and of each group only once
- [ ] `can_see` is true for an organisation admin over members of any of its groups, including groups made later, and for a group admin over members of that group only
- [ ] `can_see` is false with no permission, for a non-member, while the participant's consent is missing, withdrawn or outdated, and for anything other than progress whatever permissions exist
- [ ] Nothing about a participant's pathway changes for members or non-members
