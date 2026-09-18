# Whatever You Do Prototype

> ✨ Most of this document was produced with AI assistance; human decisions and edits may be interleaved.

## Purpose

The prototype is a single-file visual and behavioural reference for Whatever You Do, the first product built with Anville, a configurable pathway studio and engine. It represents the product experience and content, not the Anville authoring system.

It demonstrates the intended participant journey and a possible public-facing product surface. It does not provide a reusable pathway engine or production backend.

## Public Experience

The prototype includes:

- Homepage and hero messaging.
- About section.
- Five-part explanation of the journey.
- Impact statistics.
- Church-leader marketing page.
- Blog index with five hardcoded articles.
- Newsletter form.
- Team and advisory-board placeholders.
- Spiritual-direction promotion.
- Donation and contact sections.
- Footer content.

This public marketing surface is not part of the first application milestone.

## Participant Journey

1. Account setup:
   - Name.
   - Email.
   - Date of birth.
   - Reason for taking the course.
2. Baseline ratings:
   - Biblical understanding of work/calling.
   - Understanding of personal gifts and limitations.
   - Sense of God's specific calling.
   - Clarity of practical plan.
3. Mentor setup:
   - Mentor name and email.
   - Contact confirmation.
   - Copyable invitation link.
   - Optional skip.
4. Trusted contacts:
   - Contact names and email addresses.
   - Add-more control.
   - Observer email preview.
   - Optional skip.
5. Journey selection:
   - Online guided journey.
   - Offline workbook plus online assessment.
6. Workbook hub.
7. Five workbook sections.
8. Closing video.
9. Repeated closing baseline ratings.
10. Completion summary.
11. Congratulations and next steps.

## Workbook Sections

### 1. How You Have Been Designed

- Scripture reading confirmation.
- Gifts and talents reflection.
- Strengths assessment.
- Trusted observer feedback.
- Self-versus-others comparison.
- Written summary of gifts and limitations.
- Completion gates based on assessment, comparison, and reflection.

### 2. The Shape of Your Life

- Capture remembered material.
- Name life chapters or seasons.
- Place markers into chapters.
- Record recurring threads.

Marker types include:

- Open door.
- Hardship or loss.
- Person.
- Lasting fruit.
- God's leading.

Prototype readiness rules include:

- At least three chapters.
- At least five markers.
- At least three marker types.
- Every marker assigned to a chapter.
- At least ten characters of recurring observations.

### 3. Putting Your Calling Into Words

- Recap of earlier work.
- Sentence builder:
  - Contribution.
  - Who it serves.
  - Outcome.
- Calling statement:
  - “God seems to have designed me to [contribution] among [who], so that [outcome].”
- Reflection on giving God glory.
- Minimum calling statement length.

The section also generates divergent possibilities through four lenses:

- Who it serves.
- The participant's contribution.
- The vehicle, such as job, business, church, or voluntary role.
- “What if?” provocations.

Prototype readiness rules include:

- At least six possibilities.
- At least two lenses.
- At least two developed role or life pictures.

Each picture contains:

- Title.
- Intended people.
- Daily life.
- What it would take.
- An example day.

### 4. Growth Plan

Activities are grouped into:

- Steps of faith or experiments.
- Skills and gifting.
- Character.
- Mentorship.
- Discipling others.

Activities may be:

- Selected from suggestions.
- Entered as custom text.
- Assigned to quarters.
- Reordered.
- Unassigned or removed.

The prototype uses six example quarters from Q3 2026 through Q4 2027.

The production version must make all activity categories, suggestions, time periods, ordering rules, and completion requirements configurable.

### 5. Letter to Your Future Self

- Reflection prompts.
- Recap of calling statement.
- Recap of starred possibilities.
- Recap of growth-plan activities.
- Letter text.
- Delivery email.
- Future delivery date.
- Save, copy, print, and seal controls.

The prototype's letter is only generated locally. It is not posted, scheduled, emailed, or persisted remotely.

## Assessment

The prototype defines 36 hardcoded strength items.

Each item contains:

- Identifier.
- Label.
- APEST tags.
- Professional Energy Profile tags.

The participant:

1. Sorts every item into five buckets:
   - Definitely not me.
   - Not really me.
   - Average or unsure.
   - Good at this.
   - Real strength.
2. Fine-tunes each item using a 0–100 slider.
3. Receives calculated APEST and Professional Energy Profile results.

The production configurator must define:

- Assessment dimensions.
- Items and labels.
- Bucket or scale definitions.
- Item-to-dimension relationships.
- Weights.
- Formulas.
- Normalisation.
- Thresholds.
- Category classification.
- Result labels and explanatory content.
- Versioning and validation rules.

## Observer and Trusted-Contact Flow

The prototype sketches an observer invitation link and respondent journey.

The respondent is intended to provide:

- Strength assessment responses.
- Energy or happiness observations.
- Three best qualities.
- One new skill to develop.
- One existing skill to develop.
- One character area to develop.
- Biggest observed change.
- Tasks or work they struggle with.

