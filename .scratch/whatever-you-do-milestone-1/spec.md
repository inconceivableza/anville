# Spec: whatever-you-do-milestone-1

**Status:** ready-for-agent

> ✨ Synthesised with AI assistance from the `/grill-with-docs` session of 18–21 Sept 2026. Terms follow `CONTEXT.md`; decisions that are hard to reverse are recorded in ADRs 0001–0005 and are referenced here rather than repeated. Decisions that live nowhere else are written out in full below.

## Problem Statement

*Whatever You Do*, a Christian vocational-calling workbook, exists today as a single-file, browser-only prototype that demonstrates the intended experience, alongside a paper version that has already been run with real mentors. The prototype has no server. Its section gates are mostly cosmetic, the comparison between a participant's view of themselves and the view of people who know them is fabricated at render time, observers can never actually reach the questions they are meant to answer, and every prompt, scripture reference and scoring constant is hardcoded in its JavaScript. It cannot be reshaped without changing code, and it cannot be trusted with a real person's reflections.

The requirement is a real application, demonstrable to the content owner on 25 Sept and 2 Oct and to a remote audience at a tech event on 9 Oct, in which:

- a participant works through the workbook and can stop and resume on any device;
- people who know the participant can genuinely give feedback, and the participant sees it without learning who said what;
- a non-technical author can reshape the pathway (wording, scripture, instrument items, sections) without a developer, because other churches and organisations will want their own content and structure.

There is one developer, about 5–8 hours a day, with senior oversight, and 18 days. The scope has to be sequenced so that something real and demonstrable exists at each of the three dates, and so that what is cut, if time runs short, is cut in an agreed order.

## Solution

A server-rendered Django application in which the *Whatever You Do* **pathway** is not code but a **pathway document**, loaded as an immutable **pathway version**, that the engine renders to a **participant**. Everything the prototype hardcoded (the 36 **items**, the **constructs**, the bucket-to-points seeds, the scripture, the lens prompts, the gate messages, the mentor briefs) lives in that document. The engine owns the things that must not be authored: login, age confirmation, **consent**, the **hub**, progress, **locks**, gate evaluation, persistence and scoring.

The work lands in three demo slices. Each slice is demonstrable on its own.

### Slice 1 — 25 Sept (screen-share, local)

A real server-backed app, built on the content owner's content in a data file:

- sign-up behind the enrolment code, and login;
- the four baseline ratings, and one full **section** shaped as scripture read-confirm, then an activity, then a **gate**, then complete (the calling-statement section is the model, with a plain long-text activity in place of the sentence builder);
- a hub showing all five sections, with locks enforced by the server;
- progress that survives a reload and a second device;
- the pathway document loaded by a command, so that editing one prompt in the file and reloading visibly changes the app.

There is no studio in this slice. The 18+ confirmation and consent follow in slice 2; slice 1 holds fake data only, so storing answers before consent exists is acceptable for this slice and never beyond it.

### Slice 2 — 2 Oct (screen-share, local)

The real instrument, and the first face of the studio:

- the 36-item sort, slider fine-tune, scoring and results screen, with the prototype's descriptions and validity disclaimer, reproducing the prototype's output for the same inputs;
- Section 1 and the separate Strengths assessment section, end to end, with their gates;
- the complete onboarding: baseline, reason, mentor contact, contact list;
- the 18+ confirmation and the consent step before any answer is stored;
- the studio's draft, preview and publish loop, with a schema-validated raw JSON editor as its first face.

### Slice 3 — 9 Oct (remote audience; private staging instance)

The distinctive claim, and a configurable pathway:

- the real observer flow and the self-versus-others comparison;
- Sections 2 and 3 end to end (timeline, calling statement, idea generator, role pictures, recaps);
- Sections 4 and 5 as plain text and reflection blocks;
- the closing ratings and summary;
- the offline **track**, with its hub;
- studio content forms for the text-bearing fields of the pathway document;
- a staging instance on Hetzner in an EU region, on an account owned by the content owner, seeded with fake data only.

