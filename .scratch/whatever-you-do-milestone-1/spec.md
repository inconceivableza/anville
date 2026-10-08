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

A server-rendered Django application in which the *Whatever You Do* **pathway** is not code but a **pathway document**, loaded as an immutable **pathway version**, that the engine renders to a **participant**. Everything the prototype hardcoded (the 36 **items**, the **constructs**, the bucket-to-points seeds, the scripture, the lens prompts, the gate messages, the coach briefs) lives in that document. The engine owns the things that must not be authored: login, age confirmation, **consent**, the **hub**, progress, **locks**, gate evaluation, persistence and scoring.

The work lands in three demo slices. Each slice is demonstrable on its own.

### Slice 1 — 25 Sept (screen-share, local)

A real server-backed app, built on the content owner's content in a data file:

- sign-up (behind an enrolment code at the time; ticket 37 makes it optional per deployment and off), and login;
- the four baseline ratings, and one full **section** shaped as scripture read-confirm, then an activity, then a **gate**, then complete (the calling-statement section is the model, with a plain long-text activity in place of the sentence builder);
- Section 5's letter, with the four after-ratings required before it is sent (ticket 05);
- a hub showing all five sections, with locks enforced by the server;
- progress that survives a reload and a second device;
- the pathway document loaded by a command, so that editing one prompt in the file and reloading visibly changes the app.

There is no studio in this slice. The 18+ confirmation and consent follow in slice 2; slice 1 holds fake data only, so storing answers before consent exists is acceptable for this slice and never beyond it.

### Slice 2 — 2 Oct (screen-share, local)

The real instrument, and the first face of the studio:

- the 36-item sort, slider fine-tune, scoring and results screen, with the prototype's descriptions and validity disclaimer, reproducing the prototype's output for the same inputs;
- Section 1 and the separate Strengths assessment section, end to end, with their gates;
- the complete onboarding: baseline, reason, coach contact, contact list;
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

1. The simple real coach flow (a tokenised, read-only view of shared sections); the coach stays a stored contact plus the prototype's printable and copyable preview.
2. The studio content forms, which fall back to the raw JSON editor alone.
3. Tracks and the offline hub. The content owner wants to keep offline, so it ranks below the studio forms.
4. Observer invitations and the observer questionnaire. The aggregation, suppression and comparison screen are still built, fed by seeded observers marked as test data on the server and labelled as illustrative on screen.
5. The sort, scoring and results are never cut.

Sections 4 and 5 are already planned as plain text and reflection blocks, so there is nothing further to cut there.

### Sprints

The planning session of 25 Sept regrouped the tickets into sprints, and the 2 Oct demo regrouped them again. Where this differs from the slices above, it replaces them. Each ticket records its sprint on a `**Sprint:**` line.