The prototype does not persist actual observer responses. Comparison data is generated randomly and stored only in browser memory.

Production requirements include:

- Invitation tokens.
- Consent.
- Response status.
- Real server-side response persistence.
- Anonymity rules.
- Minimum aggregation thresholds.
- Participant-controlled sharing.
- Observer identity and relationship handling.
- Configured qualitative questions.
- Comparison and aggregation rules.

## Mentor Flow

The prototype supports:

- Mentor details.
- Optional mentor skip.
- Copyable mentor link.
- Section-specific mentor previews.
- Full-workbook mentor preview.
- Hardcoded mentor briefings.

Mentor briefings currently contain concepts such as:

- Purpose.
- Suggested duration.
- Questions.
- Watch-outs.
- Things to avoid.

The production version must make mentor access, briefing content, permissions, and sharing configurable.

## Timeline State

The prototype maintains timeline state containing:

- Chapters.
- Markers.
- Marker types.
- Marker-to-chapter assignments.
- Current phase.
- Recurring threads.
- Generated observations.

The state is rendered by JavaScript and synchronised to hidden legacy fields for summaries and mentor output.

## Calling and Possibility State

The prototype maintains separate calling state containing:

- Contribution.
- Intended audience.
- Outcome.
- Calling statement.
- Reflection on God's glory.
- Possibility ideas.
- Lens assignments.
- Starred ideas.
- Developed role pictures.

The state is fragmented between JavaScript objects, DOM fields, and generated HTML.

## Roadmap State

The prototype maintains separate growth-plan state containing:

- Activities.
- Activity identifiers.
- Categories.
- Quarter assignments.
- Selected activity.
- Suggested ordering.

The completion button does not clearly enforce a complete configured plan. Production completion rules must be explicit and centrally defined.

## Completion and Routing

The prototype contains sequential locks between major sections:

1. Gifts.
2. Timeline.
3. Calling statement.
4. Possibilities.
5. Role pictures.
6. Growth plan.
7. Letter.
8. Closing questions and completion.

Some gates are hardcoded in JavaScript and some are soft or incomplete. The production system must represent routes, visibility, prerequisites, and completion criteria as pathway configuration.

## Persistence and Export

The prototype uses:

- In-memory JavaScript state.
- Browser `localStorage`.
- Manual JSON save-file export.
- Manual JSON restore-file import.

It does not provide:

- Server-side persistence.
- User accounts.
- Authentication.
- Multi-device access.
- Server-side versioning.
- Audit history.
- Real data ownership or deletion controls.

The save-file scrubber removes angle brackets from imported strings before rendering, but this is prototype-level protection rather than a production persistence model.

## Prototype-Only Behaviour

The following are simulated or incomplete:

- Demo mode and auto-filled sample data.
- Tester briefing.
- Fake personal details using `example.com`.
- Invented observer data.
- Placeholder videos.
- Placeholder team and advisory-board content.
- Newsletter submission.
- Email previews instead of sending.
- Mentor communication previews.
- Future-letter delivery.
- PDF download.
- Offline workbook delivery.
- Reminder scheduling.
- Aggregate organisation dashboard.
- Some resource links.
- Some completion rules.
- Theological and editorial review.

These behaviours must not be mistaken for production requirements unless explicitly carried into the configured product.

## Migration Principles

- Treat the HTML as a source of behaviour and initial content.
- Preserve the user-facing wording and ordering for the first import.
- Move all meaningful content into pathway configuration.
- Move all questionnaire and scoring definitions into validated configuration.
- Replace browser globals with server-persisted pathway execution state.
- Replace fabricated observer data with real invitation and response workflows.
- Replace hardcoded gates with declarative completion and route rules.
- Keep prototype-only warnings, demo controls, fake data, and tester tooling out of the production participant experience.
- Preserve the option of a controlled test-data or preview mode for administrators.

## First Migration Gate

The first migration gate should prove the configurable engine with a representative pathway slice:

- Author creates a pathway.
- Author defines sections and blocks.
- Author configures at least one question and scoring rule.
- Author previews and publishes the pathway.
- Participant authenticates and sees the pathway.
- Participant completes configured blocks.
- Responses persist.
- Conditional routing works.
- Results are calculated from stored configuration.
- An empty pathway renders empty.
- A user with no available pathway receives an intentional empty state.

A separate second gate should import the full prototype journey and content, then add mentor, observer, and organisation-leader collaboration.

## Known Risks

- The prototype's visible completeness may obscure simulated behaviour.
- Content, workflow state, responses, and presentation are currently mixed.
- Hidden legacy fields duplicate state.
- Hardcoded scoring rules may be difficult to migrate without independent worked examples.
- Observer privacy and aggregation require careful specification.
- Completion rules need explicit semantics.
- Published pathway versioning must prevent participant experiences changing unexpectedly.
- JSON configuration requires schema validation and safe expression evaluation.
- Authentication, permissions, consent, and data retention require security review.