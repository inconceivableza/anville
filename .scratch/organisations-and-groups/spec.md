# Spec: organisations-and-groups

**Status:** ready-for-agent

Terms follow `CONTEXT.md` (see its Groups section). Decisions that are hard to reverse are in ADR 0012 (an organisation is a grouping within a deployment, not a tenant) and ADR 0013 (group results combine self-results only), and are referenced here rather than repeated.

## Problem Statement

Anville serves one participant at a time. A church or ministry that wants to take a cohort through *Whatever You Do* has no way to gather its people, see who has started and who has stalled, or invite them in one go. Each participant signs up alone with the deployment's enrolment code, and nobody but the participant (and their coach, on consent) can see anything of their progress.

Work on group progress, group results, communications and team coaching is about to start in parallel, and all of it stands on the same foundation: organisations, groups inside them, membership, permissions, and a single answer to "may this person see that person's progress?". Without that foundation in place first, each piece of work would invent its own, and they would not fit together. Consent must also cover what a group's admins see before any of it is shown.

## Solution

Inside one deployment, an operator creates an organisation and makes someone its organisation admin. The organisation admin creates groups (a cohort or a team) and shares each group's join link. A person who opens a join link signs up without an enrolment code, consents, confirms they want to join the named group, and lands on their hub, with their pathway exactly as before. A person who already has an account confirms and joins. A participant can be in several groups, in several organisations, and keeps one response across them all.

An organisation admin sees each of their groups' members: display name, sections complete out of their track, and the date they were last active, or that they have not consented. They never see answers, results or the letter. A group admin has the same rights over one group. The consent text, raised to a new version, says what a group's admins see; participants who agreed to the old one are asked again. A participant sees their groups at the foot of their hub, with a sentence on what each group's admins see, and can leave any of them.

A single function, `can_see`, answers whether one account may see a participant's progress. Later work builds on it, and a seed command creates a demonstration organisation with a part-way-through cohort of twelve so every developer starts from the same data.

## User Stories

### Operator

1. As an operator, I want to create an organisation in Django admin, so that a church or ministry can start using groups.
2. As an operator, I want to give an account organisation admin rights while creating the organisation, so that someone can run it straight away.
3. As an operator, I want to give an account group admin rights over a single group, so that a cohort's facilitator sees only their own cohort.
4. As an operator, I want to remove a member from a group in Django admin, so that a mistaken or unwanted membership can be undone.
5. As an operator, I want to take an admin's rights away in Django admin, so that someone who has stepped down no longer sees anyone's progress.
6. As an operator, I want to see organisations, groups, memberships and permissions in Django admin, so that I can answer questions about who sees whom.
7. As an operator, I want a seed command to refuse to run unless the deployment is in debug mode, so that fake data can never reach staging.

### Organisation admin

8. As an organisation admin, I want a "Your organisations" page reached from my hub, so that I can find my organisation's groups.
9. As an organisation admin, I want to create a group with a name and a type (cohort or team), so that I can gather a season's participants.
10. As an organisation admin, I want to see every group in my organisation with its member count, so that I know how many people have joined.
11. As an organisation admin, I want to copy a group's join link, so that I can send it to the people I want in it by whatever means I already use.
12. As an organisation admin, I want to replace a group's join link, so that a link that has been passed further than intended stops working.
13. As an organisation admin, I want existing members to stay in the group when I replace its link, so that replacing it never costs anyone their place.
14. As an organisation admin, I want to see each member's display name, sections complete out of the sections in their track, and the date they were last active, so that I can tell who is under way and who might need a word.
15. As an organisation admin, I want a member who has not consented, or who has withdrawn consent, shown as "hasn't consented", so that I understand why I see nothing for them.
16. As an organisation admin, I want a member who has not started shown as not started, so that I can tell them apart from someone who has stalled.
17. As an organisation admin, I want the admin pages to need only that I am signed in, not that I have consented, so that I can run a cohort without working through the pathway myself.
18. As an organisation admin, I want my rights over the organisation to cover every group in it, so that I do not need a grant per group.
19. As an organisation admin who is also a participant, I want my own pathway to work as any participant's does, so that running a group never gets in the way of doing the pathway.

### Group admin

20. As a group admin, I want to see my group's members and their progress, so that I can follow my cohort.
21. As a group admin, I want to copy and replace my group's join link, so that I can bring people in.
22. As a group admin, I want to see nothing of any other group, even in the same organisation, so that members of other groups keep their privacy.
23. As a group admin, I want to be unable to create groups, so that only the organisation admin decides the organisation's shape.

### Joining

