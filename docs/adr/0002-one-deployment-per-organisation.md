---
status: accepted
---

# One deployment per organisation; no tenancy in the data model

Anville is meant to be usable by many churches and organisations, and may be open source. We will not build multi-tenancy: each organisation runs its own deployment with its own database and configuration, and the data model has no organisation concept. The prior plan made organisation a real tenancy boundary from the start; that is rejected here.

> ✨ Drafted with AI assistance; the decision was reviewed and agreed by the team.

## Considered options

**One deployment serving many organisations, with an organisation on every record.** Rejected for now. The costs:

- Every table carries an organisation and every query filters on it, so "cross-organisation access denied by default" becomes a security property that must be enforced and tested everywhere.
- It brings a permission matrix (platform owner, organisation administrator, participant) and an organisation-management surface before any second organisation exists.
- With one solo developer and a first demo days away, that is scope spent on a customer that has not been named.

## Consequences

- There is no `Organisation` model and no `organisation_id` column. Anyone who can author is an author of the whole deployment.
- The deployment must be cheap to stand up repeatedly: configuration comes from the environment, and nothing is hardcoded to *Whatever You Do* outside the pathway document.
- Small organisations without technical staff need someone to host for them. That is done as one deployment each, not by adding tenancy.
- Reversing this is expensive, because retrofitting tenancy touches every table and every query. That is accepted deliberately; if hosting many organisations becomes the main use, reopen this decision before the second one is onboarded.
