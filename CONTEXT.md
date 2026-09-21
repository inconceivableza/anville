# Anville

> ✨ Produced with AI assistance during a design interview; terms were agreed with the team.

Anville is a configurable coaching-pathway engine and studio. Its first pathway is
*Whatever You Do*, a Christian vocational-calling workbook.

This document is a glossary and nothing else. Decisions live in [docs/adr/](docs/adr/).
Behavioural reference for the prototype lives in [docs/prototype/](docs/prototype/).

## Language

### The product

**Anville**:
The engine that renders a pathway to a participant, and the studio in which a pathway is authored.
_Avoid_: the platform, the app, the workbook system.

**Studio**:
The authoring surface in which an author edits a pathway, previews it as a participant would see it, and publishes a new pathway version.
_Avoid_: admin, CMS, backend, builder.

**Whatever You Do**:
The first pathway. A Christian vocational-calling and discernment workbook.
_Avoid_: WYD, the workbook, the calling workbook.

**Prototype**:
The single-file client-side HTML sketch of *Whatever You Do*. A behavioural and content reference, never production architecture.
_Avoid_: v1, the old app, the demo.

### Pathway structure

**Pathway**:
A configured coaching experience: ordered sections and their content, rules and result behaviour.
_Avoid_: course, programme, questionnaire, workbook.

**Pathway version**:
An immutable snapshot of a pathway, and the exact thing a response is answered against.
_Avoid_: revision, release.

**Pathway document**:
The single versioned document holding a pathway version's content, instrument, measurement and presentation.
_Avoid_: config, schema, definition file.

**Section**:
A top-level division of a pathway, presented to the participant as one unit of work.
_Avoid_: pillar, chapter, step, module.

**Block**:
A configured unit of content or interaction within a section. Some blocks capture a response; some do not.
_Avoid_: element, field, widget, component.

**Gate**:
A predicate that must pass before a participant may proceed, together with the authored copy explaining which clause failed.
_Avoid_: lock, check, validation. (The prior plans used "Gate" for delivery milestones; in this repo a milestone is a *milestone*.)

**Recap**:
A block that shows a participant's earlier answers back to them through a named view, with an authored message for when there is nothing to show yet.
_Avoid_: summary, snapshot, derived block.

### Measurement

**Instrument**:
The scored set of items belonging to a pathway, distinct from the prose around it.
_Avoid_: assessment, test, survey, quiz.

**Item**:
A single scored statement within an instrument, carrying a permanent identifier.
_Avoid_: question, card, statement.

**Construct**:
A named quality an instrument measures. Items load onto constructs; items never carry a score themselves.
_Avoid_: dimension, axis, trait, category, pillar.

**Bucket**:
One of five named, ordered piles a participant sorts items into before fine-tuning, from weakest to strongest.
_Avoid_: pile, band, tier.

**Compositional score**:
A score expressed as a share of a grand total, so only relative shape survives and absolute strength is discarded. The prototype's profile is compositional; the plans call the same property *ipsative*.
_Avoid_: normalised score, percentage score.

### People

**Participant**:
The person completing a pathway, who owns their responses and controls what is shared.
_Avoid_: user, client, respondent, coachee.

**Observer**:
An invited person who answers a parallel instrument *about* a participant, without an account.
_Avoid_: trusted contact, respondent, rater, referee.

**Mentor**:
A person the participant names, who receives only what the participant chooses to share.
_Avoid_: coach, guide, supervisor.

**Author**:
The person who writes and edits a pathway. Assumed non-technical.
_Avoid_: admin, editor, content manager.

### Responses

**Response**:
A participant's or observer's persisted set of answers to one pathway version.
_Avoid_: submission, result, entry.

**Answer**:
One block's captured value within a response, keyed by that block's permanent identifier.
_Avoid_: field value, datum.

**Result**:
The scores and presentation computed from a response against the pathway version it was answered on, persisted once rather than recomputed.
_Avoid_: report, profile, outcome.

**Consent**:
A participant's explicit, withdrawable agreement to how their answers are processed, recorded against the version of the text they agreed to and kept separate from enrolment.
_Avoid_: opt-in, agreement, terms.
