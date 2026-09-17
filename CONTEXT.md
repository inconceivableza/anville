# Anville

> ✨ Most of this document was produced with AI assistance; human decisions and edits may be interleaved.

## Studio And Product

Anville is the configurable pathway studio and engine. Its first pathway is Whatever You Do, a Christian vocational-calling and discernment platform.

Anville's coach-studio editor allows authorised users to create coaching pathways. A pathway may contain sections, content blocks, questionnaires, activities, routes, completion rules, scoring, mentor material, observer feedback, and participant reflection.

The existing HTML prototype is a behavioural and content reference only. It is not the production architecture.

## Current Decisions

- The first demo targets one organisation and one pathway.
- Platform owners/admins are the initial pathway authors.
- Participants can access all published pathways available to them.
- If exactly one pathway is available, open it automatically.
- If no pathway is available, show an intentional empty application state.
- A pathway with configured sections but no content must also render as empty.
- Gate 1 administrators explicitly create participant assignments; participants do not discover pathways without an assignment.
- Gate 1 requires one authenticated user per participant; anonymous completion is later work.
- Gate 1 assignments support `active`, `completed`, `revoked`, and `expired` states.
- Each assignment stores the participant, pathway, pinned pathway version, status, timestamps, and creating administrator.
- The database enforces one response per assignment, and an assignment's pinned pathway version cannot change after creation.
- Assignment expiry is optional, enforced server-side, and reflected in the assignment status.
- The pathway engine must not contain hidden hardcoded fallback content.
- The first product focuses on the pathway system, not the public marketing website.
- The authoring experience should provide both:
  - A structured visual editor.
  - An advanced validated JSON editor.