- **Sprint 1, ended 2 Oct:** 09, 10a, 13a, 13b, 14a, 14b, 15a, 16a, 16b, 16c, 33 and 34 are done. 13c, 15b, 25 and 30 were left open and are placed below.
- **Sprint 2a, ends 8 Oct, before FaithTech (9–10 Oct):** 26 (staging, with email from a temporary domain), 37 (display name, email as username, the enrolment code optional and off), 32a (homepage copied from the prototype), 13c (the coach's link), 27 (the coach sees the results and comparison once the participant consents), 38 (results and comparison in words), 39 (scripture copyright notices), 40 (the workbook step, with Sections 2–4 hidden) and 41, split on 7 Oct into 41a (a header with sign out, and a pathway sidebar), 41b (the flow back to the hub and Section 1) and 41c (time estimates). 25 (coach preview and briefs) was split on 6 Oct into 25a (the coach's guide for Section 1) and 25b (a printable copy of Section 1), whose sprints are not yet decided: the coach view the content owner asked for is 27. The goal is the content owner's journey end to end for participants, coaches and observers: the opening questions, the strengths assessment, the workbook, the letter and the closing ratings. The workbook is a static PDF from the content owner, offered from the app, and replaces Sections 2–4 for now.
- **Sprint 2b, 12–16 Oct, after the regroup on Monday 12 Oct:** 22 (cut to the closing ratings and summary), 15b (observer relationship and withdrawal), 42 (observers skip fine-tuning quickly), 43 (observer reminders), 28a (password reset, once email exists), 36 (observer timestamps), 30 (tie-break).
- **Sprint 3 or later:** 41d (loading the participant once per page, from 41a's review), 32b (the homepage from content), 31a and 31b (written questions; the 2 Oct demo asked for a higher minimum than three for written answers, released separately from the scores, and how to protect them is not settled), 13d (removing a contact), 35 (vocabulary rename), 11 and 12 (the studio's JSON editor and preview; until then the document is edited as a file and loaded by command), 17–21 (Sections 2 and 3 and recaps, parked while the static workbook stands in for them; building them online is a short follow-up once wanted), 23 (tracks and the offline hub, largely overtaken by the workbook step), 24 (studio content forms and observer wording), any OAuth or OIDC work (28b, and a production identity provider), structural editing in the studio (adding components through the GUI), results that read better when scores are evenly high (a pie chart, absolute values, or a scoring method the author chooses), a waitlist for the organisational version (churches, charities, leadership teams), which collects contact details and so needs a privacy notice, and inline formatting in authored text (authored text is plain today, so the prototype's italics such as the *not* in Section 1's reflection prompt, its bold phrases such as "Aim for **quantity, not quality**", and the bulleted lists in its hints are lost; a small fixed markup, escaped first, used by every block template and stripped wherever text goes out plain, noted in ADR 0003; about half a day to a day, found in ticket 09), and a gate checklist on a part of a section (ticket 41b: a part shows no "Mark complete" and so no checklist, which suits the Strengths assessment, whose sort says what it needs, but a part with a text gate would never say what is unmet). None of the last five has a ticket yet. 10b (the faithful port's mentor step) has no sprint and may never be done.
- **Raised at the 2 Oct demo, not yet decided or ticketed:** see Open content and product items, "From the 2 Oct demo". FaithTech volunteers are offered cohort management, custom content and styling per cohort, a psychological safety survey, or their own idea; none of these is in this milestone.
- **Engine tidying without a ticket, from ticket 09's code review:** what a `section_link` does is spread over `engine/hub.py`, `engine/views.py` and `engine/document/lint.py` rather than defined once in `engine/document/blocks.py`, as the README asks; a hook on `BlockType`, like `opens_what_follows`, would gather it. The linter refuses a link that holds back its own section, but not two sections each holding on the other, which shuts both the same way; that needs a search of the whole pathway, worth building once a pathway has more than one held link. "Section link" and "time estimate" are not yet in `CONTEXT.md`.

So FaithTech sees, on staging: the homepage, onboarding with a display name, Section 1 and the strengths assessment, observers' assessments and the comparison in words, the coach accepting and seeing the results and comparison, the workbook and the letter with its closing ratings (ticket 05), with Sections 2–4 hidden. The closing summary follows in 2b. The first three items of the cut order no longer apply as written: the coach flow has come back, cut down, into 2a, and the studio and the offline track are sprint 3 or later. Item 4, seeded observers in place of invitations and the questionnaire, is no longer worth taking, since only 15b remains of it.

## User Stories

### Access, age and consent

1. As a participant, I want to create an account with my email address and a password, so that my work is saved to me.
2. As an operator, I want to be able to require a shared enrolment code to sign up, so that a deployment can admit only people invited to the pathway (off by default; ticket 37).
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
12. As a participant, I want to name a coach, or skip that step, so that I can involve someone if I choose.
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

### Coach

62. As a participant, I want my coach stored with my response and a printable or copyable preview of each section to hand to them, so that I can share my work.
63. As a participant, I want my coach, once they have accepted, to see my results and comparison through their link when I consent, so that they can read it without an account.

### Observers

64. As an observer, I want a unique link that stops working after a configurable period (30 days by default) or when the participant revokes it, so that access is limited.
65. As an observer, I want a privacy notice before the first question saying who asked, what is stored and what the participant will and will not see, so that I can decide whether to take part.
66. As an observer, I want to sort the same 36 statements about the participant, phrased about them and not about me, so that my answers are about them.
67. As an observer, I want to answer six written questions about the participant, leaving blank any I can't answer, so that I can add what a sort cannot say.
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
- A block type stays in the engine while any stored pathway version uses it: a version is never edited, so a response pinned to it would otherwise break. Retiring a block type needs its responses moved to a later version first (found in ticket 25a, when a local response was left on a version holding a block type since dropped).
- Any text field may be a single string or a pair keyed by role (participant, observer). Blank observer text means the same as the participant's.
- Text is escaped on output and never altered on input. Nothing executable exists anywhere in the document.

### Engine: sections, tracks, gates, progress

- Onboarding and closing are ordinary sections of the pathway. The engine owns account creation, the 18+ confirmation, consent, the hub, progress, locks and status; none of these are authored blocks. The participant's name and email come from the account, not a form block.
- A **track** is a participant-chosen ordered list of the pathway's sections with its own hub. A section may belong to more than one track. Answers are keyed by block, so they persist when a participant switches track. The track is chosen by a choice block in onboarding.
- Section order is a per-section list of the sections it requires. Locks and access are decided by the server on every request, never by hidden markup.
- A **gate** is a list of clauses from a fixed set (a block has an answer, a count of entries (optionally only those with any content), a count of distinct values, a minimum text length, "every entry has a value for a field", and combinations), each with its own authored message for the case where that clause fails. A gate is optional on a section. A clause that needs something other than an answer (such as "the comparison has been visited") is a new named clause type, added in code (ADR 0003).
- The engine re-checks a gate when a section is completed. Completing a section is an explicit participant action, enabled only when the gate passes, and leads back to the hub, which points at the next step (ticket 41b).
- A section may be a **part** of another (`part_of`), as the Strengths assessment is of Section 1 (ticket 41b). The hub and sidebar list it within that section; it has no completion of its own and is complete once its gate passes, worked out rather than stored; it opens only once the participant reaches that section's link to it (for the Strengths assessment, once Section 1's reading is confirmed), or with that section if it has no link, or by its own requirements alone where that section is not in the track; and its page, its results and its comparison lead back to that section.
- The hub, status chips, locks and next-step banner are derived by the engine from progress and are not authored blocks.
- Progress counts only the interactive blocks reachable in the participant's track.

### Blocks

- A block is only something an author would place and configure. Whatever can be derived from state belongs to the engine.
- The first set of block types is:
  - content: rich text (absorbing hint boxes and checklists), scripture reading with a confirm gate, video (placeholder that says so);
  - capture: agreement scale, short text, long text, single select, checkbox confirm, contact list;
  - bespoke: sort assessment (sort, fine-tune and results), sentence builder, idea generator, card builder, timeline board;
  - derived: recap.
- A coach brief is not a block: it is carried by what the coach is shown, which for now is the sort's results and comparison (ticket 25a; see Coach).
- The growth-plan board and letter scheduling are not in the first set. Sections 4 and 5 use plain text and reflection blocks.
- Every block, however interactive, produces exactly one answer value. The server validates that value against the block's answer schema and never trusts the widget. Simple blocks use server-rendered HTMX. Interaction-heavy blocks (sort, timeline, idea generator) are named block types, each with a configuration schema and a Vite JavaScript module that owns its interaction. Adding a bespoke block is additive: a schema, a widget and a validator.
- The prototype's 31 block types were a documentation taxonomy. Several (lock cards, status cards, the next-step banner, the completion gate) are engine-derived and are not blocks.

### Responses, answers and results

