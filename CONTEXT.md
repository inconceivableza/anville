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
- The pathway engine must not contain hidden hardcoded fallback content.
- The first product focuses on the pathway system, not the public marketing website.
- The authoring experience should provide both:
  - A structured visual editor.
  - An advanced validated JSON editor.
- Pathways support conditional visibility and branching.
- Publication states are draft, preview, published, and archived.
- Scoring rules are declarative JSON configuration, not arbitrary executable code.
- Prototype wording and ordering should initially be preserved during import.
- Gate 1 focuses on the participant pathway engine.
- Gate 2 adds full prototype import and collaboration workflows.
- Privacy should initially be participant-controlled where practical.
- Authentication should use a generic OIDC boundary through `django-allauth`; the provider is not yet chosen.

## Intended Architecture

- Backend: Python/Django.
- Database: PostgreSQL.
- Storage: JSON pathway and configuration documents stored in SQL rows, with relational entities where needed for identity, permissions, assignments, responses, and querying.
- Authentication: OAuth/OpenID Connect through `django-allauth`.
- Interaction: HTMX.
- Client build: JavaScript built with Vite. The precise client framework and Django/HTMX/Vite boundary remain to be decided.
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

- Exact organisation and tenancy model.
- Whether pathway availability is assignment-based, organisation-based, invitation-based, or a combination.
- The detailed permission matrix.
- The exact client framework used with Vite.
- The concrete OIDC provider.
- Which pathway content types and scoring operators are supported initially.
- How JSON documents are versioned and validated.
- Whether published pathway versions are immutable.
- Exact privacy, consent, retention, and deletion rules.
- Email, PDF, scheduled-letter, video, and notification providers.
- Deployment choice between Docker Compose and k3s/Helm.