### Agreed cut order, if time runs short

Cut in this order, first item first:

1. The simple real mentor flow (a tokenised, read-only view of shared sections); the mentor stays a stored contact plus the prototype's printable and copyable preview.
2. The studio content forms, which fall back to the raw JSON editor alone.
3. Tracks and the offline hub. The content owner wants to keep offline, so it ranks below the studio forms.
4. Observer invitations and the observer questionnaire. The aggregation, suppression and comparison screen are still built, fed by seeded observers marked as test data on the server and labelled as illustrative on screen.
5. The sort, scoring and results are never cut.

Sections 4 and 5 are already planned as plain text and reflection blocks, so there is nothing further to cut there.

## User Stories

### Access, age and consent

1. As a participant, I want to create an account with my email address and a password, so that my work is saved to me.
2. As a participant, I want to need a shared enrolment code to sign up, so that only people invited to the pathway can join.
3. As a participant, I want to confirm that I am 18 or over with a checkbox and not be asked for my date of birth, so that I share only what is necessary.
4. As a participant, I want a plain-language consent screen before anything I write is stored, so that I know how my reflective and religious answers are used.
5. As a participant, I want to decline consent and have nothing stored beyond my account, so that declining costs me nothing.
6. As a participant, I want to withdraw my consent later, so that I stay in control.
7. As a participant, I want to be asked again if the consent text changes in meaning, so that I am never bound by wording I did not see.
8. As a participant, I want the single available pathway to open automatically after login, so that I do not have to find it.
9. As a participant, I want a clear, intentional empty screen when no pathway is published, so that a misconfigured deployment does not look broken.

### Onboarding

10. As a participant, I want to rate four statements about my understanding of work and calling on a 1–10 scale at the start, so that I have a baseline to compare against later.
11. As a participant, I want to say why I am taking the workbook, so that my situation is on record.
12. As a participant, I want to name a mentor, or skip that step, so that I can involve someone if I choose.
13. As a participant, I want to list people who know me well, or skip the step, so that I can invite them to give feedback.
14. As a participant, I want to choose between the online track and the offline track, so that the workbook fits how I like to work.

### Hub, progress and gates

15. As a participant, I want a hub that shows all sections in my track with their status, so that I always know where I am.
16. As a participant, I want the next step highlighted, so that I am never unsure what to do.
17. As a participant, I want locked sections to stay locked even if I type their address, so that the order the author intended actually holds.
18. As a participant, I want to resume where I stopped, on any device, so that I can work in short sessions.
19. As a participant, I want my answers saved as I write, so that I never lose work by forgetting to press save.
20. As a participant, I want a gate to tell me exactly which requirement is unmet, so that I know what to do next.
21. As a participant, I want to mark a section complete myself once its gate passes, so that completion is a deliberate act.
22. As a participant, I want to revisit a completed section and see my earlier answers, so that I can reread and refine them.
23. As a participant, I want my progress to count only sections that apply to my track, so that the numbers are honest.

### Content and reflection blocks

24. As a participant, I want to read scripture passages and confirm I have read them before the activity opens, so that the activity is grounded in them.
25. As a participant, I want a hint at the top of each section stating the big question, so that I understand the task.
26. As a participant, I want video slots that say plainly when a video is not yet available, so that placeholders do not pretend to be real.
27. As a participant, I want long-text questions with room to write, so that I can reflect properly.
28. As a participant, I want short-text and single-choice questions where the pathway asks for them, so that simple answers are simple to give.
29. As a participant, I want a recap of my earlier answers where the pathway shows one, with an authored message when there is nothing to show yet, so that I am not shown an empty panel.

### The instrument and results