- There is one response per participant per pathway version, with answers stored as JSON keyed by block identifier. Autosave writes one block's answer at a time and never re-serialises the whole response.
- Observer responses are separate records from the participant's, never written by the participant, and deleted with the participant's response. An observer never touches a participant's state (the prototype overwrote it).
- A **result** is computed when the sort is submitted and stored against that pathway version. Later versions never recompute it.
- There is no retake in this milestone. When retake is added it creates a new attempt and keeps the old ones, and comparisons always use the latest attempt. Until then the database refuses a second sort through the unique constraint `one_result_per_sort_per_response` (ticket 06), which retake has to replace with its attempt model.
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
- The words for the answers follow `CONTEXT.md` (assessment, placement, self-result, observer result, observer average; ticket 35). The block type `sort_assessment` and the block id `strengths-sort` keep their names, since loaded pathway versions are immutable and answers are stored against the block id.
- The rank-based colouring of PEP bars shares a colour between tied scores. The APEST bars use fixed per-construct colours.
- The prototype's unbalanced APEST×PEP item matrix and its compositional nature are ported as they are and recorded as content debt for the content owner. Neither is fixed silently.
- The comparison thresholds are data in the document: a gap of five percentage points or more is significant, and observer agreement is banded by range (up to 6 is strong agreement, up to 14 is some variation, above that is divided views). The comparison lists the five largest gaps across both frameworks, ties in the order the constructs were declared. A gap of nothing has no direction and reads as a modest gap, where the prototype said "You rate higher (+0)" (developer's call, ticket 16b). The agreement bands are read narrowest first whatever order they are written in, and a range above them all takes a label of its own, so no document can leave a range without a band.
- Results and the comparison show each construct as a standing in words, never a percent (ticket 38): its share as a percent of an even share of its framework, against thresholds in the document (`presentation.standing`), read highest first. The comparison also says whether others see a construct higher, lower or much the same, by the same significant gap and direction as the largest gaps (`presentation.comparison.seen_by_others`). Each construct is drawn on a line from 0 to twice an even share, so the even share is always in the middle and the line is the same for every participant and on both pages; a share beyond the end sits at the end with an arrow past it (developer's call, ticket 38, in place of variant F's line ending just past the largest share).
- On the comparison the participant's dot carries a person icon above it and the observers' a group icon below, and the words beside them still name each ("You: Strong", "Others: Leading"), as variant F did, rather than the icons replacing them. Each profile card ends in one tick, "Show how the n responses were spread", in place of an expander per construct: while ticked, each construct shows each observer's dot in place of the observers' mean, and how far they agree under its line, which is otherwise hidden; each person's standing, lowest first, is given to screen readers only, not shown (developer's calls, ticket 38).

### Observers (ADR 0005)

