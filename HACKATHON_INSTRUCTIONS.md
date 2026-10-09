# Whatever You Do — hackathon requirements

What we're building, and the rules that keep it buildable afterwards.

> ✨ Adapted with AI assistance from an earlier brief, and checked against the code as partially built, `CONTEXT.md` and ADRs 0002–0013. Where this brief and the code disagree, the code and the ADRs win.

## Start here

**Whatever You Do helps people discern their God-given purpose.** The personal pathway is built. Its consent text and observers' notice are still marked drafts, so it runs on made-up data only. This weekend we add the layer that lets an organisation run it with a group of their people.

Read `CONTEXT.md` (the Groups section) before naming anything: the codebase says **organisation admin**, **group admin**, **member**, **join link**, **observer** and **section**, not leader, trusted contact or step.

### What already exists

| Part | What it does |
| --- | --- |
| Strengths assessment | Part of Section 1. The participant sorts 36 strengths into five buckets and fine-tunes each. It is scored on two frameworks, APEST(d) and the Professional Energy Profile (PEP). Observers (at least two invited; nothing shown until three answer) sort the same strengths about them, through their own link and without an account. The comparison between the two is the most valuable output. |
| The Workbook | A downloadable PDF for Sections 2 to 4, worked on paper. Some participants do the whole middle of the course offline. Life timeline, expressing your calling, growth plan, devotional readings. |
| Letter to your future self | Written in Section 5. Sending it back after a year is **not built**: no email provider is chosen. |
| Coach | One person walks alongside one participant, named by the participant in "Before we begin". The coach answers through a link (no account), gets a coach brief, and sees the participant's results and comparison only if the participant shares them (ADR 0011). |
| Five impact questions | Five 1–10 ratings asked in "Before we begin" and again in Section 5, fixed once their section is complete. The before-and-after is how we prove it worked. |
| **Organisations and groups** (new, partially built) | Most of Workstream A: organisations, groups, permissions, joining by link, consent v2, "Your groups", "Your organisations" with members' progress, and `seed_cohort`. See Workstream A. |

### What we are building this weekend

Churches, charities and businesses want to run this with a group of their people at once. That needed four things, and the first is now mostly in place:

1. **Organisations and groups** — so people can be linked together at all *(mostly built)*
2. **An admin view** — who has started, who hasn't, who has finished *(a first version is built)*
3. **Aggregate results** — the gifts across a group, and the before-and-after ratings
4. **Their own content** — their teaching videos alongside ours
5. **A UX review** — see Workstream F

Plus a way for an admin to message the group, which is what makes the admin view actionable.

### The one-line goal

By Sunday, a church leader should be able to share a join link with twelve people, watch them progress, see what the group's gifts look like, and send them all a message.

## Non-negotiables

Read this before writing code. These are cheap today and expensive to retrofit. Most are now in the code: keep them there.

### 1. Rights are relationships, not user types

Never add `is_coach`, `is_admin` or `role` to the user. A person is not an admin — they *manage Example Church*. It is stored as a row in `organisations.Permission`:

| holder | capability | organisation | group |
| --- | --- | --- | --- |
| Rachel | `manage` | Example Church | — |
| a facilitator | `manage` | — | Autumn cohort |
| a pastor | `see_progress` | Example Church | — |

The brief's "scope type, scope id" became two nullable foreign keys with a check constraint that exactly one is set, so the database keeps referential integrity. `manage` on an organisation also creates groups; `manage` on a group copies and replaces its join link; either capability sees members' progress. Only the operator grants permissions (Django admin, or the seed command).

Organisations and groups are records like users. `organisation_id` lives on the **group**, not on permission rows. That gives the cascade — organisation, then group, then member — so one permission on an organisation reaches every group in it, including groups made later. Never write a permission row per group.

Membership (`organisations.Membership`: participant, group, joined_at) is a relationship too. Belonging to an organisation is derived from its groups, and people can belong to several, in several organisations, keeping one response across them all.

**Coaches and observers hold no permissions.** They have no account (ADR 0012): each is a contact on the participant's response with a link of their own. Don't rebuild them as permission rows.

### 2. One permission function

Everything asks the same question: **may this person see this of that participant?** It is `can_see(viewer, participant, what)` in `organisations/visibility.py`, with `members_seen_by(viewer, group)` as its companion for a whole group. Route every check through them.