30. As a participant, I want to sort 36 statements into five buckets one card at a time, so that I make quick honest judgements.
31. As a participant, I want to undo my last sort, so that a slip of the finger is not permanent.
32. As a participant, I want sliders seeded from my bucket choices that I can fine-tune, so that I can refine within a bucket.
33. As a participant, I want the sort to be complete before I continue, so that the profile is based on all 36 statements.
34. As a participant, I want to see my APEST(d) profile and my PEP profile ranked, so that I can see my relative shape.
35. As a participant, I want the descriptions the content owner wrote beside each result, so that the results mean something.
36. As a participant, I want the validity disclaimer shown with my results, so that I treat them as indicative and not definitive.
37. As a participant, I want to expand the individual item scores behind each result, so that I can see how it was built.
38. As a participant, I want my result computed once and kept as it was calculated, so that later edits to the pathway never silently change it.

### Feedback from others

39. As a participant, I want to add the people I would like feedback from, one per row, so that each gets their own invitation.
40. As a participant, I want a unique link for each observer that I can copy and send however I like, so that I stay in control of how they are asked.
41. As a participant, I want to revoke a link and issue a fresh one, so that I can correct a mistake or chase a slow observer.
42. As a participant, I want to see how my view compares with observers' views once enough of them have answered, so that I can find hidden strengths and blind spots.
43. As a participant, I want the biggest gaps between my view and observers' views surfaced, so that I know where to look first.
44. As a participant, I want to see how much observers agree with each other, so that I can tell a consensus from a split.
45. As a participant, I want an explanation and no numbers while too few observers have answered, so that no single observer can be identified.
46. As a participant, I never want to see an observer's name next to their answers, so that observers can be honest.

### Sections 2 and 3

47. As a participant, I want to create chapters of my life and drop typed markers into them, so that I can lay out my story.
48. As a participant, I want to note the recurring threads I see across my timeline, so that patterns surface.
49. As a participant, I want to build a calling statement from a fixed sentence template and then edit it freely, so that I have something to start from.
50. As a participant, I want to generate possibilities through four lenses with rotating prompts, so that I explore widely.
51. As a participant, I want to star the possibilities that draw me, so that they feed later recaps.
52. As a participant, I want to develop two or three role pictures with a worked example to look at, so that a possibility becomes concrete.

### Sections 4 and 5, closing

53. As a participant, I want to reflect in writing on a growth plan and on a letter to my future self, so that the pathway completes even while these sections are plain.
54. As a participant, I want to answer the same four ratings at the end and see them beside the first set, so that I see how far I have come.
55. As a participant, I want a closing summary of my work, so that I have something to keep.

### Tracks and the offline way

56. As a participant on the offline track, I want to download the paper workbook, so that I can work through the reflection and scripture on paper.
57. As a participant on the offline track, I want to do the strengths assessment online, so that I still get my profile and the comparison.
58. As a participant on the offline track, I want to record the date I intend to finish, so that I have a target.
59. As a participant on the offline track, I want the closing ratings to open once I have done the assessment, so that I can finish when I finish the paper.
60. As a participant, I want to switch between tracks without losing any answer, so that changing my mind is safe.
61. As a participant, I do not want to be promised an email reminder the system cannot send, so that I can trust what the screen says.

### Mentor

62. As a participant, I want my mentor stored with my response and a printable or copyable preview of each section to hand to them, so that I can share my work.
63. As a participant, if time allows, I want to give my mentor a link that shows only the sections I have chosen to share, so that they can read without an account.

### Observers

