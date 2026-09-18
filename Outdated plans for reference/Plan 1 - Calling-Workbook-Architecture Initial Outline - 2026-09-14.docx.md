**Calling Workbook Platform**

Technical architecture and questionnaire format

Design document · 16 September 2026

This document sets out the recommended architecture for a web platform on which a person completes a structured self-assessment workbook, invites people who know them to answer a parallel set of questions about them, and receives a combined report. It covers data modelling, infrastructure, authentication, compliance, the questionnaire document format, library selection, and the administration and authoring workflow.

All library metrics quoted in Part Four were taken from GitHub and the npm registry on 14 September 2026 and should be re-checked before any final decision.

# **Part One — System overview**

## **1.1 What the system does**

Three participant roles interact with one workbook instance:

* **Participant** — works through a multi-section workbook combining written content, scripture, card sorting, ranking, rating scales and long-form reflective writing. Owns their data and controls who is invited.

* **Invited contact (observer)** — answers a parallel, differently worded version of a subset of the questions about the participant. Holds no account and arrives via a single-use link.

* **Mentor** — optionally named by the participant, sees a summary the participant chooses to share.

The system's distinctive requirement is the join between these: a participant's self-assessment and several observers' assessments must be scored on the same constructs and presented side by side, with the observers' identities withheld.

## **1.2 Findings from the prototype**

Three issues in the single-page prototype materially affect the design.

### **Invitation model**

The prototype generates one shared link copied to all contacts. The requirement is one unique link per contact, which makes contacts a first-class database entity rather than a client-side list, and enables per-contact tracking, reminders, revocation and expiry.

### **Anonymity claim**

The observer screen states that responses are "completely anonymous" while collecting the respondent's first name and relationship. Storing the name makes the data pseudonymous, not anonymous, and makes the observer a data subject with their own rights. The wording must change to a claim that can be honoured, for example "your name is never shown to the participant".

### **Special category data**

The workbook is explicitly religious in framing and content. Religious belief is special category data under Article 9 of the GDPR. This raises the lawful-basis requirement to explicit consent and strengthens the case for infrastructure under direct control within the EU.

# **Part Two — Data architecture**

## **2.1 Recommended model**

Use a **relational spine with JSONB payloads**, not a single JSON document per person and not full normalisation.

Identity, access, lifecycle, consent and audit live in ordinary tables. Answer content lives in JSONB columns. A narrow derived table carries the handful of values that are actually charted.

## **2.2 Why not one document per person**

A single document per participant fails on five counts:

1. A participant and several observers write concurrently, so one document produces lost updates.

2. Erasing one observer's contribution on request would require rewriting the participant's document.

3. Access control is per-fragment — the participant sees aggregates but never identities — which is awkward to enforce inside a single blob.

4. The self-versus-others comparison is an aggregation across respondents, not a document read.

5. The minimum-response threshold that protects observer anonymity is a query, not a field.

## **2.3 Why not full normalisation**

A fully normalised question/option/answer schema is the opposite error. The sealed letter, timeline, roadmap and card-sort bucket ordering are idiosyncratic structures that would generate many joins and constant migrations while the content is still changing.

## **2.4 Schema outline**