Today `what` is only `progress`; anything else returns false whatever permissions exist. New work that needs another kind of view adds a new `what`, with its own rule and its own consent sentence.

### 3. Admins see progress and combined results, never individual content

An organisation or group admin sees a member's **display name, sections complete out of their track, and the date last active**, and (once Workstream C lands) the **group's self-results averaged**. Nothing else: no answers, no one person's results, no letter, no email address.

This is the line that makes the product trustworthy, and once crossed it cannot be uncrossed. People write things in the letter to themselves they would never write if they thought their pastor could read them.

The operator — whoever runs the deployment — can read everything, and no permission changes that (ADR 0012). Don't promise otherwise.

### 4. Minimum group size before any combined result renders

Three members with a self-result (ADR 0013), the same minimum as the observer average. Below that, nothing renders. An admin of a group of three who knows two members' results can still work out the third's; that is accepted, as it is for observers. Never show one person's result, and never a count small enough to point at someone.

### 5. Participants can see what admins see

The consent text, the join page and "Your groups" all carry the same sentence on what a group's admins see (`organisations/templates/organisations/what_admins_see.html`). Still worth adding: the participant's own row, exactly as admins see it.

### 6. Consent before the data model, not after

Built. Consent v2 says who sees what, including a group's admins, and participants who agreed to v1 are asked again. Consent is one row per participant per version of the text, not per group. A member who withdraws stays in their groups and shows only as "hasn't consented".

**Anything new an admin will see — observers answered, coach status, before-and-after ratings, email — needs a consent sentence and a raised text version before it is built.** Batch them: one version raise for the weekend, not four.

### 7. Nothing changes for solo users

Someone not in a group notices no difference at all. Signing up without a join link still asks for the enrolment code. This is the existing product and it works.

## Workstream A — Organisations, groups and joining

**Everything else depends on this. It is partially built.** Read `organisations/models.py`, `organisations/visibility.py` and ADR 0012 before building on it.

### Must have

- [x] `Organisation` — name
- [x] `Group` — organisation, name, `type` (`cohort` or `team`), join token
- [x] `Permission` — holder, capability (`manage`, `see_progress`), organisation or group
- [x] `can_see(viewer, participant, what)` and `members_seen_by(viewer, group)`, walking the cascade
- [x] `Membership` — a participant belongs to a group, and may belong to several in several organisations
- [x] The operator creates an organisation and its first admin in one Django admin form; an organisation admin creates groups on "Your organisations"
- [x] Share a join link: copy it, or replace it if it travelled too far. Nobody creates accounts by hand
- [ ] Invite by email — **not built**: no email provider is chosen. Waits on Workstream E's provider
- [x] A person who opens a join link signs up without the enrolment code, consents, and lands in the right group
- [x] Consent v2: what a group's admins will and will not see
- [x] "Your groups": each group, its organisation, what its admins see, and "Leave this group"
- [x] `seed_cohort`: Example Church, an Autumn cohort of twelve part-way through, and an admin

### Notes

**Group `type` is a label only.** `cohort` and `team` both exist and nothing behaves differently. Team features are out of scope this weekend, but the value being there means they are rows later rather than a migration.

**Roles, as they are:** a *participant* is anyone with an account and a response; a *member* is a participant in a group; an *organisation admin* or *group admin* holds a permission; a *coach* or *observer* is a contact with a link, and has no account. Coach and observer already exist — do not rebuild them.

**Do not build:** full RBAC, policy engines, inherited permission trees, SSO, billing, tenancy (ADR 0002). Two capabilities and one function is the whole thing.

**Still open in A, if someone wants it:** admins appointing other admins or removing members from Anville's own pages (today, Django admin only).

### Done when

A leader creates a group, shares its join link with twelve people, and those people appear in that group having consented. *Met, except by email.*

## Workstream B — The admin progress view

**The point of this screen is spotting the people who haven't started, or who started and went quiet.** Everything else is secondary.

A first version is built: "Your organisations" lists each group's members with display name, "*n* of 5 sections · last active *date*", "not started" or "hasn't consented", sorted by name.

### Must have

- [x] Everyone in the group, one row each
- [x] Progress across the five sections (Before we begin, Section 1, the Strengths assessment, the Workbook, Section 5) — as a count today
- [x] Last activity date
- [ ] Make it a table with progress shown visually, and which section someone is on
- [ ] Sort and filter: not started, under way, finished, hasn't consented
- [ ] Whether they have a coach who has accepted — **new `what`, needs a consent sentence.** Coaches have no account, so "has the coach been active" isn't known
- [ ] Count of how many observers have answered (the commonest place people stall — they are waiting on other people) — **new `what`, needs a consent sentence.** A count only, never who