- An observer is identified by the contact record the participant created and a token unique to them, bound to it and held separately from the observer's answers. Each token accepts the observer assessment once and the written part once (ADR 0008). Observers type no name. A relationship is asked and stored but is never used to slice or filter results.
- A token is 32 random bytes, stored only as a hash. The link lives for a period set in the pathway document, 30 days by default, and can be revoked. Taking a contact off the list revokes their link. The participant copies the link and sends it themselves; the application sends no email in this milestone.
- Because the participant holds a copy of every link, the observer claims theirs on first use: starting exchanges the token for a secret only the observer holds, and the participant's copy stops working. Answering and withdrawal are reachable only through the claimed secret, and sent answers are never shown back through any link (tickets 13b, 15a, 15b, 31a). A participant can still tell whether a given person has started or answered, and could answer in their place.
- The observer sees a privacy notice before any question, stating who asked, what is stored, what the participant will and will not see, and how to withdraw. The copy states that their name is never shown to the participant and never that they are "completely anonymous", and promises nothing about whether the participant can tell that a given person has started or answered (they can, see above). It never says the participant "won't know who wrote this" (ADR 0008). The notice says nothing of the written answers until ticket 31a asks for them and gives their account; it describes only what is true at the time (ticket 27).
- The observer sorts the same 36 items. Thirty-two are shared with the participant verbatim. Four say "you" or "yours" in the participant's wording and get observer wording: outlast them, different from theirs, matters to them, they could explain it. The observer screens are in the third person about the participant. The Christian framing is kept.
- The observer assessment is sent and counts on its own; the written part is then offered as a second part (ADR 0008). Its six questions follow the content owner's qualitative-strengths prototype, which replaces the original prototype's seven, and are asked of the participant too. Observers may leave any blank. The participant sees observers' written answers without names, shuffled per question, and none until at least three observers have sent the written part with at least one answer in it. The minimum counts over the written part as a whole, not per question, so a question may show a single answer (ADR 0008).
- Sent answers outlive the link: revoking or reissuing it, or taking the contact off the list, leaves them in place, and revoking and reissuing always work. The cost is that someone can be counted twice (ADR 0007).
- Aggregation scores each observer's sort on its own before averaging, keeps the per-observer values for the distribution strip, and hides every number below the minimum number of observers. That minimum is three and is set in the pathway document. Below it the participant sees an explanation and nothing else.
- A document may raise the minimum but never set it below three: fewer would come too close to exposing one observer's answers (developer's call, ticket 14a). The mean is each observer's unrounded share averaged and rounded once, not the prototype's average of already-rounded percents, so it can differ by one from the mean of the rounded values that place each observer's dot and standing in the comparison's spread (ticket 38). The per-observer values are given in ascending order, never in the order observers answered, so a participant who knows who answered when cannot pair a value with a person.
- Withdrawing deletes the observer's answers.
- An observer's answers belong to the participant's response and are deleted with it: they are personal data about the participant, so erasing the participant's answers erases what others said about them too (ticket 14b).
- The participant sees only how many observers have answered, never which invited person has (ADR 0005).
- Section 1's "comparison viewed" requirement is satisfied by visiting the comparison in either state, including the below-minimum explanation. Otherwise a participant would be locked out of every later section until three observers had answered, which could take weeks. (The prototype has the same trap: its empty state never sets the flag.) A visit is the participant pressing "Compare with how others see you →" on the results page, a POST, never loading the comparison's address: a browser may load an address ahead of time (Chrome preloads from the address bar) without the participant seeing it. Opening the comparison by a typed or bookmarked address shows it but does not count (developer's call, ticket 16c).
- The fallback for the demo, if observer invitations are cut, is the same mechanism as seeding: observers created directly as server-marked test data, passing through the real aggregation and suppression, with an on-screen label whenever every contributing observer is test data. There is no separate fixture.

### Participants, access and consent (ADR 0004)

- Login is email and password through `django-allauth`, with email verification off during the fake-data phase. Google sign-in is additive later.
- Sign-up can be closed by a shared enrolment code, required unless the deployment turns it off from the environment, so a deployment that forgets the setting admits nobody without a code; it is turned off in every environment for now (ticket 37). There is no assignment model: anyone with an account sees the one pathway. The account's username is its email, emails are unique, and a display name given at sign-up names the participant to observers and their coach.
- An account without a display name is named by the part of its email before the @, and only an account with no email at all (one made with `createsuperuser`) by its username, so that no observer is asked to answer for a blank. An email longer than a username can hold (150 characters) is refused at sign-up, rather than cut short into a username that is not the email (developer's call, ticket 37).
- Accounts use Django's built-in user, with the display name held alongside it. If the user table itself ever needs to change (for example, dropping the username), switch to a custom user model before any real participant is added: after that, switching means migrating real accounts (developer's call, ticket 37).
- Age is confirmed by an 18+ checkbox and no date of birth is stored.
- A consent step precedes any stored answer. It records the version of the consent text and a timestamp, is separate from enrolment, is withdrawable, and declining stores nothing beyond the account. There is no account page yet, so a "Your consent" link at the foot of the hub leads to it (ticket 08); when an account page exists, that link belongs there.

### Offline track

- The offline track's hub is derived like any other hub, from the track's sections: a paper-workbook section (a download and a target date the participant records), the online strengths assessment, and the closing ratings, which require the assessment. Switching to the online track is allowed at any time.
- The sort and its results are their own section, "Strengths assessment", belonging to both tracks and requiring only onboarding. In the online track, Section 1 keeps its scripture and reflection, links to the Strengths assessment section, and its gate requires the sort to be answered. Offline participants do the Strengths assessment section alone, as in the prototype. Ticket 41b, the developer's call, ends the consequence once accepted here, that the sort could be reached before Section 1's scripture: as a part of Section 1, the Strengths assessment opens only once Section 1's reading is confirmed, while in a track without Section 1 it still opens with onboarding.
- The paper workbook is assumed to exist as a file from the trial and is served as an asset attached to the pathway. If it does not, the download says plainly that it is coming.
- The target date is stored. The prototype's on-screen promise of a reminder email is removed until email delivery exists.

### Coach

- The coach is a stored contact, and coach briefs are authored content in the document, carried by what the coach is shown. While the workbook replaces Sections 2–4, only Section 1's brief is in the app, on the Strengths assessment's sort: the coach sees it on their link with the results, before them, once they have accepted and the participant shares the results, as the mock-up's "What happens next" promises the guide with the results; and the participant can open it beside the consent to share those results, on their comparison, where they decide what the coach sees (ticket 25a; moved there from the foot of Section 1 by the developer, 8 Oct, as the prototype showed it on its "Send to Mentor" screen). The coach's "Thank you — Sam will be told" is said only on the page accepting leads to; later visits open "You're Sam's coach". The workbook carries the briefs for Sections 2–4, reworded by the content owner, and the letter has none. The prototype only showed the brief to the participant, saying it was "sent with this", though nothing was sent.
- The prototype's per-section and whole-workbook printable and copyable preview is cut to a copy of the participant's Section 1 work, the only section still answered in the app (ticket 25b). It shows their own results with no observer figures: the prototype showed every item with the observers' average for it, which the aggregation does not compute and which would show more than the comparison does, and the comparison reaches the coach through their link with the participant's consent (decided with the developer, 6 Oct).
- Once the coach has accepted, the participant may tick "Give my coach access to my results and this comparison" on their comparison, once they have visited it, and the coach's link then shows their results and the comparison, read-only and as the participant sees them, until the consent is withdrawn or the link revoked or reissued, or the coach changed (ticket 27, cut down at the 2 Oct demo from sharing chosen sections). The consent is kept on the coach's link, and the observers' privacy notice says the participant may show what they see to a trusted third party (ADR 0011). Sharing other sections waits for the online journey. It reuses the observer token machinery, including the same configurable link lifetime (30 days by default). There is no coach account and no coach answers beyond accepting or declining.
- The coach chosen in onboarding gets a link of the observer kind (ticket 13c) asking them to accept or decline six commitments. Only accepted or declined is stored: one commitment affirms the coach's own faith, so which boxes were ticked would be special category data about the coach. An acceptance still implies it, since accepting needs every box, and is kept anyway (ADR 0010). The answer belongs to the link: revoking or reissuing asks again, and a link is answered once (developer's call, ticket 13c). The participant sees only the outcome; after a decline they may choose someone else or carry on without a coach, and a partial agreement is never shown (decided with the developer, 29 Sept). Saving another coach or removing this one revokes the link (30 Sept). Accepting or declining is not the "real coach access" that Out of Scope and the cut order leave for later: the coach sees no section of the participant's. As with observers, the participant holds a copy of the link, so they could accept on the coach's behalf. Claiming doesn't help, as the participant can claim as easily as use; only delivery that reaches the coach (email, or a coach account) would, and neither is in this milestone.
- The prototype says "mentor"; the content owner's coach-selection mock-up changes this to "coach" throughout. Wording migrated from the prototype says "coach" wherever it meant the mentor role.

### Studio

- The studio's essential work is the draft, preview and publish loop, which creates immutable versions. Preview uses synthetic participant state and never creates a real response. Publishing requires a validation pass.
- Editing surfaces arrive in this order: a raw JSON editor with schema validation on 2 Oct, content forms for the text-bearing fields by 9 Oct, and structural editing (adding, removing and reordering sections and blocks) after 9 Oct.
- Studio forms are generated from the document's JSON Schema, so the schema must stabilise before the forms are built, around 2 Oct.
- Authors are non-technical. Anything that would be safe only for a developer to edit is not acceptable as the primary path.