| Table | Purpose and notable columns |
| :---- | :---- |
| users | Authentication identities, managed by the auth library. |
| workbooks | One per user per cycle, so the workbook can be retaken and compared. Carries status, instrument\_version, created\_at. |
| workbook\_sections | Section payloads as JSONB. The flexible half of the model. |
| contacts | Invited people: name, email, relationship, workbook\_id. Identity held separately from answers. |
| invitations | contact\_id, token\_hash, sent\_at, opened\_at, submitted\_at, expires\_at, revoked\_at. |
| responses | invitation\_id (null for the participant's own), submitted\_at, payload JSONB, instrument\_version. |
| response\_items | Narrow projection derived on submit: response\_id, question\_key, value\_num, value\_text, rank. |
| consents | subject, purpose, lawful basis, consent text version, timestamp. |
| audit\_log | Who read or changed what, and when. |
| instruments | The pathway document itself, versioned and immutable once published. |

**response\_items** is the component most often skipped and most often regretted. Writing it on submit turns the comparison chart, the construct averages and any future cohort reporting into a single clean SQL query instead of JSON-path manipulation. The JSONB payload remains the source of truth; the narrow table is a projection that can be rebuilt at any time.

## **2.5 Stable keys and versioned instruments**

Two commitments are needed early. Answers must be keyed by stable question identifiers rather than by position or DOM identifier, and those identifiers must be frozen once published. The instrument definition itself must be stored in the database and versioned, so that a response captured in 2026 remains interpretable after a question is reworded in 2027\.

## **2.6 Migration path from the prototype**

The prototype's existing snapshot and restore functions already constitute a document schema. The client's autosave can be pointed at an API endpoint using the same shape as the JSONB body, with individual fields promoted to columns as the model settles. This avoids a rewrite at the point of moving from local storage to a server.

# **Part Three — Infrastructure**

## **3.1 Server-based versus serverless**

The recommendation is server-based, and the reasoning is about lock-in and data residency rather than performance.

|  | Serverless | Server-based |
| :---- | :---- | :---- |
| Operations | Nothing to patch; scales to zero | Patching, backups, monitoring are yours |
| Cost at this volume | Cheap compute, but paid glue | Predictable, roughly €10–20 per month |
| Lock-in | High — via platform KV, cron, queues, auth and blob storage rather than the compute itself | Low — Docker, Postgres and SMTP move anywhere |
| Data residency | Logs and metadata hard to pin down on US-owned platforms | Fully determined by the chosen data centre |
| Long-running work | Poor fit; PDF report generation does not suit a function | Straightforward |
| Database connections | Requires a pooler | Direct |

The mitigation, should serverless ever become desirable, is to write a plain HTTP application using no platform primitives — only Postgres, S3-compatible storage and SMTP. Kept to that discipline, the choice becomes reversible, which is the real objective.

## **3.2 Database**

**PostgreSQL 18**, using JSONB. No separate NoSQL store.

Postgres provides ACID guarantees for the invitation state machine, JSONB with GIN indexes for the document portions, row-level security as a defence-in-depth backstop, pgcrypto for application-level encryption, and full-text search — in one engine with one backup story.

Of the document stores considered: MongoDB is SSPL rather than OSI-approved open source; CouchDB is Apache-2.0 and strong at offline sync but weak at the cross-document aggregation this system depends on; SurrealDB is BSL. None offers anything Postgres does not already provide at this scale.

The sealed letter should be encrypted at the application layer with a key held outside the database, so that a database administrator or a leaked dump does not expose it. The prototype presents it as sealed; the implementation should make that true.

## **3.3 Hosting**

**Hetzner Cloud**, in Falkenstein, Nuremberg or Helsinki. A German company, so no US CLOUD Act exposure. Resources must be kept out of Hetzner's Ashburn and Hillsboro regions.

Hetzner offers no managed PostgreSQL service. Three viable approaches:

* **Self-managed in Docker** on the same host, with pgBackRest or wal-g archiving WAL to a Hetzner Storage Box plus a second copy at a different EU provider. Cheapest, and adequate at this scale provided restores are actually tested.

* **Ubicloud managed Postgres**, which runs inside Hetzner's German data centres from roughly $15 per month and provides automated backups and point-in-time restore.

* **Scaleway or OVHcloud managed Postgres**, if a fully managed EU service with a support contract is preferred.

Deployment via Kamal or Coolify, both of which are Docker underneath and therefore portable to any VPS.

# **Part Four — Authentication and access control**

## **4.1 Protocols and library**

OAuth 2.1 with OpenID Connect for Google, Microsoft and Apple. For a TypeScript application, **Better Auth** (MIT) is the recommendation: it runs inside the application and stores users in the project's own Postgres, reached version 1.6 in May 2026, and covers email and password, social providers, magic links, passkeys, two-factor authentication and rate limiting. For Python, django-allauth is the mature equivalent.

A standalone identity provider — Keycloak (Apache-2.0) or Authentik (MIT core) — is the wrong shape for a single application. It would mean operating a second stack purely to log users in. Revisit only if a second application is added or SAML becomes necessary for institutional customers.

## **4.2 Passwordless by default**

Offer Google sign-in and magic links, with no password storage at all. This removes credential stuffing, password reset flows, hashing decisions and a substantial share of breach surface in a single decision. Email and password can be added later if users demand it.

## **4.3 Observer token design**

Observer access is separate from authentication entirely.

* 32 random bytes, base64url encoded.

* Stored as a SHA-256 hash only, never in plaintext.

* One row per contact; expiry of 30 to 60 days; revocable.

* Rate-limited by IP address.

* URL of the form /r/\<token\>, containing no email address or name.

* A cookie set on first open so a partially completed form can be resumed.

* The participant's name is not revealed until the token validates.

## **4.4 Access control**

| Role | May see |
| :---- | :---- |
| Participant | Their own workbook in full; observer results in aggregate once the response threshold is met; never an observer's identity alongside their answers. |
| Observer | Only their own response, only via their token, write-once and then locked. |
| Mentor | Only what the participant has explicitly chosen to share. |
| Administrator | The minimum necessary, with every access written to the audit log. Sealed letters remain encrypted and unreadable. |

Enforce in the application through a single policy module, with row-level security in Postgres as a backstop. Item-level disclosure rules must be enforced server-side when a report is assembled, independently of what the report definition requests.

# **Part Five — Transactional email**

Invitation emails contain the participant's name and the fact that they are being assessed, so the content is personal data and residency matters.

| Provider | Residency | Assessment |
| :---- | :---- | :---- |
| Scaleway TEM | France, EU only | Recommended. Cleanest residency position, SMTP and REST, generous free tier. |
| Mailjet | EU, Sinch-owned | Recommended alternative; already familiar, good API. |
| Mailgun | EU region available | Acceptable fallback; US parent company. |
| SendGrid | EU residency on Pro and Premier only | Requires an EU subuser, EU endpoint and EU dedicated IP. |
| Postmark | US only | Excluded. No European region for data, content, metadata or logs. |

Send through an abstraction — nodemailer over SMTP is sufficient — so that switching provider is a configuration change. Use a dedicated subdomain for transactional mail, configure SPF, DKIM and DMARC, never mix transactional with marketing sending, and warm the domain slowly, since most invitations will go to personal mailboxes at the large consumer providers.

# **Part Six — Data protection**

## **6.1 The subject access conflict**

This is the non-obvious problem and it should be planned for before it arises.

A participant has a right of access under Article 15 to personal data concerning them. Observers' free-text answers about their character and their struggles are personal data concerning them. A determined participant can therefore request the raw feedback, which collides directly with what was promised to the observers.

Article 15(4) permits restriction where access would adversely affect the rights and freedoms of others, and that is the ground to stand on. To make the position survivable:

* Never promise anonymity that cannot be delivered.

* Hold observer identity in a separate table from their answers, so identity can be erased without destroying the contribution.

* Suppress all observer results below three responses, and four for the more sensitive blocks.

* Summarise rather than quote the most sensitive free-text answers, so that no observer is identifiable by their phrasing.

* Document the policy for handling such requests before the first one arrives.

## **6.2 Operational requirements**

* A record of processing activities.

* A data processing agreement with each processor — hosting, email, error tracking.

* Explicit consent capture for the religious-belief aspect, with the consent text version recorded in the consents table.

* A retention rule with actual deletion, for example purging invitations 90 days after submission and workbooks after two years of inactivity.

* Self-service export and deletion for participants.

* Error tracking that does not export data to the United States; self-hosted GlitchTip is a straightforward option.

# **Part Seven — The pathway document format**

The questionnaire is defined as a single versioned JSON document, referred to as a pathway. It contains sections, items, scriptures and resources, invitation configuration, email templates, scoring rules and report definitions. A JSON Schema, a worked example and a linter accompany this document.

## **7.1 Four layers**

The format keeps apart four things that are tempting to merge. Merging them is what makes questionnaire systems impossible to change later.

| Layer | Keys | Who edits | Consequence of change |
| :---- | :---- | :---- | :---- |
| Content | sections, resources, messages | Anyone, including a copywriter | None |
| Instrument | items | Author, carefully | Additive only; identifiers are permanent |
| Measurement | constructs, scoring, aggregation | Author, deliberately | Breaks comparability with earlier responses |
| Presentation | reports | Anyone | None |

Delivery configuration — flows and invitations — sits alongside these, defining who answers what and how invitations are issued.

## **7.2 What a question indicates**

An item never carries a score. It **loads onto a construct**, and the construct declares its own kind. This is what allows the same machinery to express quite different kinds of measurement.

### **Unipolar — how much of A**

The default: one named quality, from none to a great deal. Several items may load the same construct, in which case the construct score is the weighted mean. A reverse-keyed item uses a weight of −1.

{ "id": "tenacity", "kind": "unipolar",  
  "scale": { "min": 0, "max": 100, "unit": "percent" } }  
   
"scoring": { "loads": \[ { "construct": "tenacity", "weight": 1,  
    "transform": { "kind": "linear", "from": \[1,5\], "to": \[0,100\] } } \] }

### **Bipolar — a position between A and B**

Two named poles with a neutral middle. The scale straddles zero; the negative pole sits at the minimum and the positive pole at the maximum. A midpoint answer on the source scale maps to exactly zero.

{ "id": "orientation", "kind": "bipolar",  
  "scale": { "min": \-100, "max": 100 },  
  "poles": {  
    "negative": { "id": "consolidating", "label": "Consolidating" },  
    "positive": { "id": "initiating",    "label": "Initiating" } } }  
   
"transform": { "kind": "linear", "from": \[1,7\], "to": \[-100,100\] }

Use bipolar where the two ends are genuinely opposed trade-offs. Use two unipolar constructs where a person could plausibly be high on both, which is usually the case for strengths.

### **Ranking and card sorting — relative, not absolute**

Drag-ranking and forced sorting produce **ipsative** data: scores are relative within one person and sum to a constant. Two consequences follow, both enforced by the linter.

6. Normalise with ipsative\_percent rather than percent\_of\_max.

7. Mark the construct as not comparable. Ranking one item first out of six does not mean the same thing for two different people, so absolute levels should not be charted across people without a caveat.

Each option carries its own construct and the item declares a single transform for all of them.

{ "id": "energy-rank", "type": "ranking",  
  "options": \[ { "id": "wonder", "label": "Wonder", "construct": "wonder" } \],  
  "scoring": { "optionScoring": {  
      "transform": { "kind": "rank\_to\_points", "topScore": 6, "step": 1 } } } }

Card sorting uses a bucket\_to\_points lookup table, so the distance between "sometimes" and "often" is an explicit decision rather than an accident of bucket order.

### **Index — derived from other constructs**

No item touches it; it is a weighted combination of other constructs, useful for a headline figure or for showing movement between the start and end of a workbook.

### **Free text — not scored**

Free-text items set an analysis mode instead of scoring: verbatim, themes, or wordlist.

## **7.3 Role-specific wording**

The same item is phrased differently depending on who is answering. Any text field accepts an object keyed by role identifier.

"prompt": {  
  "self":     "What are you doing when you are most energised?",  
  "observer": "What is {{participant.firstName}} doing when they  
               seem most energised?" }

This is what keeps the self and observer instruments genuinely comparable. Two separately worded items would give two different measurements presented as one.

## **7.4 Aggregation**

Defaults are set at document level and overridden per construct.

| Setting | Guidance |
| :---- | :---- |
| observerMethod | mean for ratings, mean\_of\_ranks for ranking, modal\_bucket for sorts where the most common pile is more meaningful than an average. |
| normalise | ipsative\_percent for anything rank-derived, percent\_of\_max otherwise. |
| minResponses | Three is the floor. Four is safer for sensitive blocks, because with three responses a distinctive answer identifies its author. |
| dispersion | Prefer range or standard deviation over none. Disagreement between observers is often the most interesting finding in the report. |
| excludeSelfFromObserverStats | Keep true, or the participant's own view drags the comparison towards itself. |

## **7.5 Specifying the display**

A report is an audience, a set of source roles, and an ordered list of blocks. Each block names constructs or items and one or more **series** identifying which population to draw. One series produces a self-report; two or more produce a comparison. The same block types serve both, which is why aggregating the participant's answers and aggregating the contacts' answers need no separate machinery.

| Block type | Use for |
| :---- | :---- |
| score\_bars, ranked\_list | One population, ordered results. |
| comparison\_dots | Self against others. A dot plot reads considerably better than a radar chart for gaps. |
| diverging\_bars | Bipolar constructs, drawn either side of a centre line. |
| gap\_table | The blind-spot engine. gapDirection of others\_higher surfaces unrecognised strengths; self\_higher surfaces overestimation. |
| verbatim\_list | Free-text answers as written. |
| theme\_summary | Free text summarised, so nobody is identifiable by their phrasing. |
| narrative | Conditional prose; the first variant whose condition passes is shown. |

The two halves of the gap analysis need different framing. Others rating the participant higher than they rate themselves is encouraging and can be shown early. The participant rating themselves higher than others do is the difficult one and warrants a higher response threshold and gentler surrounding copy.

Conditions are declarative data, not code:

{ "when": { "metric": "score", "construct": "orientation",  
            "series": "self", "op": "gte", "value": 35 },  
  "text": "You are a starter. Expect to feel restless once  
           something is running well." }

There is no eval and nothing executable anywhere in the format. This is what makes it safe to accept an imported pathway and render it in a live preview. Had JavaScript expressions been permitted in conditions, the preview feature would have been a remote code execution path.

## **7.6 The renderer boundary**

A form library is used as a renderer only, never as the source of truth. Item identifiers, constructs, scoring, aggregation, reports and privacy flags remain in the pathway document; only the drawing of standard item types is delegated.

"render": { "engine": "surveyjs",  
  "element": { "type": "rating", "name": "orientation-pull",  
               "rateMin": 1, "rateMax": 7 } }

The embedded element is verbatim library JSON, and its name must equal the item identifier. Card sort and drag-rank remain native, because no form library models them. Keeping the boundary at the render key means changing renderer later is a mechanical change to one key.

## **7.7 Versioning**

Four rules keep historical data meaningful:

8. A published version is immutable. Editing creates a draft with a new version number.

9. Every stored response records the pathway identifier and version.

10. Item identifiers are never reused for a different question. Retire rather than repurpose.

11. Changing a scale, a construct, or which construct an item loads onto requires a migration entry against the previous version, failing which that version's data is flagged as not comparable and excluded from trend charts.

# **Part Eight — Library evaluation**

Figures below were collected on 14 September 2026 from GitHub and the npm registry.

## **8.1 Form renderers**

| Library | Stars | Forks | First release | Last commit | Licence | Targets |
| :---- | ----: | ----: | :---- | :---- | :---- | :---- |
| react-jsonschema-form | 15,896 | 2,338 | Dec 2015 | 14 Sep 2026 | Apache-2.0 | React |
| Formbricks | 12,937 | 2,517 | — | 14 Sep 2026 | AGPL-3.0 \+ EE | Platform |
| Formily | 12,576 | 1,596 | Feb 2019 | 21 Jun 2025 | MIT | React, Vue |
| HeyForm | 8,971 | 707 | — | 9 Sep 2026 | AGPL-3.0 | Platform |
| JSON Editor | 4,904 | 698 | Sep 2014 | 25 Aug 2026 | MIT | Vanilla |
| SurveyJS Form Library | 4,868 | 927 | Mar 2016 | 14 Sep 2026 | MIT | Vanilla, React, Vue, Angular |
| FormKit | 4,762 | 208 | Feb 2022 | 24 Jul 2026 | MIT core | Vue |
| LimeSurvey | 3,719 | 1,122 | — | 14 Sep 2026 | GPL-2.0 | Platform |
| ngx-formly | 2,969 | 583 | Sep 2017 | 8 Sep 2026 | MIT | Angular |
| OhMyForm | 2,890 | 449 | — | Archived | AGPL-3.0 | Platform |
| JSONForms | 2,739 | 424 | May 2016 | 14 Sep 2026 | MIT | React, Vue, Angular |
| uniforms | 2,102 | 238 | May 2016 | 12 Jan 2026 | MIT | React |
| Form.io renderer | 2,087 | 1,110 | Apr 2016 | 2 Sep 2026 | MIT (server OSL-3.0) | Vanilla |
| Vueform | 1,510 | 115 | Jul 2022 | 22 Jun 2026 | MIT core | Vue |

### **Assessment**

Star counts mislead here. react-jsonschema-form has three times the stars of SurveyJS but is the wrong category: it renders a form from a JSON Schema describing the **answer data**, so one would be specifying the shape of the response rather than the presentation of the question. Formily's figure is inflated by its enterprise user base, and its default branch last moved in June 2025\.

**SurveyJS Form Library is the recommendation.** The ten-year history with commits this week is the relevant signal, not the star count. It is the only option supporting plain JavaScript alongside the frameworks, and it ships a native ranking question type that covers the energy-profile drag order outright, leaving only the card sort as custom work. The constraint is the licensing split: the Form Library is MIT, but Creator, Dashboard and PDF Generator are commercial, so the visual builder should not be part of the plan.

**JSONForms is the credible alternative** if that split is unacceptable. Its separation of a data schema from a UI schema mirrors the separation of scoring from render already adopted here, it is MIT throughout with Eclipse Foundation backing, and it is actively developed. Against it: no vanilla JavaScript target, a smaller widget set, and more custom renderers to write.

OhMyForm is listed deliberately. With 2,890 stars, an AGPL licence and an apparently healthy history, it is now archived — the argument against building on any survey platform rather than a library.

## **8.2 Builders and editors**

| Renderer | Builder component | Stars | Last commit | Licence |
| :---- | :---- | ----: | :---- | :---- |
| SurveyJS | Survey Creator | 1,278 | 14 Sep 2026 | Commercial |
| Form.io | Built into formio.js | 2,087 | 2 Sep 2026 | MIT |
| bpmn-io form-js | form-js-editor, playground | 550 | 9 Sep 2026 | MIT with watermark clause |
| Formily | Designable | 3,529 | 25 Apr 2022 | MIT — dead |
| JSONForms | jsonforms-editor | 87 | 19 Nov 2025 | No licence file |
| — | formBuilder (standalone) | 2,709 | 7 Aug 2026 | MIT |
| — | Formeo (standalone) | 605 | 8 Aug 2026 | MIT |

Three points stand out. Formily's Designable has 3,529 stars and has been untouched since April 2022, which is precisely the trap star counts set. The JSONForms editor has no licence file in its repository, meaning there is no licence at all rather than a permissive one. And form-js is MIT but carries a clause requiring the bpmn.io watermark to remain visible and unobscured, which must be checked against branding requirements.

## **8.3 Why no third-party builder can be the pathway editor**

Every one of these builders edits **its own** schema. None models constructs, loadings, transforms, aggregation methods, report blocks, gap direction, role-specific prompts, invitation configuration or disclosure flags.

Adopting Survey Creator as the administration interface would make SurveyJS JSON the source of truth, with the measurement layer bolted on as a metadata bag hanging off each question — exactly the coupling avoided by placing the renderer beneath the render key. Additionally, the two most important item types, the bucket card sort and the drag-rank, cannot be authored in any of them, so even scoped to rendering a builder would cover perhaps six of ten item types.

## **8.4 Build versus buy for the platform as a whole**

A forms platform such as Formbricks is not a suitable foundation. The workbook is not a survey: card sorting into buckets, drag-ranking, the sealed letter, the timeline, the hub with per-pillar progress and the mentor preview are not expressible in a form builder, so an application would be required regardless and a second system synchronised alongside it. The observer flow also contains the card sort, so even the questionnaire portion cannot be delegated cleanly.

Licensing reinforces the conclusion. Formbricks' core is AGPLv3 with enterprise functionality under a separate licence, and no white-label licence is offered that would permit taking components such as the survey editor into another product. AGPL over a network service requires publishing modifications, which is workable for an open-source project and a problem otherwise.

LimeSurvey (GPL-2.0, German, actively maintained) is worth noting for one capability the others lack: its participant tables provide genuine per-person tokens, single-use links, reminder scheduling and token attributes. It cannot link a participant's self-assessment to their observers' responses or compute the comparison, so the reporting layer remains bespoke.

# **Part Nine — Administration and authoring**

## **9.1 The editor**

Build the pathway editor rather than adopting one, in three phases, stopping whenever it is good enough.

### **Phase one — a few days**

Monaco bound to the pathway JSON Schema, the linter running on a debounce, a diff view and the preview harness. Monaco has native JSON Schema support: pointing it at the schema yields autocomplete on every key, inline error highlighting, enumerated value dropdowns and hover documentation drawn from the schema's description fields. This is roughly thirty lines of configuration and is genuinely pleasant for anyone comfortable with JSON.

Every description in the schema becomes help text in the editor. It is worth investing in them.

### **Phase two — when a second author appears**

Per-layer forms for constructs, items, sections and reports. Each is an ordinary CRUD screen. The item editor is a type dropdown, prompt fields per role, scale bounds and labels, an options list and a scoring panel — around two days of work, and it fits the model exactly in a way no third-party builder will.

### **Phase three — only if requested**

Drag-and-drop ordering of sections and items, the one thing commercial builders do that is genuinely fiddly to replicate.

Phase one remains sufficient for longer than expected because authors have a language model available. The reason people buy drag-and-drop builders is that hand-editing structured configuration is tedious, and that problem is substantially addressed by pasting the schema, describing the change, and previewing the result.

JSON Editor (4,904 stars, MIT, vanilla) is the alternative to Monaco if generated form controls are preferred to a text editor. It renders an editing interface directly from a JSON Schema, though it handles deeply nested arrays of objects poorly, which describes most of this document.

## **9.2 Editing by language model, with preview**

The objective is that an author exports the pathway, asks a language model to change it, and pastes the result back to preview it before publishing. This is achievable with no model-side integration at all: the human is the transport.

The single structural requirement is that the application can render a pathway **that arrived from the clipboard rather than the database**. If the renderer fetches the pathway by identifier deep inside its components, preview is painful; if there is one entry point taking a document object, preview is nearly free.

### **Code required**

| Component | Detail |
| :---- | :---- |
| Pure core package | validate (ajv, precompiled from the schema), lint, score, aggregate, evaluate conditions, resolve role-specific text. No input or output; runs identically in Node and the browser. Roughly 800 to 1,500 lines, and needed regardless. |
| Renderer | A pure function of pathway, role and answers. A report renderer as a pure function of pathway and aggregated results. |
| Synthetic response generator | Given a pathway, produce plausible responses so reports can be previewed at all. Presets for random, high on a given construct, large self-versus-other gap, and sharp observer disagreement. Around 150 lines, and what makes preview useful rather than decorative. |
| Preview harness | A route reading the candidate document from session storage rather than the database, with a role switcher, a scenario panel, sliders to force construct scores so narrative variants can be seen to flip, a persistent unsaved banner and a clear button. |
| Import screen | Textarea and file drop, then validate, lint, diff, and offer preview or save as draft. Raw diff via jsondiffpatch with a domain-aware summary layered on top, colouring scoring changes differently from copy changes. |
| Briefing pack button | Copies schema, current pathway and a short instruction preamble to the clipboard in one action. Around fifty lines, and without it authors paste the pathway alone and imports fail. |
| Rendering safety | Content blocks rendered as sanitised Markdown with no raw HTML; document size and item count capped on import. |

### **Three levels of integration**

**Level zero — copy and paste.** The import screen and the briefing pack button. Works today with any chat interface. No integration of any kind.

**Level one — still no plugins, materially better.** Three additions. Host the schema and the authoring guide at stable public URLs, so an author can instruct a model to read them rather than pasting 27 KB. Accept file upload on the import screen, since models return downloadable files more reliably than long text in a chat response. And support patch documents, so the model returns only what changed.

The patch format matters most. Whole-document regeneration is where models silently drop a construct or truncate an array. A patch is small enough to survive any output limit, trivially diffable, and fails loudly if the target version has moved.

{ "target": { "pathway": "calling-workbook", "version": "1.2.0" },  
  "ops": \[  
    { "op": "add",     "collection": "items", "value": { "id": "q-rest" } },  
    { "op": "replace", "collection": "items", "id": "q-character",  
      "path": "prompt.observer", "value": "..." },  
    { "op": "remove",  "collection": "sections", "id": "old-intro" } \] }

**Level two — an optional MCP server, later.** Endpoints for retrieving a pathway, validating it, applying a patch, saving a draft and generating a preview URL: roughly 200 lines wrapping endpoints already built. The one real gain is that the model can call the validator and correct itself in a loop rather than a human relaying error messages. Worth building only once authoring is frequent enough that the copy-and-paste cycle becomes the bottleneck; because it is a thin wrapper, deferring it costs nothing.

For a technical author there is a fourth route requiring no new code at all: keep pathways in a git repository, edit them with a language model in the editor, and have continuous integration run the validator on every pull request, with a merge triggering publication.

### **Why validation is the safeguard**

Schema validity is not sufficient. A deliberately mangled version of the example pathway was tested against the linter, which caught a mistyped construct identifier, an undeclared template variable, ipsative constructs charted across people, and a response threshold of one — all four of which pass JSON Schema validation.

Two design decisions make this work: additionalProperties is false throughout the schema, so a hallucinated key fails loudly rather than being silently ignored; and a content-only import mode rejects any change touching constructs, scoring or item identifiers, so a copy edit or translation cannot quietly renumber a scale.

# **Part Ten — Recommended stack and build order**

| Layer | Choice |
| :---- | :---- |
| Database | PostgreSQL 18 on Hetzner (Falkenstein or Nuremberg), pgBackRest to a Storage Box plus an off-site copy, row-level security enabled, pgcrypto for the sealed letter |
| Backend | Node 22 with TypeScript; Hono for portability or Fastify for batteries; Drizzle ORM; Zod validation at every boundary |
| Authentication | Better Auth — Google, Microsoft and magic link; signed opaque tokens for observers |
| Client | The existing vanilla JavaScript, moved into Vite as modules; SurveyJS Form Library for standard item types; native widgets for card sort and drag-rank |
| Email | Scaleway TEM or Mailjet, over SMTP behind an abstraction |
| Deployment | Docker Compose via Kamal or Coolify, Caddy for TLS |
| Monitoring | Uptime checks plus self-hosted GlitchTip |
| Alternative stack | Django with django-allauth and HTMX, if the team is Python rather than TypeScript. Django's administration interface and migration story are better for a compliance-heavy application with a small team. |

## **Build order**

12. Authentication and workbook persistence.

13. Contacts and tokenised invitations.

14. Observer submission.

15. Scoring, aggregation and the comparison report.

16. PDF export.

17. Pathway editor — Monaco phase first.

Everything after step three is pure addition, so the system delivers value before it is complete.

# **Appendix — Accompanying files**

| File | Contents |
| :---- | :---- |
| pathway.schema.json | JSON Schema (draft 2020-12) defining the pathway document format in full. |
| calling-pathway.example.json | A worked example built from the prototype's content: constructs, items, sections, flows, invitations, message templates and three reports. |
| validate\_pathway.py | Two-pass validator — JSON Schema followed by a referential and semantic linter. Reference implementation to be ported to TypeScript for the import endpoint. |
| AUTHORING.md | Authoring guide covering the four layers, scoring semantics, display specification and the language-model workflow. |

