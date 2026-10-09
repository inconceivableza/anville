# Whatever You Do — hackathon requirements

What we're building, and the rules that keep it buildable afterwards.

## Start here

**Whatever You Do helps people discern their God-given purpose.** The personal journey is built and production-ready. This weekend we add the layer that lets an organisation run it with a group of their people.

### What already exists

| Part | What it does |
| --- | --- |
| Gifts and talents assessment | A card sort plus six written questions. Five people who know the participant answer the same questions anonymously. The gap between the two is the most valuable output. |
| Offline workbook | A printed booklet for the middle sections. Some participants work entirely on paper. Life timeline, expressing your calling, growth plan, devotional readings. |
| Letter to your future self | Written at the end, sealed for a year, sent back automatically. |
| Coach | One person walks alongside one participant. Gets briefing material before each conversation. |
| Five impact questions | Asked on day one and again at the end. The before-and-after is how we prove it worked. |

### What we are building this weekend

Churches, charities and businesses want to run this with a group of their people at once. That needs four things that do not exist yet:

1. **Organisations and groups** — so people can be linked together at all
2. **An admin view** — who has started, who has stalled, who has finished
3. **Aggregate results** — the gifts across a group, and the before-and-after scores
4. **Their own content** — their teaching videos in place of ours
5. &#91;A UX REVIEW!\]

Plus a way for an admin to message the group, which is what makes the admin view actionable.

### The one-line goal

By Sunday, a church leader should be able to invite twelve people, watch them progress, see what the group's gifts look like, and send them all a message.

## Non-negotiables

Read this before writing code. These are cheap today and expensive to retrofit.

### 1. Roles are relationships, not user types

Never add `is_coach` or `role` to the users table. A person is not a coach — they *coach Sam*. Store it as a row:

| who | can do | scope type | scope id |
| --- | --- | --- | --- |
| Rachel | admin | organisation | St Mary's |
| Niall | coach | person | Sam |
| Tom | observer | person | Sam |

Four columns. Scope needs both a type and an id because it points at different kinds of thing.

Organisations and groups are records like users. `organisation_id` lives on the **group**, not on permission rows. That gives the cascade - organisation, then group, then person, then their journey - so one admin row reaches everything beneath it. Never write a permission row per cohort.

Organisation membership is also a relationship, not a field on the user. People can belong to more than one.

### 2. One permission function

Everything asks the same question: **can this person see this thing?** One lookup that walks those rows and the cascade. Route every check through it, even with only four roles.

### 3. Admins see aggregates, never individual content

A leader sees **progress** and **anonymised aggregates**. Nothing else.

This is the line that makes the product trustworthy, and once crossed it cannot be uncrossed. People write things in the letter to themselves they would never write if they thought their pastor could read them.

### 4. Minimum group size before any aggregate renders

Five. With three people a "gifts map" identifies individuals.

### 5. Participants can see what admins see about them

One screen listing exactly what is visible. Removes the suspicion entirely, costs almost nothing.

### 6. Consent before the data model, not after

Participants must be told what their leader can see **before** they start. Build this in, do not leave it for later - it shapes the schema.

### 7. Nothing changes for solo users

Someone not in an organisation must notice no difference at all. This is the existing product and it works.

## Workstream A — Organisations, groups and invitations

**Everything else depends on this. Start it first, and get the schema reviewed before anyone builds on top of it.**

### Must have

- [ ] `organisations` table — id, name
- [ ] `groups` table — id, name, `organisation_id`, `type`
- [ ] Permissions table — who, can do, scope type, scope id
- [ ] The `canSee(person, thing)` function, walking the cascade
- [ ] Membership relationship — a person belongs to an organisation (and may belong to more than one)
- [ ] Create an organisation, create a group inside it
- [ ] Invite by email — paste a list or share a join link. Nobody creates accounts by hand
- [ ] Invited person lands in the right group automatically on sign-up
- [ ] Consent screen before a participant starts: what their leader will and will not see
- [ ] A participant-facing screen showing exactly what is visible about them

### Notes

**Group `type` matters even though only one value is used now.** Set it to `cohort` or `team`. Team features are out of scope this weekend, but the column being there means they are rows later rather than a migration.

**Four roles exist:** `participant`, `coach`, `observer` (trusted contact), `admin`. Observer and coach already exist in the current product — do not rebuild them, extend them into this shape.

**Do not build:** full RBAC, policy engines, inherited permission trees, SSO, billing. Four roles and one lookup is the whole thing.

### Done when

A leader can create an organisation, create a group, invite twelve people by email, and those people appear in that group having consented.