- Gate 1 includes minimal authoring, preview, and publication; a polished drag-and-drop editor is later work.
- Gate 1 pathway availability is assignment-based; broader organisation or invitation availability remains later work.
- Pathways support conditional visibility and branching.
- Publication states are draft, preview, published, and archived.
- A pathway has at most one current published version, and only schema-valid and semantically valid documents can be published.
- Publication requires an explicit validation pass; archiving the previous published version and publishing the new version occur atomically.
- Preview versions are never assignable; participant access requires a published version.
- A published pathway version is immutable; later edits create a new draft/version.
- Responses are persisted separately from pathway definitions, with their JSON payload as the response source of truth and relational metadata or derived projections for querying, reporting, and aggregation.
- Each assignment points to a specific published pathway version; new participants receive the latest published version, while participants already in progress remain on the version they started.
- Each assignment has one resumable participant response; draft progress may be autosaved, and submission is the completion boundary after which the response is locked.
- Submission is idempotent; retries cannot create duplicate responses or result snapshots.
- Draft responses may be incomplete; required-field and route validation is enforced at submission.
- Each block or question can declare whether it is required; only reachable required items block submission.
- Non-interactive content blocks produce no response entries.
- Response answers are keyed by stable block or question identifiers, never by array positions.
- Responses are not automatically migrated when a question, scale, scoring rule, or identifier changes; those changes create a new pathway version, and explicit migration tooling is later work.
- Responses to blocks hidden by routing remain stored, but are excluded from active results unless the scoring configuration includes them.
- Preview uses synthetic participant state and never creates real assignments or participant responses.
- Schema validation occurs during editing; semantic validation is required before preview and publication.
- Response payloads are structurally validated on save; reachability, requiredness, and scoring rules are enforced at submission.
- Structural validation uses a standard JSON Schema validator, while semantic validation uses explicit application-level rules.
- The initial pathway schema uses JSON Schema Draft 2020-12.
- Structural and semantic validation return machine-readable error codes and document paths shared by the visual editor, JSON editor, preview, and publication workflows.
- In Gate 1, administrators can see assignment status and completion state but not raw participant answers by default; participant-controlled sharing is later work.
- Participants can see their own result after submission.
- Organisation is a real tenancy boundary from the beginning, even though the first demo seeds only one organisation.
- Every organisation-owned record is organisation-scoped at the database or query boundary; cross-organisation access is denied by default.
- Gate 1 administrators manage pathways, publication, and assignments; participants access only their own assignments, responses, and results.
- Gate 1 uses three effective permission levels: platform owner, organisation administrator, and participant.
- SQLAlchemy is the database access and ORM layer; Django remains the web and application framework.
- Submitted responses persist a result snapshot calculated from their pinned pathway version; later pathway versions never recalculate historical results.
- Submitted results persist dimension scores and classifications alongside the result presentation snapshot.
- The versioned JSON pathway document is canonical; the visual editor and advanced JSON editor both read and write that same document.
- Section, block, question, route, and scoring identifiers are stable logical identifiers, not array positions or DOM identifiers, and are never reused for a different meaning.
- Gate 1 choice questions support single-select and multi-select options with stable option identifiers.
- Scoring rules are declarative JSON configuration, not arbitrary executable code.
- Gate 1 scoring uses a small allowlisted set of numeric operators; unsupported or invalid formulas block publication.
- Declarative conditions must never execute arbitrary code.
- Routes are deterministic and side-effect-free evaluations of stored response or pathway state; invalid route references block publication.
- Routes use explicit ordered branches with a deterministic fallback; ambiguous or missing fallbacks block publication.
- Pathway publication, assignment changes, response submission, and result generation record actor and timestamp metadata.
- Audit entries are append-only and are not silently deleted or overwritten.
- Persisted lifecycle timestamps are server-generated UTC timestamps; client-provided timestamps are ignored.
- Pathway design separates content, instrument/question definitions, measurement/scoring, and report/presentation.
- These layers remain within one versioned pathway document; relational records wrap the document for ownership, publication, responses, and querying.
- Ranking and card-sorting responses are treated as relative data and are not automatically comparable across people.
- Free-text responses are not scored unless an explicit configured analysis method is added.
- Gate 1 scoring supports numeric rating-based scoring only; ranking, card sorting, and observer comparison are later work.
- Gate 1 numeric ratings use configurable integer scales with explicit minimum, maximum, labels, and optional scoring weights.
- Every reachable scored rating is required before a result can be calculated.
- Gate 1 initially supports content, choice question, numeric rating, reflection, result, and completion blocks; richer activities, media, ranking, card sorting, contact collection, Scripture-specific blocks, and collaboration blocks are later work.
- The pathway document supports role-specific prompts from the beginning, even though Gate 1 renders participant wording only.
- Prototype wording and ordering should initially be preserved during import.
- Gate 1 focuses on the participant pathway engine.
- Progress counts reachable interactive blocks rather than every block in the pathway.
- Completion requires both a valid submission and reaching the configured completion block.
- Revoked or expired assignments prevent further access while preserving existing responses and audit history.
- Gate 2 adds full prototype import and collaboration workflows.
- Privacy should initially be participant-controlled where practical.
- Participant deletion or anonymisation preserves aggregate audit integrity while removing identifying data where legally required.
- Observer identity and observer responses are stored as separate concerns, and the product must not promise complete anonymity unless it can guarantee it.
- Observer-facing privacy language must state precisely what is and is not shown to the participant.
- Observer and mentor workflows are Gate 2 work; their roles and privacy boundaries remain part of the domain model.
- Observer aggregates are suppressed until a minimum response count is met; the provisional Gate 2 threshold is three ordinary responses and a higher threshold for sensitive or easily identifying feedback.
- Authentication should use a generic OIDC boundary through `django-allauth`; the provider is not yet chosen.
- Gate 1 may use a local development authentication path behind that same boundary; choosing a production OIDC provider is not required before the participant and administrator flows are built.

## Intended Architecture

