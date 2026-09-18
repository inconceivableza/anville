---
status: accepted
---

# Use the Django ORM, not SQLAlchemy

Anville uses Django with `django-allauth` for authentication, which means the Django ORM is already present and managing the auth, allauth, session and admin tables — it cannot be removed. Adopting SQLAlchemy would therefore mean running *two* ORMs and two migration systems against one Postgres database, rather than choosing between them. We use the Django ORM alone.

> ✨ Drafted with AI assistance; the decision and its reasoning were reviewed and agreed by the team.

## Considered options

**SQLAlchemy as the database access and ORM layer, with Django as the web framework.** This was recorded as a decision in the previous `CONTEXT.md` and is rejected here, so a future reader will otherwise re-propose it. The costs:

- Two migration systems — Django migrations for the auth tables, Alembic for domain tables — with no knowledge of each other, making deploy ordering, rollback and schema drift two questions instead of one.
- `transaction.atomic()` wraps a Django connection while a SQLAlchemy session holds its own, so a response submission and its audit entry could not be made atomic without deliberately sharing a connection. Audit entries are meant to be append-only and never silently lost.
- Foreign keys to `auth.User` degrade to bare integer columns with no relationship or cascade — repeated for organisation, creating administrator and audit actor.
- Organisation scoping ("cross-organisation access denied by default") would need enforcing in two idioms, leaving the security property only as strong as the weaker one.
- Django admin cannot introspect non-Django models, costing a free early scaffold for the pathway editor.

The stated motivation was storing JSON documents in SQL rows. `models.JSONField()` maps to Postgres `jsonb` with GIN indexing and containment queries, so nothing is given up.

## Consequences

- One ORM and one migration system. There should never be an `alembic.ini` in this repository.
- SQLAlchemy Core stays available as a read-only tool for the derived `response_items` projection (Plan 1, section 2.4) if reporting queries later need it. That is additive and does not reopen this decision.
- The choice matters less than it appears if the engine is built as a pure core over the pathway version document and the response document. Persistence then only loads a JSON blob, calls the core, and saves a JSON blob plus a few indexed columns — the least demanding ORM workload there is.