## Workstream B — The admin progress view

**The point of this screen is spotting the three people who stopped at week two.** Everything else is secondary.

### Must have

- [ ] A table of everyone in the group, one row each
- [ ] Progress across the five steps — not started, in progress, done
- [ ] Last activity date
- [ ] A visible flag for anyone who has not opened it in 14+ days
- [ ] Whether they have a coach assigned, and whether that coach has been active
- [ ] Count of how many trusted contacts have responded (this is the commonest place people stall — they are waiting on other people)
- [ ] Sort and filter by status

### Explicitly not on this screen

No timeline content. No calling statements. No written answers. No letters. If a developer finds themselves building a link through to someone's reflective writing, that is the wrong product.

### Notes

**Stalling has two different causes and they need different responses.** Someone who has not logged in is a nudge problem. Someone waiting on their trusted contacts is a different nudge, aimed at other people entirely. Showing both in the same column loses that.

**The nudge button belongs here**, but the sending mechanism is Workstream E. Agree the interface between the two early.

**Nudges come from a named human**, not from the platform. "Rachel thought you might need a hand picking this back up" works. "Whatever You Do: you have incomplete items" does not.

### Done when

An admin opens a group of twelve, immediately sees who has stalled and why, and can nudge them.

## Workstream C — Aggregate results

**This is the demo.** It is also the thing no other tool can do, because it needs the assessment data underneath it.

### C1 — The gifts map

- [ ] Aggregate the assessment across everyone in the group
- [ ] Show where the group clusters and where it is thin
- [ ] Both scales: APEST(d) and working style
- [ ] Show the observer view alongside self-assessment where available
- [ ] Hard floor: renders only at five or more completed assessments

The line that makes a leadership team sit up is *"heavy on teachers and shepherds, thin on pioneers"*. That is the output to aim for.

### C2 — Before-and-after scores

- [ ] The five impact questions, aggregated at group level
- [ ] Day one against end of course
- [ ] Same five-person floor

**Treat question five separately.** If one to four rise and five falls, the course has given someone clarity and anxiety in the same package, which is the opposite of the intent. Do not average all five into a single score.&#32;

### Notes on framing

**This is a conversation starter, not an org chart.** Research on team effectiveness consistently finds that how a team interacts matters far more than its composition. If this becomes a deployment tool — slotting people into roles by type — it will do harm and it will not work.

So: present findings with questions attached. *"Who here is carrying something nobody has asked them to use?"* Avoid fixed-trait language. Show ranges and spread rather than clean type labels. Frame results as this-season, not as essence.

### Done when

A leader sees the shape of their group's gifts, sees what changed over the course, and is prompted with a question rather than a recommendation.

## Workstream D — Their own content

**Small job, high perceived value.** Roughly half a day for one person. Good first task for someone who wants something self-contained.

### Must have

- [ ] An organisation can set its own video for each step of the journey
- [ ] Paste a URL (YouTube, Vimeo) — no file hosting this weekend
- [ ] Falls back to the default Whatever You Do video where none is set
- [ ] Participants in that organisation see their own organisation's video
- [ ] Preview before saving

### Notes

