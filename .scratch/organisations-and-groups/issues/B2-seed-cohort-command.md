# B2: Seed a demonstration cohort

**What to build:** A developer runs `seed_cohort` on their machine and gets Example Church with an Autumn cohort of twelve fake members spread across the pathway, and an organisation admin to sign in as, so they can build on realistic data straight away.

**Blocked by:** A1 (Organisations, groups, membership and permissions, with can_see); B1 (Consent v2)

**Status:** claimed

**Spec:** Seed command; User Stories › Developers

- [x] The command refuses to run unless debug is on, and needs a published pathway
- [x] It creates Example Church, an Autumn cohort of twelve members and an organisation admin, and prints the admin's email and password and the cohort's join link
- [x] Members are spread across the pathway: some not started, some part-way, some finished with self-results, observer answers through real invitations and closing ratings; one has withdrawn consent
- [ ] Every account uses a reserved example address and every response is flagged as test data
- [ ] Running it a second time says the organisation already exists and creates nothing