24. As a person invited to a cohort, I want to open the join link and sign up without an enrolment code, so that I need only the one link I was sent.
25. As a person signing up through a join link, I want to give consent before I join, so that I know what I am agreeing to first.
26. As a person signing up through a join link, I want a page naming the organisation and group, and saying what its admins will see, before I join, so that joining is a choice I make knowingly.
27. As a person with an account, I want to open a join link and be asked "Join Example Church, Autumn cohort?", so that I can join without signing up again.
28. As a member, I want a join link for a group I am already in to say so and take me to my hub, so that opening it twice does no harm.
29. As a person with an old, replaced join link, I want to be told the link no longer works, so that I know to ask for a new one.
30. As a person who declines to join on the confirmation page, I want nothing recorded, so that opening a link commits me to nothing.
31. As a person who signs up without a join link, I want everything to work as it does today, enrolment code included, so that solo participants see no difference.
32. As a participant who joins a second group, I want my pathway to carry on where I was, so that joining never starts me again or splits my progress.
33. As a participant, I want to belong to groups in more than one organisation, so that my church cohort and my workplace team can both include me.

### Consent

34. As a participant who agreed to the earlier consent text, I want to be asked again now that it says what a group's admins see, so that my consent covers what is actually shown.
35. As a participant, I want the consent text to say that if I join a group, its admins see my progress and the group's combined results, never my own results, so that I know the limits before I join.
36. As a participant who withdraws consent, I want a group's admins to see only "hasn't consented" for me, so that withdrawing stops them seeing my progress.
37. As a participant who withdraws consent, I want to stay in my groups, so that consenting again later restores things without rejoining.

### Your groups

38. As a participant, I want a "Your groups" link at the foot of my hub, beside "Your consent", so that I can find which groups I am in.
39. As a participant, I want each of my groups listed with its organisation, so that I know who can see my progress.
40. As a participant, I want a sentence beside each group saying what its admins see, so that the consent text's promise is in front of me where it applies.
41. As a participant, I want to leave a group, so that its admins stop seeing my progress.
42. As a participant who leaves a group, I want my answers untouched, so that leaving costs me nothing of my own work.
43. As a participant, I want the admins' own names kept off "Your groups", so that nobody's details are shown to every member.

### Developers

44. As a developer building on organisations, I want one function that says whether an account may see a participant's progress, so that every view I build asks the same question the same way.
45. As a developer building on organisations, I want that function to refuse anything but progress, whatever permissions exist, so that no new view can show answers, results or the letter by mistake.
46. As a developer building on organisations, I want a seed command that creates Example Church with an Autumn cohort of twelve, part-way through, with self-results, observer answers and closing ratings, so that I start from realistic data without walking twelve pathways.
47. As a developer building on organisations, I want the seed command to print an organisation admin's email and password, so that I can sign in and see the admin pages at once.
48. As a developer building on organisations, I want all seeded responses flagged as test data, so that they can never be mistaken for real ones.
49. As a developer building on organisations, I want organisations, groups, memberships and permissions in the glossary and ADRs, so that I name things the way the codebase does.

## Implementation Decisions

### Shape (ADR 0012)

- A new Django app holds organisations, groups, memberships and permissions, and the `can_see` function. The engine and access apps do not depend on it, except where the hub links to "Your groups" and "Your organisations", and where sign-up skips the enrolment code for a held join link.
- Separation between organisations is by permission inside Anville only. No row-level security, no schema per organisation.

### Models

- **Organisation:** a name. Nothing else.
- **Group:** an organisation, a name, a type from a fixed set (`cohort`, `team`; a label only, no behaviour depends on it), and a join token. The join token is stored as it is, not hashed, so admins can copy the link again; replacing it is the defence against a link travelling too far.
- **Membership:** an account and a group, unique together, with the time it was made. Belonging to an organisation is derived from its groups. Leaving deletes the row.
- **Permission:** an account, a capability from a fixed set (`manage`, `see_progress`), and a scope that is either an organisation or a group. The brief's "scope type, scope id" is kept as two nullable foreign keys with a check constraint that exactly one is set, so the database keeps referential integrity; the scope type is derived from which is set.
  - `manage` on an organisation: create groups, copy and replace any of its groups' join links, and everything `see_progress` gives.
  - `manage` on a group: copy and replace that group's join link, and everything `see_progress` gives. It cannot create groups.
  - `see_progress`: see members' progress in the scope.
  - A permission on an organisation covers all its groups, including groups created later.
  - Only the operator grants or removes permissions (Django admin, or the seed command). A permission names an account; observers and coaches have none.
- All four are registered in Django admin. Permissions appear inline on the organisation and on the group, so creating an organisation and its first admin is one form.

### `can_see`

- `can_see(viewer, participant, what)` returns true or false.
- It is true only when all of these hold:
  - `what` is `progress`. Any other value is false, whatever permissions exist.
  - The participant holds current consent (the version now in force, not withdrawn).
  - The participant is a member of a group on which the viewer holds `see_progress` or `manage`, directly or through that group's organisation.
- It never grants answers, results, the letter or email. Work that needs another kind of view adds a new `what` with its own rule and its own consent sentence, and group results follow ADR 0013.
- A companion query gives the members of one group the viewer may manage or see, with each one's progress or "hasn't consented", so pages do not loop over `can_see` member by member.

### Progress