The prototype journey (<https://neon-alpaca-f9ee16.netlify.app>) already has video placeholders at each step — this slots into them rather than adding anything new.

**Replace or add, not just replace.** Some organisations will want their church leader introducing the section *and* the standard teaching. Allow both, ordered.

**This is what makes it feel like their course rather than ours**, which matters more for adoption than it looks on paper. A church leader who has recorded three two-minute videos is invested in the thing succeeding.

### Done when

An admin pastes a URL, and participants in that organisation see it at that step instead of the default.

## Workstream E — Group communication

**This is what makes the admin view actionable.** Without it, a leader who spots three stalled people has to copy twelve addresses into Outlook. Build it as a broadcast, and resist everything it could become.

### Must have

- [ ] Send a message to a group: **all participants**, **all coaches**, or **both**
- [ ] Subject and body, delivered by email
- [ ] A record of what was sent, to whom, and when
- [ ] Sent from a named human, with replies going to that person's own inbox
- [ ] Unsubscribe route

### Should have if time allows

- [ ] Send to a filtered subset — "everyone who has not started", "everyone still waiting on trusted contacts"
- [ ] Starter templates (see below)

### Coaches and participants are different audiences

Do not ship this as one list with a filter on top. They receive genuinely different things:

| Audience | Typical message |
| --- | --- |
| Participants | "The celebration evening is on the 14th, sign up here" · "You are halfway, keep going" |
| Coaches | "Here is what we have learned about running conversation two" · "Three of your people have stalled" |

### Starter templates

Worth including three, because admins many not all be confident writers and the quality of these messages determines whether people come back. It also quietly teaches the practices learned from running the course.

1. **Nudge for people who have stalled** — warm, no guilt, offers a way back in
2. **Mid-course encouragement to coaches** — what to watch for, permission to ask rather than advise
3. **Invitation to the closing event**

### Do not build

Threads, replies in-app, inboxes, notification preferences, scheduling, rich text editors, attachments. The moment this becomes a messaging system it needs moderation, read states and a mobile story.

**Broadcast out. Replies go to the sender's own email.**

### Two things to decide before writing code

**Sender identity and deliverability.** Bulk email on behalf of an organisation needs a proper sending domain and reputation. Do not wire up a raw SMTP call — agree the provider first.

**Who can send.** Admins only, or coaches to their own people as well? Lean admin-only for the weekend.

### Done when

An admin selects a group, picks participants or coaches, writes a message, sends it, and can see it in a sent log.

## Out of scope

All of these are real eventually. None of them this weekend. If you find yourself building one, stop and check.

| Not building | Why |
| --- | --- |
| Billing and subscriptions | Nothing here depends on it |
| SSO | Email invitations are enough for a dozen people |
| Custom branding beyond video | Visual theming is a rabbit hole |
| Data export | Wanted later, buys nothing on Sunday |
| Anything resembling an LMS | Modules, quizzes, completion certificates. Not this product - yet |
| In-app messaging | See Workstream E |
| Mobile apps | The journey works in a browser |

### Team coaching — deliberately deferred

Worth understanding because it shapes the schema, even though nothing gets built for it.

**What it will be:** an organisation runs the course with an actual team rather than a mixed cohort. Everyone gives feedback on everyone, not just on one participant. We will want to distinguish what colleagues said from what people outside work said, likely the most revealing gap the product can surface.

**Why Workstream A matters so much:** that feature should be new **rows**, not new columns.

- The team coach is **always external**, never the line manager. They would hold `coach → each member` plus `admin → the group`. Two existing roles, one person, no new concept
- Reciprocal feedback is simply more `observer` rows
- Whether someone is a colleague or outside the team is an attribute **on the feedback relationship**, not on the user

**So three things to honour now:**

1. Keep attributes on the edge. When a trusted contact submits, that relationship holds how they know the participant. "We work together" must be addable as a value, not a new table
2. Give groups a `type` now, even though only `cohort` is used
3. Assume feedback is **many-to-many** from the start. One participant with five observers is a special case of that, not the shape of the schema

**The test:** if adding team coaching later needs new rows and almost no new columns, this weekend was built right.

## Dividing the work, and the demo

### Suggested teams

| Workstream | People | Depends on | Notes |
| --- | --- | --- | --- |
| A — Orgs, groups, invitations | 2 | Nothing | Start first. Everything waits on the schema |
| B — Admin progress view | 1–2 | A (schema only) | Can build against stub data while A finishes |
| C — Aggregate results | 2 | A (schema only) | This is the demo. Needs someone comfortable with the assessment data |
| D — Their own content | 1 | A (schema only) | Self-contained. Good for someone arriving late |
| E — Group communication | 1 | A, plus B for the nudge button | Agree the sending provider before coding |

**Agree the schema in the first hour, together.** B, C, D and E can then all proceed against it in parallel. If A is still moving at lunchtime on Saturday, everyone else is blocked.

### What to do if you finish early

In this order: the filtered sends in E, the stalled-by-reason breakdown in B, then the "what your admin can see" participant screen. Not new features.

### Demo script — five minutes

1. Rachel creates **St Mary's** and a group called **Autumn cohort**
2. She invites twelve people. One accepts on screen and sees the consent notice — *this is what your leader can and cannot see*
3. Rachel uploads her pastor's two-minute intro video for section one. The participant refreshes and sees it
4. Rachel opens the progress view. Three people have stalled; two are waiting on trusted contacts
5. She messages the stalled three using the nudge template
6. She opens the aggregate view: the group's gifts, heavy in some places and thin in others, with a question underneath it
7. The before-and-after scores, with question five shown separately

**Seed the data beforehand.** A demo of an empty cohort shows nothing. Have twelve completed assessments in the database.

### Definition of done

A church leader can invite twelve people, watch them progress, see what the group's gifts look like, and send them all a message — and no admin anywhere in the product can read a participant's ‘letter to their future self’.