- Backend: Python/Django.
- Database: PostgreSQL.
- Persistence: SQLAlchemy ORM/Core with PostgreSQL.
- Storage: JSON pathway and configuration documents stored in SQL rows, with relational entities where needed for identity, permissions, assignments, one response per assignment, response status, result snapshots, audit metadata, and querying.
- The storage model follows a relational spine with JSON payloads where the shape is pathway-specific; persisted responses are separate from pathway definitions and may have derived query projections.
- Authentication: a generic OAuth/OpenID Connect boundary through `django-allauth`, with a replaceable local development authentication path for Gate 1.
- Interaction: HTMX.
- Client build: Django-rendered HTML with HTMX and focused Vite JavaScript modules; Gate 1 does not introduce a SPA framework.
- Source control: GitHub.
- Future hosting: Hetzner.
- Future deployment: Docker Compose or k3s/Helm, to be decided later.

## Domain Terms

### Organisation

A group that owns or administers pathways and may contain cohorts, leaders, mentors, or participants.

### Pathway

A published or draft coaching experience. A pathway contains ordered sections or steps and their configured content, rules, routes, and result behaviour.

### Block

A configured unit of pathway content or interaction. Examples include paragraph, Scripture passage, video, resource, callout, activity, question, rating, card sort, contact collection, reflection, result, and completion blocks.

### Assignment

The relationship that makes a pathway available to a participant. A participant may eventually have multiple assignments.

### Response

A participant's or collaborator's persisted answer to a configured block or question.

### Route

A configured rule that controls visibility, progression, branching, or completion based on answers, roles, or state.

### Scoring model

A declarative configuration defining dimensions, items, scales, weights, formulas, normalisation, thresholds, classifications, and result presentation.

### Collaborator

A mentor, coach, observer, trusted contact, or organisation leader who may receive access or submit configured input.

### Participant

The person completing a pathway and controlling access to their collaboration data where the product permits.

### Observer

An invited person who provides configured feedback about a participant, normally through a scoped invitation rather than a full account.

### Mentor

A collaborator named or selected by a participant who may receive only the pathway information the participant chooses to share.

### Administrator

An authorised organisation or platform user who can author, validate, preview, publish, and manage pathway versions.

### Invitation

A scoped, revocable access grant for a collaborator or observer, with its own response status and expiry rather than a shared reusable link.

### Pathway version

An immutable published execution target. It identifies the exact pathway definition, content, rules, scoring configuration, and result presentation used for a participant response.

## Gate 1 Acceptance Criteria

An administrator can:

- Authenticate.
- Create or import one pathway.
- Define sections and representative content/question blocks.
- Configure conditional visibility or branching.
- Configure at least one declarative scoring flow.
- Edit through the visual editor and validated JSON view.
- Preview the pathway.
- Publish and unpublish/archive the pathway.

A participant can:

- Authenticate.
- See an empty state when no pathway is available.
- Be shown the only available pathway automatically.
- Access an assigned or available published pathway.
- Complete configured content and questions.
- Follow configured routes.
- Submit responses.
- Return later and see persisted responses.
- Receive results calculated from stored scoring configuration.

## Gate 2 Acceptance Criteria

The imported pathway reproduces the prototype's meaningful participant journey and content through configuration rather than hardcoded application code.

Gate 2 additionally supports:

- Mentor or coach access.
- Observer/trusted-contact invitations and responses.
- Participant-controlled sharing.
- Configured anonymity and aggregation rules.
- Organisation-leader views.
- Real persisted collaboration data.
- Prototype-equivalent completion, summary, and result behaviour.

## Open Decisions

- Long-term pathway availability beyond Gate 1 assignment, including organisation-wide and invitation-based access.
- The detailed permission matrix.
- The concrete OIDC provider.
- Which additional scoring operators are supported beyond Gate 1 numeric rating scoring.
- Exact privacy, consent, retention, and deletion rules.
- Exact observer aggregation thresholds and sensitive-feedback disclosure rules.
- Email, PDF, scheduled-letter, video, and notification providers.
- Deployment choice between Docker Compose and k3s/Helm.