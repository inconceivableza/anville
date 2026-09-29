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
A client-side HTML sketch by the content owner of all or part of a pathway. A behavioural and content reference, never production architecture.
_Avoid_: v1, the old app, the demo, mock-up.

**Original prototype**:
The first prototype, covering the whole of *Whatever You Do*, from which the engine and the faithful port are built.
_Avoid_: the prototype (when another prototype could be meant).

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

**Faithful port**:
The pathway document that reproduces the original prototype without the content owner's later changes, kept complete alongside the pathway so the two can be compared.
_Avoid_: v1, original version, baseline document.

**Section**:
A top-level division of a pathway, presented to the participant as one unit of work.
_Avoid_: pillar, chapter, step, module.

**Track**:
A participant-chosen, ordered list of a pathway's sections with its own hub. A section may belong to more than one track, and a participant's answers persist when they switch.
_Avoid_: journey, path, route.

**Block**:
A configured unit of content or interaction within a section. Some blocks capture a response; some do not.
_Avoid_: element, field, widget, component.

**Page**:
One of the parts an author may split a section into, reached by the participant one after another; the hub shows the section as one. A section not split is a single page.
_Avoid_: screen, step, sub-section.

**Hub**:
The engine-derived overview of a participant's track: its sections, their status and locks, and the next step. Never authored.
_Avoid_: dashboard, home, menu.

**Lock**:
The state of a section whose required sections are not yet complete. Locks come from section order; gates come from a section's own requirements.
_Avoid_: gate, padlock, block.

**Gate**:
A predicate that must pass before a participant may complete a section, together with the authored copy explaining which clause failed.
_Avoid_: check, validation, lock. (The prior plans used "Gate" for delivery milestones; in this repo a milestone is a *milestone*.)

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
An invited person who answers the pathway's instrument *about* a participant, in wording addressed to them, without an account.
_Avoid_: trusted contact, respondent, rater, referee.

**Invitation**:
A participant's revocable, expiring grant to one named person to act as an observer, carried by a link unique to that person.
_Avoid_: invite link, survey link, access code.

**Coach**:
A person the participant names to walk alongside them, who draws out the participant's own conclusions rather than passing on their own experience, and who receives only what the participant chooses to share.
_Avoid_: mentor, guide, supervisor.

**Content owner**:
The person who owns the content and direction of *Whatever You Do*, and who writes its prototypes.
_Avoid_: client, product owner, prototype builder.

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

**Enrolment code**:
A shared code that admits a person to sign up to a deployment. It grants access only and never stands in for consent.
_Avoid_: invite code, access code, password.

**Consent**:
A participant's explicit, withdrawable agreement to how their answers are processed, recorded against the version of the text they agreed to and kept separate from enrolment.
_Avoid_: opt-in, agreement, terms.