- For a member the viewer may see: display name, the count of complete sections out of the sections in their track (the hub's own counting, through `track_sections`), and the date (no time) their response was last updated.
- A member with no response shows as not started. A member without current consent shows "hasn't consented" and nothing else.
- No stall flag. The Workbook is worked offline, so a quiet fortnight may be someone at work in it.
- No email address is shown; contacting members is a new use of their email and needs its own consent sentence, decided with communications to members.

### Joining by link

- The join link is the group's URL with its token. Opening it holds the token in the session and shows the join page.
- The join page needs sign-in and current consent. A person without an account is sent to sign up; the sign-up form drops the enrolment code while the session holds a valid join token. After sign-up they go through consent as today, then return to the join page.
- The join page names the organisation and group and says, in one sentence, what its admins see. "Join" creates the membership and goes to the hub. Leaving the page without joining records nothing.
- Already a member: the page says "You're already in this group" and offers the hub.
- An unknown or replaced token shows a page saying the link no longer works and to ask whoever sent it for a new one. It reveals nothing about the group.
- Signing up without a join link is unchanged: the enrolment code still applies unless the deployment has turned it off.

### Consent v2 (ADR 0004)

- Raise the consent text's version and add one paragraph: if you join a group, its admins see your name, how far through you are and when you were last active, and the group's results combined, never yours on their own; leaving the group ends that.
- No real participant has consented yet, so only development and staging accounts are asked again. The text stays a marked draft.
- Withdrawing consent keeps memberships. `can_see` returns false while consent is withdrawn.

### Pages

- **Your groups** (participant, needs consent): each group's name and organisation, the sentence on what its admins see, and "Leave this group" (a POST with a confirmation). Admins' names are not shown. Linked from the foot of the hub beside "Your consent".
- **Your organisations** (needs sign-in only, and at least one permission, otherwise refused): each organisation and group the account has rights over; for each group, its type, member count, join link with copy and replace, and the members' progress. A "New group" form appears for organisations the account manages. Linked from the foot of the hub only for accounts holding a permission.
- Copying the link uses the browser's clipboard from a Vite module; htmx keeps eval disabled (ADR 0006).

### Seed command

- `seed_cohort` refuses to run unless `DEBUG` is on.
- It needs a published pathway, as `seed_observers` does, and reuses its way of making a self-assessment, self-result and observer answers.
- It creates Example Church, an Autumn cohort of twelve members, and one organisation admin with `manage` on Example Church, and prints the admin's email, password and the cohort's join link.
- Members are spread across the pathway: some not started, some part-way, some finished with self-results, observer answers through real invitations, and closing ratings. One member has withdrawn consent. All accounts use reserved `example.com` addresses and every response is flagged as test data.
- Running it twice does not duplicate the organisation; it says it already exists.

## Testing Decisions

- A good test drives behaviour a person or a caller can observe: a page's content and redirects, a function's answer, a command's output and the records it leaves. No test reaches into private helpers or asserts on queries.
- **Journeys** (the existing `tests/journeys` seam, Django's test client): joining as a new person without an enrolment code, joining while signed in, already a member, a replaced link refused, declining records nothing, solo sign-up still needs the code, consent v2 asks again, "Your groups" lists and leaves, "Your organisations" creates a group and shows link and progress, a group admin cannot see another group or create one, an account with no permission is refused, "hasn't consented" after withdrawal. Prior art: `test_consent.py`, `test_invitations.py`, `test_coach_link.py`.
- **`can_see` called directly** (one new seam, against the database), because later work will call it: organisation scope covers its groups, group scope covers only its group, no permission is false, withdrawn or outdated consent is false, any `what` other than `progress` is false even for an organisation admin, a non-member is false.
- **The seed command through `call_command`**: refuses without `DEBUG`, creates the organisation, cohort, admin and twelve members, prints the sign-in details, and does not duplicate on a second run. Prior art: the `load_pathway` fixture in the journeys conftest.
- Counting sections is already covered by the hub's core tests; progress is pinned through the journeys rather than a new core function.

## Out of Scope

- Tenancy (ADR 0002 stands).
- Accounts for coaches and observers (ADR 0012, "Not decided here"). An observer's answers are never linked to an account.
- Emailed invitations; no email provider is chosen.
- Admins appointing other admins, or removing members, from Anville's own pages (Django admin only).
- Group results. They are built later on ADR 0013: self-results only, hidden below three members with a self-result, never per person.
- Combining observer results for a group.
- A stall flag or reminders.
- Showing members' email addresses to admins.
- Group types with behaviour (a team's coaching, a cohort's season dates).

## Further Notes

- **Cut order, if time runs short:** first replacing a join link; then the "New group" form (groups are made in Django admin instead); then the progress list on "Your organisations" (to be built later on `can_see`). Never cut the seed command, consent v2, or `can_see`.
- The operator is whoever runs the deployment and holds Django admin and database access. They can read everything, and no permission changes that (ADR 0012). "No admin can read the letter" holds for organisation and group admins, not the operator.