### Delivery and hosting

- Slices 1 and 2 are demonstrated by screen-share from a local instance. A staging instance is stood up before 9 Oct on Hetzner in an EU region, on an account owned by the content owner with the developer deploying into it, holding fake data only.
- Fake data uses reserved example domains. With the enrolment code off, staging's sign-up is open, so sign-up and the homepage say plainly that it is a demo, to use made-up details, and that data may be wiped (ticket 26). Seeded observers used to demonstrate the comparison are marked as test data on the server.

## Testing Decisions

- A good test drives external behaviour and asserts on what a participant, observer or author could observe (a rendered response, a stored answer, a refused request), never on how the engine is arranged inside. Tests survive refactoring of the internals.
- There are two seams, agreed with the developer:
  1. **The participant journey over HTTP**, through Django's test client against a real PostgreSQL database, with no mocking of the database. This covers the engine, gates, persistence, tracks, consent, observer token URLs and studio publish.
  2. **A pure core for scoring, gate evaluation and document validation**, exercised without a browser or a database.
- Each ticket starts by agreeing with the developer its seams and a short list of behaviours to test, one line each; that list is the cap. The two seams below serve most tickets; propose another only for a genuinely new module with logic of its own. Sort each proposed line with these questions (agreed 30 Sept). They guide judgement rather than replace it: keep or cut a test for a reason they don't cover, and say why when proposing the list.
  1. If it broke, would someone be harmed, or data leak or be lost? Keep it: refusals, what is stored, what is never logged, token security.
  2. Is it the complicated part? Keep one test per outcome of the branching (a checklist's verdicts, scoring, gates).
  3. Is it already guaranteed elsewhere? Cut it: engine-wide behaviour (escaping, the no-JavaScript and htmx responses, locked sections, logging) is tested once in the engine, not again per block; structure is the linter's.
  4. Does it assert authored wording or layout? Cut it: the pathway document and the drift test own the copy, and layout is a hand check in `docs/manual-checks.md`.
  5. Would it break in a refactor that changes no behaviour? Cut it or rewrite it.
- A ticket's list is roughly one or two tests per criterion plus its refusals, about 5–10 tests, not 50. Rank the list by risk so the developer can cut from the bottom. If a logic or privacy bug reaches a hand check or a demo that a test would have caught, add that test and loosen the cap for that kind of behaviour; if nothing gets through for a few tickets, the cap is about right. The journey tests so far repeat engine behaviour per block and assert wording (the coach checklist alone has 52 tests); folding them into engine tests is tidying without a ticket.
- The list below is the pool a ticket's list is drawn from, not a list to copy whole. Journey tests cover, at least:
  - direct navigation to a locked section is refused by the server;
  - each prototype gate is reproduced with a message per failing clause;
  - completing a section is refused when its gate does not pass;
  - autosave of one block leaves other blocks' answers untouched;
  - a participant resumes on a fresh session with all answers present;
  - declining consent stores nothing beyond the account;
  - the enrolment code is required when the deployment turns it on, and not asked for when off, and the 18+ confirmation is enforced;
  - an observer token is refused when wrong, expired after its configured lifetime or revoked, and only its hash is stored;
  - no single observer's answers reach the participant: no aggregate appears below the minimum, no written answer appears until three observers have sent the written part with at least one answer, written answers are never attributed and come in no stable order across questions, and nothing sent is read back through any link;
  - an observer answers and withdraws only through their claimed link, the participant's copy can do neither once claimed, and each part locks once sent;
  - sent answers survive revoking, reissuing and removing the contact;
  - an observer's blank written answers are sent as blank, and a written part with no answer in it doesn't count toward the minimum;
  - switching track keeps every answer;
  - publishing from the studio creates an immutable version and never modifies an existing one, and a preview creates no response;
  - an empty pathway renders the empty state.
- Pure-core tests use golden fixtures that reproduce the prototype's scoring output for fixed inputs. The prototype's stored bucket integers are inverted against the new ordering, so the mapping (prototype bucket 1 is the strongest bucket) is encoded once in the fixtures and not left to be applied by hand. Fixtures include an all-strongest and an all-weakest sort, which produce the same profile because the score is compositional. Rounding drift is respected, and no test asserts the percentages sum to 100.
- Pure-core tests also cover gate clause evaluation for every clause type, document validation errors carrying document paths, scoring each observer on their own before averaging, the five-point gap rule, the agreement bands, tie-breaking by declaration order, and the linter's second-person warning.
- Browser tests for the Vite widgets are out of scope for this milestone. The widgets are checked by hand, and the server-side validator for each block's answer is covered by the two seams above.
- There is no existing test code in the repository. This spec sets the prior art: the golden-fixture approach for scoring, and journey tests for everything with a URL.

## Out of Scope

- Any change to the marketing brochure, blog, team pages, donate or newsletter surfaces of the prototype. The homepage alone is in scope, copied from the prototype (ticket 32a), and later generated from content (ticket 32b).
- The prototype's demo and tester tooling.
- Multi-tenancy (ADR 0002) and any organisation-management surface.
- An assignment model, and any way for a participant to find or choose among pathways.
- Under-18 participants (ADR 0004).
- The growth-plan board, and letter scheduling and delivery. Sections 4 and 5 are plain text and reflection blocks.
- Retake of the assessment.
- Structural editing in the studio (adding, removing, reordering sections and blocks) and any drag-and-drop editing.
- Real email delivery of any kind, including observer invitations, coach invitations and reminders. Links are copied by hand.
- Real coach access, unless time allows (first item in the cut order).
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
- a retention rule, and deletion and export when consent is withdrawn. Until it is decided, withdrawing closes the pathway and keeps every stored answer, and a journey test pins that so any change is deliberate (ticket 08);
- a data protection impact assessment;
- the policy for a participant asking to see observer feedback about them (the Article 15(4) conflict);
- how an observer withdraws once their link has stopped working (see Open content and product items);
- processor agreements with the host and any email provider;
- the choice of an email provider, which is also blocked on delivery being built;
- the lawful basis for keeping a coach's acceptance, which implies their faith since accepting needs every commitment ticked (ADR 0010);
- the observer privacy notice wording and the consent text, which need writing before any real use. The consent text in `access/templates/access/consent.html` is a marked draft; raise `CONSENT_TEXT_VERSION` in `access/consent.py` when it is replaced, so everyone is asked again (ticket 08);
- a privacy notice and a contact address for the public homepage, which links to neither yet; the prototype's Privacy Policy and Terms links and its Contact section were left out until they exist (ticket 32a);
- the licence, if the project goes open source. Crossway's ESV notice forbids quoting the ESV "in any publication made available to the public by a Creative Commons license", and the NIV and ESV are quoted under their publishers' permission, which no open licence of ours can pass on. The pathway documents hold that scripture, so an open licence over the whole repository would claim to license text we do not own. Three options, none chosen yet: license the code openly and leave the quoted scripture outside the licence, which works only while the scripture is kept to the pathway documents (today the homepage template also quotes Colossians 3:23 until ticket 32b moves it into content); move to a public-domain translation, such as the BSB or WEB, before going open source; or fetch the scripture at run time, through a Bible API, so it is never in the repository (its terms and privacy are in ticket 39's research). The repository has no licence yet, and a test fails if one is added while a pathway quotes scripture, so the choice is made here first (ticket 39);
- the Anglicised ESV notice, found only in the Bible Society of South Africa's licensed copy, to be confirmed with HarperCollins in writing before any real use (ticket 39). HarperCollins's own 2012 copyright page confirms the publisher, the "Anglicized" spelling and the "Unless otherwise indicated" form, but no HarperCollins source online gives the current digital notice (checked 7 Oct; ticket 39's research).

Both UK and EU data protection law apply. The workbook's free text may contain special category data beyond religion (the hardship-and-loss markers solicit accounts of suffering), so the whole reflective corpus should be treated as potentially special category.

### Open content and product items

- **Unbalanced item matrix.** Shepherd and deacon items can never earn Ponder points, and Teacher items can never earn Rally points. The scoring is also compositional, so "strong across the board" cannot be expressed. Both are ported as they are and raised with the content owner as content debt. Fixing either changes every participant's results and would need a new scoring method or a new version.
- **Kept only because the prototype did it** (raised in ticket 14a, to review with the content owner, and likely to change soon; the first three are frozen in `compositional_share`, so changing any is a new named method, never an edit):
  - Each percent is rounded half up, like JavaScript's `Math.round`, and each construct on its own, so a framework's percents need not add up to 100.
  - The score is a share of the grand total (see the item matrix above).
  - Ties fall back to declaration order (ticket 30 may settle this).
  - The comparison's thresholds (a five-point gap; agreement bands at 6 and 14) and the bucket slider seeds (10, 25, 45, 65, 85) are the prototype's numbers. They are data in the document, so they change without code.
  - The standings' thresholds (125, 105 and 85% of an even share) and the comparison's "Others place this higher/lower", "Much the same" are variant F's placeholders, also data in the document, until the content owner gives real ones (ticket 38). They are not symmetric about an even share, and the developer kept them so (6 Oct).
- **Retake**, **letter scheduling and delivery**, **the growth-plan board** and **structural studio editing** are all deferred and are recorded above as out of scope.
- **Observer withdrawal after expiry.** An observer withdraws through their link while it is valid. How they withdraw once it has expired, or once the participant has revoked or reissued it or removed them, which leaves their answers in place (ADR 0007), is not decided (for example, by contacting the deployment's operator). Whatever binds the answers (ticket 15a) must keep them traceable to the observer, held apart from the participant, after the invitation and contact are gone, so a later way to withdraw stays possible.
- **Observer autosave.** Not in ticket 31a; whether an observer's written answers are ever saved before they send them is open for 31b, leaning never. The prototype saves each field as it is typed, since losing minutes of typing is costly, but an unsent draft is data about the participant that nothing uses, and observers would need telling in the privacy notice. If it ever happens, a draft is reachable only through the claimed link, never the participant's copy, or the participant could read one observer's answers before they are mixed with others'. Without it, an observer who leaves before sending comes back through their claimed link to an empty written part.
- **Batched release of observers' answers.** Not decided; ticket 31b decides it, for the comparison's numbers (16a, 16b) as well as the written answers. Without batching, a participant who sends one more link and notes what changed sees exactly what that person added, even without trying, since links go out on different days; in the paper trial, a participant de-anonymised critical feedback by matching one person's answers across questions. Batching costs this: a late answer may never be released, and withdrawal must still take effect at once. And it has a limit: it stops a participant working out who wrote what by accident, not on purpose. One who sets out to identify someone can add contacts they answer for themselves, which defeats both batching and the minimum, and nothing in this milestone prevents it. The developer was shown the recommendation to batch and left the decision to 31b. Ticket 16b's distribution strip sharpens the case: before batching, the one new value on each construct is exactly that person's, where the mean alone gave it to within the rounding (ADR 0005). If 31b batches, two calls are already made (developer's call, 2 Oct): the comparison changes only once at least two new observers have answered since it last changed, a number set in the pathway document that a document may raise but never set below two; and while answers wait, the participant sees how many have answered and how many the comparison shows, since they can already tell who has answered from the links.
- **From the 2 Oct demo.** Agreed: the fine-tune sliders stay fine-grained, not 10 or 20 steps; results and the comparison drop their numbers for words (ticket 38); the participant may go on to the workbook once their own assessment is done and they have invited their coach and observers, never waiting on observers' answers (ticket 40); the coach sees only the results and comparison, behind one consent (ticket 27). Raised, not decided:
  - *One shared observer link.* Every observer gets the same link; on following it they create an account or receive a link of their own to come back and finish. This would replace issuing a link per contact (13a), and touches ADRs 0005 and 0009 and withdrawal (15b). The content owner's concern: a personal link makes an "anonymous" survey feel less anonymous.
  - *Scores and written answers protected differently.* The content owner sees little risk in the scores, since they are all strengths and add up the same, and much more in written answers, where an anecdote can identify its writer even among three. So written answers need a higher minimum than three (ADR 0008 says three), released in their own batch, so a participant is never held back waiting for them. How to protect them is open, and is why 31a and 31b moved out of sprint 2. Whether the scores are batched (above) is still 31b's call, now with the content owner's view that they need it less.
  - *Closing collection.* "Once it's done, it's done": collection closes once enough have answered, or after a deadline the observer is told of, and late answers are refused. Not decided; it interacts with batching and withdrawal.
  - *Reminders.* The participant cannot tell who has answered, so the system should remind observers who have not (ticket 43, which needs email and must not let anyone match answers to contacts).
  - *How many contacts to ask for.* Two in onboarding for now (ticket 10a); the prototype asked for five, and the comparison needs three.
  - *Bible translations.* Copyright notices are ticket 39. A Bible API letting a reader or author choose the translation was suggested for later. Until then the translations stay as they are, a mix (developer's call, 7 Oct): the pathway documents' passages are ESV, with British spellings that suggest the Anglicised edition; the homepage's Colossians 3:23 is NIV; and the workbook is NIV where it names or quotes one. The workbook's notice is the content owner's to add to the booklet, not the app's. The publishers' limits on quoting without permission (ticket 39's research) are the cap: each allows up to 500 verses of its translation, provided no complete book is quoted (the ESV also caps any one book at half) and scripture stays under 25% of the work's text. The 25% is the limit to watch: scripture is about 21% of the faithful port by a rough word count. Each translation's notice is on a credits page every page links to. The document's translation's notice begins "Unless otherwise indicated", as Crossway allows where more than one translation is quoted, so only a passage from another translation names it beside its reference, as the homepage's "(NIV)" does (developer's call, 7 Oct). The homepage's verse belongs to no pathway, so the credits page carries its NIV notice itself until ticket 32b moves the homepage into content, and the pathway documents declare only the ESV. The stored ESV text now matches the ESV Anglicised (developer's call, 7 Oct): "baptizing", "for ever" and the em dash in 1 Peter 4:11 restored, and the cuts in Acts 18:2–3 and Psalm 37:7 marked with an ellipsis. A passage stopping partway through its last verse may instead say so in its reference ("Psalm 37:3–7a"); Psalm 37 keeps the ellipsis. Still open from ticket 39: the content owner is to be told of these calls and the corrected wording; the workbook needs its own notices (the printed Anglicised ESV notice and Hodder's NIV notice), and its unlabelled quotes their abbreviations, which is the content owner's to add; and the Anglicised ESV notice is to be confirmed with HarperCollins (see Legalities are parked, not forgotten).
  - *Impact and mid-funnel metrics.* The content owner wants to know how far participants get and whether outcomes improve (for example the share at peace, against a 42% baseline) as the course changes; top-of-funnel visits can come from an ordinary site analytics tool. A plan for it is to be made. Any tracking needs its own privacy notice and ADR.
  - *Setup for volunteers.* Before FaithTech, check that the README takes a newcomer from nothing to a running app.
- **The Workbook section (ticket 40, developer's calls, 6 Oct).** *Whatever You Do* leaves out Sections 2–4, which the faithful port keeps, and offers the content owner's printed workbook in their place, as a PDF served only to a participant who has reached the section. "Workbook" here names that booklet, which `CONTEXT.md` does not yet define (it avoids "the workbook" for the pathway itself); a glossary entry is for `/domain-modeling`. The Workbook requires Section 1, whose gate already holds the sort and the comparison visit, and the letter requires the Workbook, which has no gate. "Invited" is a new clause, `links_issued`, on Section 1's gate, so the participant is told what is missing, rather than a lock on the Workbook that could only say "Locked": it counts working links (issued, not revoked or expired), never answers, so nobody waits on anyone. Two observers' links, the number onboarding asks for now (a number in the document; the comparison needs three to show anything). A coach's link is needed too, even by a participant who skipped the coach in onboarding, since the booklet has its coach conversations built in; a coach who declined still counts as invited. Until the finished PDF arrives the draft stands in, saved from the Word file, and the Workbook page says it is a draft.
- **How many coach conversations.** The workbook says "three conversations with your coach built into this booklet" and holds Conversations Two to Four; Section 1's, online (ticket 25a), makes four, where the homepage says "3 conversations, roughly an hour each". To settle with the content owner.
- **Coach briefs (ticket 25a).** Section 1's brief is the original prototype's Session 1 brief, word for word. It suits the Strengths assessment, now a part of Section 1 (ticket 41b), as its questions are about the results and the comparison. Three mismatches are left for the content owner:
  - *The homepage promises more than the app does.* Its coach paragraph says "we send them what they need before each conversation", but nothing is sent, and only Section 1's brief is in the app; the workbook carries the others. The developer chose to leave the homepage's wording as it is for now (8 Oct), so the ticket's criterion that the homepage promises only what the app does is not met. Rewording it waits for the content owner, with the number of conversations above, or for ticket 32b, which moves the homepage into content.
  - *The letter has no brief.* The prototype gave none for Section 5, and none is added here.
  - *"Session 1 – Their gifts".* The brief's title says *Session* where the workbook says *Conversation* (Conversations Two to Four), and *Their* where the coach's page names the participant. It is the prototype's wording, kept as it is until the content owner rewords it.
- **Prototypes not yet planned.** The content owner's prototypes in `Prototypes for reference/` that no ticket covers yet. Each is later work; what it would change is listed so the planning that takes it up starts from the conflicts:
  - *Contact loop* (`contact-loop-prototype.html`). After sending, an observer is thanked and offered the course for themselves, and asked again once the participant finishes; they may also pass it on, or offer to coach someone through the 13c commitments. Against what is decided: its first screen shows the observer their own answers, where sent answers are never shown back through any link (Observers; Testing Decisions); it replaces 15b's plain thank-you; its data keeps answer times on the invitation beside the contact's email, which ticket 36 removes and ADR 0009 rules out; it records which observer became a participant, which needs a privacy notice and ADR, as other tracking does; and telling observers the participant has finished discloses something about the participant, so needs their say. Its second ask needs email (tickets 26, 43).
  - *Organisations waitlist* (`organisations-waitlist.html`). The waitlist named under Sprints: a page of organisations' details and plans, scored into leads, linked from the homepage, which ticket 32a does not yet do. It needs a privacy notice. It collects interest, so it does not touch ADR 0002's one deployment per organisation.
  - *Quarterly check-in* (`quarterly-checkin-prototype.html`). Check-ins after the course, with the letter sealed until about twelve months on and the closing ratings asked again then, blind to the earlier answers. It needs letter scheduling and delivery, out of scope here, and email; keeping a letter and ratings for a year needs the retention rule still open (Legalities are parked, not forgotten); paper participants type their plan in, which ties it to the offline track (ticket 23). It is how the workbook's promise that the letter is "sealed until then" would be kept (ticket 40).
- **To show the content owner, from ticket 09** (the developer's calls, to confirm, ideally at the 2 Oct demo):
  - Section 1 leaves out the prototype's "Complete — view your results" line; the Strengths assessment's status chip says it instead.
  - While the reflection waits for the sort, the page shows no gate message, where the prototype said "Complete the Strengths Assessment to continue."
  - The results page leads back to the Strengths assessment, where it is completed, not to Section 1. Replaced by ticket 41b: the Strengths assessment is a part of Section 1, as in the prototype, with no completion of its own, and its page, the results page and the comparison lead back to Section 1.
  - The minimum-length messages add the figure: "(at least 10 characters)".
  - The gate is a checklist beneath "Mark complete", met requirements ticked.
  - The time estimates are ours, as the prototype gave none: "About 1 minute" for onboarding, "About 10 minutes" for the Strengths assessment, none for Section 1 (it cannot be finished without the longer sort), and "? min" for Sections 2–5 until they are built.
  - The sort's progress bar fills to 80% over the 36 cards and holds there through fine-tuning.
- **To show the content owner, from ticket 10a** (the developer's calls, to confirm, ideally at the 2 Oct demo):
  - The reason for taking the course is asked straight after consent, not on the sign-up form, and without the prototype's "– please choose".
  - The coach step can be skipped, unlike in the coach-selection prototype. Its questions' button reads "Continue →", not "See how it looks →", and "I'm still confident" no longer says "You've said yes to all six".
  - Going ahead asks for the coach's name and email with the original prototype's tick, reworded: "I've spoken to this person and they're happy to receive a link from me about coaching me through this course." Saving shows "Sam is your coach" on the coach page, with "Choose someone else" and "Remove"; choosing someone else says Sam stays until another is saved, with "Keep Sam".
  - Saving stays on the coach page, in place of the original prototype's pair "I'll sort this later →" / "Save and continue →". The coach page's way on reads "I'll sort this later →" until a coach is kept, then "Continue with Sam →".
  - "Who knows you best?" asks for two people in *Whatever You Do* for now, not five, and leaves out "you can preview the exact email below".
- **To show the content owner, from ticket 13b** (the developer's calls, to confirm, ideally at the 2 Oct demo):
  - The observer's welcome keeps the prototype's "You've been invited" and its "What you'll do" sentence, drops "Your responses are completely anonymous" and the first-name box, and adds a privacy notice marked as a draft: what is kept, what the participant sees of the answers, and withdrawal. Its button reads "I'm answering for {name} →", in place of "Start →".
  - The participant is named by the part of their email before the @ until accounts hold a name; ticket 37 adds a display name, with this as its fallback.
  - Starting shows the observer a link of their own to bookmark; the link they were sent then reads "This link has already been used".
- **To show the content owner, from ticket 15a** (the developer's calls, to confirm, ideally at the 2 Oct demo):
  - The observer's sort widget names the participant by that same name: "Sort {name}'s strengths", "Choose the bucket that fits {name} best", "How strong is each one in {name}?", buckets "Definitely not {name}" and "Not really {name}", and sliders from "Not {name}" to "Real strength". It ends in "Send my assessment →".
  - After sending, the observer reads the prototype's thanks without "submitted anonymously": "Your assessment has been sent. It will help {name} understand how God has designed them – that's a real gift."

### Defaults assumed but not explicitly agreed

These were not discussed in detail. They are stated so the implementer does not have to guess, and any of them can be overturned:

- Participants already in progress stay on the pathway version they started when a later one is published.
- Sort card order is randomised per participant. Whether the order is recorded for reproducibility was not discussed.
- The contact list's minimum defaults to the prototype's five entries and is authored content. The minimum number of observers for any aggregate is three. These are different numbers because one gates the participant's onboarding and the other protects observers.
- The prototype's item-level "show scores" expander is kept.

### Glossary gaps

`CONTEXT.md` does not yet define **milestone**. It is used in this spec in its ordinary sense. If it turns out to carry a domain meaning of its own, add it through `/domain-modeling`.

### Risk

Sections 1–3, the studio, the real observer flow and the offline track in 18 days, by one developer, is more than fits comfortably. The cut order exists for that reason. Watch slice 2 in particular: the instrument, Section 1, full onboarding and the studio's first face all land on 2 Oct.

### Sources

The prototype reference documents describe the behaviour being migrated, its traps and its content, and the two earlier plans remain useful for the observer, privacy and document-format thinking, though several of their decisions are superseded here (SQLAlchemy by ADR 0001, tenancy by ADR 0002, and the milestone names "Gate 1" and "Gate 2" by the plain use of "gate" for a completion predicate).
