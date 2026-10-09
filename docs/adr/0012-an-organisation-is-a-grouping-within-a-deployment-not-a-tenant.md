---
status: accepted
---

# An organisation is a grouping within a deployment, not a tenant

Churches and ministries need to gather their participants into groups and follow their progress, so there is now an `Organisation` model: an organisation holds groups, and an organisation admin's or group admin's rights reach only as far as the organisation or group their permission names. This replaces ADR 0002's consequence that there is no `Organisation` model, and nothing else in it. ADR 0002 decided against tenancy, and that stands: a tenant is a deployment, isolated from others on its own domain with its own users and pathway, whereas an organisation shares its deployment's pathway and its participants, one of whom may be a member of several organisations at once. A participant in two tenants would be the very leak tenancy exists to prevent, so an organisation cannot be a tenant.

Organisations are kept apart by permissions checked inside Anville, not by isolation in the database. Whoever operates a deployment can read every organisation's data, and no permission row changes that. Authors still author the whole deployment; organisation and group admins do not author.

> ✨ Drafted with AI assistance.

## Considered options

**Make the organisation a tenant boundary, with an organisation on every record.** Rejected: the cost ADR 0002 describes, and it would forbid a participant belonging to two organisations.

**Keep ADR 0002 whole and build groups alone.** Rejected: a group then belongs to nothing, and nobody can be given rights over several groups at once.

## Consequences

- If tenancy comes later, by a schema per tenant (as django-tenants does) or by keying every table, it puts whole deployments into tenants. Organisations sit inside a tenant and need no rework.
- A permission names an account. Observers and coaches have no account, so they hold no permissions.

## Not decided here

- Accounts for coaches and observers may come later. An observer's answers are never linked to an account, even an observer who has one: they answer through their link, and ADR 0009 holds. A coach's account could be linked to their role as coach, since ADR 0010 already keeps the coach's acceptance.