### Explicitly not on this screen

No timeline content. No calling statements. No written answers. No letters. No email addresses. If a developer finds themselves building a link through to someone's reflective writing, that is the wrong product.

### Notes

**No 14-day stall flag.** The spec decided against it: the Workbook is worked on paper, so a quiet fortnight may be someone hard at work in it. If you want one, raise it before building; "not started" is safe to flag.

**Stalling has two different causes and they need different responses.** Someone who has not started is a nudge to them. Someone waiting on their observers is a different nudge, aimed at the participant to chase other people. Showing both in the same column loses that.

**The nudge button belongs here**, but the sending mechanism is Workstream E. Agree the interface between the two early.

**Nudges come from a named human**, not from the platform. "Rachel thought you might need a hand picking this back up" works. "Whatever You Do: you have incomplete items" does not.

### Done when

An admin opens a group of twelve, immediately sees who hasn't started and who is under way, and can nudge them.

## Workstream C — Aggregate results

**This is the demo.** It is also the thing no other tool can do, because it needs the assessment data underneath it.

### C1 — The gifts map

Decided in ADR 0013 and already promised in consent v2, so this can start now.

- [ ] Average the self-results (`engine.Result.scores`, one per member's Strengths assessment) across consenting members of the group
- [ ] Show where the group clusters and where it is thin
- [ ] Both frameworks: APEST(d) and PEP
- [ ] Show standings ("Leading", "Strong", "Present", "Less used", from the pathway document), never percents
- [ ] **No observer view alongside.** ADR 0013 leaves observer results out: their notice doesn't cover a group's admins
- [ ] Hard floor: renders only at three or more members with a self-result
- [ ] A new rule beside `can_see` for group results (a group-level `what`), so it is checked in one place

The line that makes a leadership team sit up is *"heavy on teachers and shepherds, thin on pioneers"*. That is the output to aim for.

### C2 — Before-and-after ratings

**Needs a decision first.** Consent v2 tells members their admins see averaged self-assessment results only, not these ratings. Write the consent sentence and an ADR (like 0013) before building.

- [ ] The five ratings (`bl-*` in Before we begin, `pl-*` in Section 5, 1–10), averaged at group level
- [ ] Before we begin against Section 5, among members who have finished
- [ ] Same floor of three

**Treat question five separately** ("I am at peace with God's plan for my life"). If one to four rise and five falls, the course has given someone clarity and anxiety in the same package, which is the opposite of the intent. Do not average all five into a single score.

### Notes on framing

**This is a conversation starter, not an org chart.** Research on team effectiveness consistently finds that how a team interacts matters far more than its composition. If this becomes a deployment tool — slotting people into roles by type — it will do harm and it will not work.

So: present findings with questions attached. *"Who here is carrying something nobody has asked them to use?"* Avoid fixed-trait language. Show standings and spread rather than clean type labels. Frame results as this-season, not as essence.

### Done when

A leader sees the shape of their group's gifts, sees what changed over the course, and is prompted with a question rather than a recommendation.

## Workstream D — Their own content

**Smaller than it looks, but not half a day any more.** Two decisions come first.

### Decide first

- **There is no video block yet.** Pathway content is the pathway document (ADR 0003), authored for the whole deployment. Add a `video` block type that an author places in a section; that is the default video.
- **ADR 0012 says organisation admins don't author.** Letting them set a video changes that, so it needs an ADR. It also needs a rule for a member of two organisations: whose video do they see?

### Must have

- [ ] A `video` block type in the pathway document, holding the default video
- [ ] An organisation can set its own video for a video block, kept by organisation and block id
- [ ] Paste a URL (YouTube, Vimeo) — no file hosting this weekend
- [ ] Falls back to the pathway's video where none is set
- [ ] Members of that organisation see their own organisation's video
- [ ] Preview before saving

### Notes

The original prototype (<https://neon-alpaca-f9ee16.netlify.app>) has video placeholders at each section; the engine does not, which is why the block comes first. The Workbook's download page is a good place for one too, since that is where people go offline.

**Replace or add, not just replace.** Some organisations will want their church leader introducing the section *and* the standard teaching. Allow both, ordered.

**This is what makes it feel like their course rather than ours**, which matters more for adoption than it looks on paper. A church leader who has recorded three two-minute videos is invested in the thing succeeding.

### Done when

An admin pastes a URL, and members of that organisation see it at that section alongside, or instead of, the default.

## Workstream E — Group communication

**This is what makes the admin view actionable.** Without it, a leader who spots three people who haven't started has to find twelve addresses themselves. Build it as a broadcast, and resist everything it could become.

### Must have

- [ ] Send a message to a group's **members**
- [ ] Subject and body, delivered by email
- [ ] A record of what was sent, to whom, and when
- [ ] Sent from a named human, with replies going to that person's own inbox
- [ ] Unsubscribe route

### Should have if time allows

- [ ] Send to a filtered subset — "everyone who has not started", "everyone still waiting on observers"
- [ ] Starter templates (see below)

### Coaches and participants are different audiences

Do not ship this as one list with a filter on top. They receive genuinely different things:

| Audience | Typical message |
| --- | --- |
| Participants | "The celebration evening is on the 14th, sign up here" · "You are halfway, keep going" |
| Coaches | "Here is what we have learned about running the timeline conversation" · "Three of your people haven't started" |

**But coaches have no account.** A coach's name and email are a contact on the participant's response, given for one purpose. Writing to coaches needs its own decision; lean participants-only for the weekend.

### Starter templates

Worth including three, because admins may not all be confident writers and the quality of these messages determines whether people come back. It also quietly teaches the practices learned from running the course.

1. **Nudge for people who haven't started** — warm, no guilt, offers a way in
2. **Mid-course encouragement to coaches** — what to watch for, permission to ask rather than advise (once coaches can be reached)
3. **Invitation to the closing event**

### Do not build

Threads, replies in-app, inboxes, notification preferences, scheduling, rich text editors, attachments. The moment this becomes a messaging system it needs moderation, read states and a mobile story.

**Broadcast out. Replies go to the sender's own email.**

### Three things to decide before writing code

**Consent.** Admins don't see members' email today, and the spec held that contacting members is a new use of it. Write the consent sentence first.

**Sender identity and deliverability.** Bulk email on behalf of an organisation needs a proper sending domain and reputation. Django's email settings exist (`EMAIL_URL`) but nothing sends yet. Do not wire up a raw SMTP call — agree the provider first. Workstream A's emailed invitations wait on the same choice.

**Who can send.** Holders of `manage` only, or `see_progress` too? Lean `manage`-only for the weekend.

### Done when

An admin selects a group, picks who in it, writes a message, sends it, and can see it in a sent log.

## Workstream F — A UX review *(suggested)*

Walk the whole thing as three people — a participant joining by link, an organisation admin, a group admin — on a phone and a laptop, using `seed_cohort`'s data. Note friction, wording that promises more than is true, and anything that leaks a member's details. File findings; fix only small copy and layout ones on the spot. Good for someone who wants to understand the product before writing code.

## Workstream G — Demo data *(suggested)*

`seed_cohort` makes twelve members with the right spread, but its self-results and ratings are generated, so the gifts map won't say "heavy on teachers, thin on pioneers", every member was last active on the same day, and Ada is one of the twelve (the demo has Ada join live). Give it a demo shape: chosen top constructs per member, staggered last-active dates, ratings that rise, and one member left out so they can join on stage. Self-contained, and the demo depends on it.

## Workstream H — Consent and decisions desk *(suggested)*

B, C2, D and E each need a decision before code: a consent sentence, an ADR, or both. One person drafts them together in the first morning — observers answered and coach status (B), before-and-after ratings (C2), organisation videos (D), writing to members and to coaches (E) — so the consent text's version is raised once. Check each against the existing ADRs.

## Out of scope

All of these are real eventually. None of them this weekend. If you find yourself building one, stop and check.

| Not building | Why |
| --- | --- |
| Billing and subscriptions | Nothing here depends on it |
| SSO | A join link is enough for a dozen people |
| Tenancy | ADR 0002 stands; an organisation is a grouping, not a tenant (ADR 0012) |
| Custom branding beyond video | Visual theming is a rabbit hole |
| Data export | Wanted later, buys nothing on Sunday |
| Anything resembling an LMS | Modules, quizzes, completion certificates. Not this product - yet |
| In-app messaging | See Workstream E |
| Mobile apps | The pathway works in a browser |
| Accounts for coaches and observers | Not decided (ADR 0012); observers' answers are never linked to an account |

### Team coaching — deliberately deferred

Worth understanding because it shapes the schema, even though nothing gets built for it.

**What it will be:** an organisation runs the course with an actual team rather than a mixed cohort. Everyone gives feedback on everyone, not just on one participant. We will want to distinguish what colleagues said from what people outside work said, likely the most revealing gap the product can surface.

**Why Workstream A matters so much:** that feature should be new **rows**, not new columns.

- The team coach is **always external**, never the line manager. They would hold `manage` on the group, as any group admin does, and be named as coach by each member. Coaching itself still goes through each member's coach link, not a permission
- Reciprocal feedback is simply more observer invitations: each member invites the others
- Whether someone is a colleague or outside the team is an attribute **on the observer's invitation**, not on the user

**So three things to honour now:**

1. Keep attributes on the edge. When an observer answers, the invitation (or contact) holds how they know the participant. "We work together" must be addable as a value, not a new table. *Nothing stores this yet, although the observers' draft notice says "how you know {name}" is kept.*
2. Give groups a `type` now, even though only `cohort` is used. *Done.*
3. Assume feedback is **many-to-many** from the start. One participant with several observers is a special case of that, not the shape of the schema. *Observers already answer per invitation, so one person can observe several participants.*

**The test:** if adding team coaching later needs new rows and almost no new columns, this weekend was built right.

## Dividing the work, and the demo

### Suggested teams

| Workstream | People | Depends on | Notes |
| --- | --- | --- | --- |
| A — Orgs, groups, joining | 0–1 | Built | Only the leftovers: emailed invitations (after E's provider), in-app admin management |
| B — Admin progress view | 1–2 | A (built) | Extend "Your organisations". Coach and observer columns wait on H |
| C — Aggregate results | 2 | A (built), G for a good demo | This is the demo. C1 can start at once; C2 waits on H. Needs someone comfortable with `engine.Result` and the pathway document |
| D — Their own content | 1 | A (built), H | Starts with the `video` block, which needs nobody's decision |
| E — Group communication | 1 | A, B for the nudge button, H | Agree the sending provider before coding |
| F — UX review | 1 | Nothing | Good for someone arriving late |
| G — Demo data | 1 | Nothing | Tune `seed_cohort` for the demo's shape |
| H — Consent and decisions | 1 | Nothing | First morning; unblocks B's extras, C2, D and E |

**Read the schema in the first half hour, together**: `CONTEXT.md` (Groups), ADRs 0012 and 0013, `organisations/models.py` and `organisations/visibility.py`. Then run `python manage.py seed_cohort` (it needs `DEBUG` on and a published pathway) and sign in as the admin it prints.

### What to do if you finish early

In this order: the filtered sends in E, the not-started/under-way breakdown in B, then the participant's own row in "Your groups". Not new features.

### Demo script — five minutes

1. The operator has made **Example Church** in Django admin and given Rachel `manage` on it. Rachel creates a group called **Autumn cohort** on "Your organisations" *(built)*
2. She copies its join link and sends it. One person opens it on screen, signs up without an enrolment code, reads *who sees what*, agrees, and joins — the join page says what the group's admins will see *(built)*
3. Rachel adds her pastor's two-minute intro video for Section 1. The participant refreshes and sees it *(Workstream D)*
4. Rachel opens the group's members. Three haven't started; one withdrew consent and shows only as "hasn't consented" *(built)*
5. She messages the three who haven't started, using the nudge template *(Workstream E)*
6. She opens the group results: the group's gifts, heavy in some places and thin in others, with a question underneath it *(Workstream C1)*
7. The before-and-after ratings, with question five shown separately *(Workstream C2)*

[`HACKATHON_DEMO_WALKTHROUGH.html`](HACKATHON_DEMO_WALKTHROUGH.html) walks this script with the real table names, and marks each step built or to build.

**Seed the data beforehand.** A demo of an empty cohort shows nothing. `seed_cohort` gives twelve members, four of them finished, and seven with a self-result (six once the member who withdrew consent is left out); Workstream G gives them the shape the story needs.

### Definition of done

A church leader can share a join link with twelve people, watch them progress, see what the group's gifts look like, and send them all a message — and no organisation or group admin anywhere in the product can read a participant's letter to their future self.