64. As an observer, I want a unique link that stops working after a configurable period (30 days by default) or when the participant revokes it, so that access is limited.
65. As an observer, I want a privacy notice before the first question saying who asked, what is stored and what the participant will and will not see, so that I can decide whether to take part.
66. As an observer, I want to sort the same 36 statements about the participant, phrased about them and not about me, so that my answers are about them.
67. As an observer, I want to answer seven written questions about the participant, so that I can add what a sort cannot say.
68. As an observer, I want to be asked my relationship to the participant without typing my name, so that I am not asked for more than I need to give.
69. As an observer, I want to be told my name is never shown to the participant, and not that I am "completely anonymous", so that the promise made to me is one that can be kept.
70. As an observer, I want to withdraw and have my answers deleted, so that I keep control of what I contributed.
71. As an observer, I want a thank-you when I finish, so that I know it was received.
72. As an observer, I want to reach the questions by following my link, so that the flow works (the prototype's never does).

### Authoring in the studio

73. As an author, I want to edit a draft of the pathway without affecting anyone in progress, so that I can work safely.
74. As an author, I want validation errors that name where in the document the problem is, so that I can fix it.
75. As an author, I want to preview the pathway as a participant would see it, using synthetic state that never creates a real response, so that I can check my work without side effects.
76. As an author, I want to publish a draft to create a new immutable pathway version, so that the version a response was answered against is never altered afterwards.
77. As an author, I want a raw JSON editor with validation against the document's schema, so that I can make any change, including structural ones, from the first day the studio exists.
78. As an author, I want forms for the text-bearing parts of the document (prompts, scripture, item wording, lens prompts, gate messages), so that I can change wording without touching JSON.
79. As an author, I want an optional observer wording for each item, blank meaning the same as the participant's, so that items phrased about "you" can be phrased about "them".
80. As an author, I want a warning when text an observer will see says "you" or "your" and has no observer wording, so that I catch the problem before publishing.
81. As an author, I want each gate to list its clauses with a message for each, so that participants are told exactly what is missing.
82. As an author, I want to load a pathway document from a file with a command, so that I can work in version control before the studio can do everything.

### Operating and demonstrating

83. As the content owner, I want to see my own wording, scripture and items in the running app, so that it feels like my workbook.
84. As the content owner, I want the same answers to give the same profile as my prototype, so that I can trust the port.
85. As the content owner, I want the demo to say plainly when it is showing illustrative comparison data, so that no audience is misled.
86. As an operator, I want all configuration to come from the environment, so that a deployment can be stood up repeatedly for another organisation.
87. As an operator, I want the staging instance to hold only fake data, so that no real person's reflections are at risk before the legal footing exists.
88. As an operator, I want seeded and test records marked as such on the server, so that they can never be mistaken for a participant's work.
89. As a developer, I want the engine's scoring, gates and document validation to be testable without a browser or a database, so that the numbers are provable.

## Implementation Decisions

### Shape and stack

- Python and Django, PostgreSQL with JSONB, HTMX for interaction, Vite for focused JavaScript modules, and no single-page-application framework. Authentication is `django-allauth`.
- The Django ORM is the only ORM and migration system (ADR 0001).
- One deployment per organisation. There is no organisation model and no organisation column (ADR 0002). Anyone who can author is an author of the whole deployment, and the deployment takes all its configuration from the environment.
- Nothing authored is hardcoded outside the pathway document. An unconfigured application, or a pathway with sections but no content, renders an intentional empty state and never a hidden fallback.

### The pathway document and versions

- A **pathway document** is one JSON document holding the pathway's content, instrument, measurement and presentation. Identifiers for sections, blocks, items, constructs and buckets are stable, never positional and never reused for a different meaning.
- The document is validated against a JSON Schema and by an additional linter covering cross-references (for example, an item loading onto a construct that does not exist, or a gate clause naming an absent block).
- A pathway document is authored as a file in version control and loaded by a management command into an immutable **pathway version** row, stored with a content hash. Publishing from the studio creates a new immutable version the same way. A published version is never edited.
- A **response** records the pathway version it was answered against. What happens to a participant already in progress when a later version is published is not decided for this milestone. The default is that they stay on the version they started. A consequence for the demos: a republished change is seen by a participant who starts after it, not by one already in progress, so demonstrate content changes with a fresh participant.
- The document configures named behaviours and is never a language (ADR 0003): a gate is a list of clauses drawn from a fixed set, a **recap** picks a named view with parameters and an authored empty-state message, and a scoring method is chosen by name and parametrised by data. Adding a behaviour is a code release.
- A named scoring method is frozen once any response has been scored with it. A change in behaviour requires a new method name and never an edit.
- Any text field may be a single string or a pair keyed by role (participant, observer). Blank observer text means the same as the participant's.
- Text is escaped on output and never altered on input. Nothing executable exists anywhere in the document.

### Engine: sections, tracks, gates, progress

- Onboarding and closing are ordinary sections of the pathway. The engine owns account creation, the 18+ confirmation, consent, the hub, progress, locks and status; none of these are authored blocks. The participant's name and email come from the account, not a form block.
- A **track** is a participant-chosen ordered list of the pathway's sections with its own hub. A section may belong to more than one track. Answers are keyed by block, so they persist when a participant switches track. The track is chosen by a choice block in onboarding.
- Section order is a per-section list of the sections it requires. Locks and access are decided by the server on every request, never by hidden markup.
- A **gate** is a list of clauses from a fixed set (a block has an answer, a count of entries (optionally only those with any content), a count of distinct values, a minimum text length, "every entry has a value for a field", and combinations), each with its own authored message for the case where that clause fails. A gate is optional on a section. A clause that needs something other than an answer (such as "the comparison has been visited") is a new named clause type, added in code (ADR 0003).
- The engine re-checks a gate when a section is completed. Completing a section is an explicit participant action, enabled only when the gate passes.
- The hub, status chips, locks and next-step banner are derived by the engine from progress and are not authored blocks.
- Progress counts only the interactive blocks reachable in the participant's track.

### Blocks

- A block is only something an author would place and configure. Whatever can be derived from state belongs to the engine.
- The first set of block types is:
  - content: rich text (absorbing hint boxes and checklists), scripture reading with a confirm gate, video (placeholder that says so);
  - capture: agreement scale, short text, long text, single select, checkbox confirm, contact list;
  - bespoke: sort assessment (sort, fine-tune and results), sentence builder, idea generator, card builder, timeline board;
  - derived and mentor: recap, mentor brief.
- The growth-plan board and letter scheduling are not in the first set. Sections 4 and 5 use plain text and reflection blocks.
- Every block, however interactive, produces exactly one answer value. The server validates that value against the block's answer schema and never trusts the widget. Simple blocks use server-rendered HTMX. Interaction-heavy blocks (sort, timeline, idea generator) are named block types, each with a configuration schema and a Vite JavaScript module that owns its interaction. Adding a bespoke block is additive: a schema, a widget and a validator.
- The prototype's 31 block types were a documentation taxonomy. Several (lock cards, status cards, the next-step banner, the completion gate) are engine-derived and are not blocks.

### Responses, answers and results

- There is one response per participant per pathway version, with answers stored as JSON keyed by block identifier. Autosave writes one block's answer at a time and never re-serialises the whole response.
- Observer responses are separate records from the participant's and are owned separately. An observer never touches a participant's state (the prototype overwrote it).
- A **result** is computed when the sort is submitted and stored against that pathway version. Later versions never recompute it.
- There is no retake in this milestone. When retake is added it creates a new attempt and keeps the old ones, and comparisons always use the latest attempt.
- Test and seed records are marked as such on the server. A client-side flag never distinguishes them.

### The instrument and scoring

- The instrument is 36 items, each loading onto exactly one construct of APEST(d) (Apostle, Prophet, Evangelist, Shepherd, Teacher, deacon) and exactly one construct of PEP (Ponder, Ideate, Assess, Rally, Facilitate, Deliver). The item bank, the result descriptions, the personas and the validity disclaimer are migrated verbatim from the prototype reference.
- Buckets have named identifiers and an explicit order from weakest to strongest. The prototype's inverted stored integers never enter the new system. Seeds are as follows, taken from the prototype:

  | Bucket | Prototype id | Slider seed |
  |---|---|---|
  | Definitely not me | 5 | 10 |
  | Not really me | 4 | 25 |
  | Average / not sure | 3 | 45 |
  | Good at this | 2 | 65 |
  | Real strength | 1 | 85 |

- The scoring method is the prototype's, frozen and named as a compositional score: each construct's raw value is the sum of its six item values, and its percentage is its raw value divided by the grand total, rounded independently. Ties fall back to declaration order. Percentages are not asserted to sum to 100.
- Sliders left untouched keep their bucket seed, so a sort alone produces a complete profile.
- The rank-based colouring of PEP bars shares a colour between tied scores. The APEST bars use fixed per-construct colours.
- The prototype's unbalanced APEST×PEP item matrix and its compositional nature are ported as they are and recorded as content debt for the content owner. Neither is fixed silently.
- The comparison thresholds are data in the document: a gap of five percentage points or more is significant, and observer agreement is banded by range (up to 6 is strong agreement, up to 14 is some variation, above that is divided views). The comparison lists the five largest gaps across both frameworks.

### Observers (ADR 0005)

- An observer is identified by the contact record the participant created and a token unique to them, bound to it and held separately from the observer's answers. Each token accepts one submission. Observers type no name. A relationship is asked and stored but is never used to slice or filter results.
- A token is 32 random bytes, stored only as a hash. The link lives for a period set in the pathway document, 30 days by default, and can be revoked. The participant copies the link and sends it themselves; the application sends no email in this milestone.
- The observer sees a privacy notice before any question, stating who asked, what is stored and what the participant will and will not see. The copy states that their name is never shown to the participant and never that they are "completely anonymous".
- The observer sorts the same 36 items. Thirty-two are shared with the participant verbatim. Four say "you" or "yours" in the participant's wording and get observer wording: outlast them, different from theirs, matters to them, they could explain it. The observer screens are in the third person about the participant. The Christian framing is kept.
- The seven written questions are stored and never shown to the participant.
- Aggregation normalises per observer before averaging, keeps the per-observer values for the distribution strip, and hides every number below the minimum number of observers. That minimum is three and is set in the pathway document. Below it the participant sees an explanation and nothing else.
- Withdrawing deletes the observer's answers.
- The participant sees only how many observers have answered, never which invited person has (ADR 0005).
- Section 1's "comparison viewed" requirement is satisfied by visiting the comparison in either state, including the below-minimum explanation. Otherwise a participant would be locked out of every later section until three observers had answered, which could take weeks. (The prototype has the same trap: its empty state never sets the flag.)
- The fallback for the demo, if observer invitations are cut, is the same mechanism as seeding: observers created directly as server-marked test data, passing through the real aggregation and suppression, with an on-screen label whenever every contributing observer is test data. There is no separate fixture.

### Participants, access and consent (ADR 0004)

- Login is email and password through `django-allauth`, with email verification off during the fake-data phase. Google sign-in is additive later.
- Sign-up is closed by a shared enrolment code. There is no assignment model: anyone with an account sees the one pathway.
- Age is confirmed by an 18+ checkbox and no date of birth is stored.
- A consent step precedes any stored answer. It records the version of the consent text and a timestamp, is separate from enrolment, is withdrawable, and declining stores nothing beyond the account.

### Offline track

- The offline track's hub is derived like any other hub, from the track's sections: a paper-workbook section (a download and a target date the participant records), the online strengths assessment, and the closing ratings, which require the assessment. Switching to the online track is allowed at any time.
- The sort and its results are their own section, "Strengths assessment", belonging to both tracks and requiring only onboarding. In the online track, Section 1 keeps its scripture and reflection, links to the Strengths assessment section, and its gate requires the sort to be answered. Offline participants do the Strengths assessment section alone, as in the prototype. One consequence: the participant can reach the sort from the hub before reading Section 1's scripture, so scripture-first is no longer enforced.
- The paper workbook is assumed to exist as a file from the trial and is served as an asset attached to the pathway. If it does not, the download says plainly that it is coming.
- The target date is stored. The prototype's on-screen promise of a reminder email is removed until email delivery exists.

### Mentor

- The mentor is a stored contact with the prototype's per-section printable and copyable preview, and mentor briefs are authored content in the document.
- If time allows, a participant marks sections as shared and the mentor opens a tokenised, read-only link to exactly those sections, reusing the observer token machinery, including the same configurable link lifetime (30 days by default). There is no mentor account and no mentor answers.

### Studio

- The studio's essential work is the draft, preview and publish loop, which creates immutable versions. Preview uses synthetic participant state and never creates a real response. Publishing requires a validation pass.
- Editing surfaces arrive in this order: a raw JSON editor with schema validation on 2 Oct, content forms for the text-bearing fields by 9 Oct, and structural editing (adding, removing and reordering sections and blocks) after 9 Oct.
- Studio forms are generated from the document's JSON Schema, so the schema must stabilise before the forms are built, around 2 Oct.
- Authors are non-technical. Anything that would be safe only for a developer to edit is not acceptable as the primary path.

### Delivery and hosting

- Slices 1 and 2 are demonstrated by screen-share from a local instance. A staging instance is stood up before 9 Oct on Hetzner in an EU region, on an account owned by the content owner with the developer deploying into it, holding fake data only.
- Fake data uses reserved example domains. Seeded observers used to demonstrate the comparison are marked as test data on the server.

## Testing Decisions

- A good test drives external behaviour and asserts on what a participant, observer or author could observe (a rendered response, a stored answer, a refused request), never on how the engine is arranged inside. Tests survive refactoring of the internals.
- There are two seams, agreed with the developer:
  1. **The participant journey over HTTP**, through Django's test client against a real PostgreSQL database, with no mocking of the database. This covers the engine, gates, persistence, tracks, consent, observer token URLs and studio publish.
  2. **A pure core for scoring, gate evaluation and document validation**, exercised without a browser or a database.
- Journey tests cover, at least:
  - direct navigation to a locked section is refused by the server;
  - each prototype gate is reproduced with a message per failing clause;
  - completing a section is refused when its gate does not pass;
  - autosave of one block leaves other blocks' answers untouched;
  - a participant resumes on a fresh session with all answers present;
  - declining consent stores nothing beyond the account;
  - the enrolment code is required and the 18+ confirmation is enforced;
  - an observer token is refused when wrong, expired after its configured lifetime or revoked, and only its hash is stored;
  - observer answers never appear to the participant, and no aggregate appears below the minimum;
  - switching track keeps every answer;
  - publishing from the studio creates an immutable version and never modifies an existing one, and a preview creates no response;
  - an empty pathway renders the empty state.
- Pure-core tests use golden fixtures that reproduce the prototype's scoring output for fixed inputs. The prototype's stored bucket integers are inverted against the new ordering, so the mapping (prototype bucket 1 is the strongest bucket) is encoded once in the fixtures and not left to be applied by hand. Fixtures include an all-strongest and an all-weakest sort, which produce the same profile because the score is compositional. Rounding drift is respected, and no test asserts the percentages sum to 100.
- Pure-core tests also cover gate clause evaluation for every clause type, document validation errors carrying document paths, per-observer normalisation before averaging, the five-point gap rule, the agreement bands, tie-breaking by declaration order, and the linter's second-person warning.
- Browser tests for the Vite widgets are out of scope for this milestone. The widgets are checked by hand, and the server-side validator for each block's answer is covered by the two seams above.
- There is no existing test code in the repository. This spec sets the prior art: the golden-fixture approach for scoring, and journey tests for everything with a URL.

## Out of Scope

- Any change to the marketing brochure, blog, team pages, donate or newsletter surfaces of the prototype.
- The prototype's demo and tester tooling.
- Multi-tenancy (ADR 0002) and any organisation-management surface.
- An assignment model, and any way for a participant to find or choose among pathways.
- Under-18 participants (ADR 0004).
- The growth-plan board, and letter scheduling and delivery. Sections 4 and 5 are plain text and reflection blocks.
- Retake of the assessment.
- Structural editing in the studio (adding, removing, reordering sections and blocks) and any drag-and-drop editing.
- Real email delivery of any kind, including observer invitations, mentor invitations and reminders. Links are copied by hand.
- Real mentor access, unless time allows (first item in the cut order).
- PDF generation. The offline workbook is a served file.
- Real videos and resource-library content, which stay placeholders that say so.
- Migrating existing prototype exports or `localStorage` data. Nothing in the prototype's save format is reusable.
- Account-level features beyond sign-up and login: password reset, Google sign-in and a production identity provider.
- Browser tests for Vite widgets.
- Correcting the unbalanced item matrix or the compositional scoring (see Further Notes).
- The legal and compliance work listed under Further Notes. It is deliberately not in the scope of this milestone.

## Further Notes

### Legalities are parked, not forgotten

The developer does not want the legal detail to bog down the build, and it will matter eventually. This spec therefore treats it as a tracked list and not as a blocker. One line is firm: no real participant's data goes into any instance until consent, a named controller and a retention rule exist. Until then, every demo and the 9 Oct staging instance use fake data only.

Still open, to be raised when the design touches them:

- who the controller is once real participants arrive, and whether the arrangement (a Hetzner account owned by the content owner, with the developer deploying into it) works for everyone involved, which has not yet been checked;
- a retention rule, and deletion and export when consent is withdrawn;
- a data protection impact assessment;
- the policy for a participant asking to see observer feedback about them (the Article 15(4) conflict);
- processor agreements with the host and any email provider;
- the choice of an email provider, which is also blocked on delivery being built;
- the observer privacy notice wording and the consent text, which need writing before any real use.

Both UK and EU data protection law apply. The workbook's free text may contain special category data beyond religion (the hardship-and-loss markers solicit accounts of suffering), so the whole reflective corpus should be treated as potentially special category.

### Open content and product items

- **Unbalanced item matrix.** Shepherd and deacon items can never earn Ponder points, and Teacher items can never earn Rally points. The scoring is also compositional, so "strong across the board" cannot be expressed. Both are ported as they are and raised with the content owner as content debt. Fixing either changes every participant's results and would need a new scoring method or a new version.
- **Retake**, **letter scheduling and delivery**, **the growth-plan board** and **structural studio editing** are all deferred and are recorded above as out of scope.
- **Observer withdrawal after expiry.** An observer withdraws through their link while it is valid. How they withdraw once it has expired (for example, by contacting the deployment's operator) is not decided.

### Defaults assumed but not explicitly agreed

These were not discussed in detail. They are stated so the implementer does not have to guess, and any of them can be overturned:

- Participants already in progress stay on the pathway version they started when a later one is published.
- Sort card order is randomised per participant. Whether the order is recorded for reproducibility was not discussed.
- The contact list's minimum defaults to the prototype's five entries and is authored content. The minimum number of observers for any aggregate is three. These are different numbers because one gates the participant's onboarding and the other protects observers.
- The prototype's item-level "show scores" expander is kept.

### Glossary gaps

`CONTEXT.md` does not yet define **milestone** or **content owner** (the person who owns the content and direction of the first pathway). They are used in this spec in their ordinary sense. If any of them turns out to carry a domain meaning of its own, add it through `/domain-modeling`.

### Risk

Sections 1–3, the studio, the real observer flow and the offline track in 18 days, by one developer, is more than fits comfortably. The cut order exists for that reason. Watch slice 2 in particular: the instrument, Section 1, full onboarding and the studio's first face all land on 2 Oct.

### Sources

The prototype reference documents describe the behaviour being migrated, its traps and its content, and the two earlier plans remain useful for the observer, privacy and document-format thinking, though several of their decisions are superseded here (SQLAlchemy by ADR 0001, tenancy by ADR 0002, and the milestone names "Gate 1" and "Gate 2" by the plain use of "gate" for a completion predicate).
