# Infrastructure sizing estimate — Hetzner

> ✨ Estimated with AI assistance from the documents in this repository. Hetzner prices were verified against the live price feed on 19 September 2026 (see [Price sources](#price-sources-and-verification)). Ubicloud and Scaleway figures are **not** verified and remain the softest numbers here.

Rough host sizing and monthly cost for the stack settled in [ADR 0001](adr/0001-django-orm-not-sqlalchemy.md) and the prior plans: Python/Django with the Django ORM, PostgreSQL with `jsonb` documents, HTMX-rendered pages, deployed to Hetzner Cloud in Falkenstein, Nuremberg or Helsinki.

This is an estimate, not a decision. Nothing here is binding; it exists so the hosting line in a budget is a considered number rather than a guess.

## Scope of "users"

The scenario columns use the informal words from the original question. In the vocabulary of [CONTEXT.md](../CONTEXT.md):

- **Concurrent users** — participants actively working through a section at the same moment, plus a handful of authors and administrators whose load is negligible by comparison.
- **Total users** — registered participants, active and dormant, at 10–20× the concurrent figure.

## All-in monthly cost

Base Ubicloud managed Postgres (point-in-time recovery included, no standby), with a staging host and transactional email folded into each profile.

| Scenario | Concurrent Users | Total Users | Server Size | Monthly Cost |
|---|---|---|---|---|
| **Low** | up to 50 | 500–1,000 | 1 × CX33 app/worker/Caddy (4 vCPU, 8 GB, 80 GB NVMe) + Ubicloud burstable PG (2 vCPU, 8 GB) + 1 TB Storage Box + 1 × CX23 staging | **€36–40 / £31–34** |
| **Medium** | up to 250 | 2,500–5,000 | 1 × CX43 app/worker (8 vCPU, 16 GB, 160 GB NVMe) + Ubicloud standard PG (2–4 vCPU, 16 GB) + 1 TB Storage Box + 1 × CX23 staging | **€76–99 / £65–85** |
| **High** | up to 1,000 | 10,000–20,000 | LB11 + 2 × CX43 app + 1 × CX33 worker/Redis + Ubicloud standard PG (8 vCPU, 32 GB) + 1 TB Storage Box + 1 × CX23 staging | **€206–252 / £177–216** |

The ranges are entirely the Ubicloud line; every Hetzner figure is a verified fixed list price, net of VAT, for the EU locations (FSN1, NBG1, HEL1).

## Where the money goes

| Line item | Low | Medium | High |
|---|---|---|---|
| App servers | €8.49 / £7.28 | €15.99 / £13.72 | €31.98 / £27.44 |
| Worker / Redis host | — | — | €8.49 / £7.28 |
| Load balancer (LB11) | — | — | €7.49 / £6.43 |
| Ubicloud managed Postgres, base tier | €14–18 / £12–15 | €41–64 / £35–55 | €118–164 / £101–141 |
| Storage Box BX11, 1 TB — weekly logical dumps | €3.20 / £2.75 | €3.20 / £2.75 | €3.20 / £2.75 |
| Staging host (CX23) | €5.49 / £4.71 | €5.49 / £4.71 | €5.49 / £4.71 |
| Scaleway TEM (transactional email) | €1 / £0.86 | €5 / £4.29 | €20 / £17.16 |
| Hetzner backups (20% of server price) | €2.80 / £2.40 | €4.30 / £3.69 | €9.19 / £7.88 |
| IPv4 addresses (€0.50 each) | €1.00 / £0.86 | €1.00 / £0.86 | €2.00 / £1.72 |
| Video hosting | external — €0 on these hosts | | |
| **Total** | **€36–40 / £31–34** | **€76–99 / £65–85** | **€206–252 / £177–216** |

Ubicloud's own PITR is the recovery mechanism. The Storage Box holds periodic `pg_dump` output as an independent, format-portable copy that depends on neither Ubicloud's tooling nor the account continuing to exist. That is cheap insurance worth keeping even though it is not a second provider.

## GBP conversion

Converted at **£0.858 per €1**, a working average for August–September 2026.

Precise published monthly averages were not retrievable in this environment, so the rate is anchored on daily spot points: 0.8575 on 31 August, 0.8597 on 4 September and 0.8561 on 19 September 2026, against a 2026 year-to-date average of 0.8641. Those points sit in a narrow band, so the average is unlikely to be wrong by more than a fraction of a penny — but it is an inference from daily rates, not a published monthly mean.

Two practical caveats: Hetzner and Ubicloud both bill in their own currency, so the GBP figure moves with the rate every month, and a card or bank FX margin of roughly 2–3% sits on top of everything in the GBP column.

## What drives the sizing

This workload is unusually light for its user count, and the reasons are worth recording because they are what keep the figures small:

- **Requests are think-time bound.** A participant sorting the 36 items or composing the letter generates a debounced autosave plus a navigation partial — roughly 4–8 requests per minute sustained. 1,000 concurrent participants is around 120 req/s average, not thousands.
- **HTMX partials, not SPA fan-out.** One template render, two or three indexed queries, one `jsonb` document read: approximately 10–25 ms of CPU per request.
- **Results are persisted, never recomputed.** A result snapshot is calculated once at submission against the pinned pathway version. The pathway version document is immutable and trivially cacheable in process.
- **The dataset is small.** Roughly 600 KB per participant — response document, result snapshot, and about eight observer responses. 20,000 registered participants is ~12 GB of live data, ~25 GB with indexes and the audit log. At every scenario the working set fits in RAM, which is why the database stays modest.
- **The heavy work is asynchronous.** PDF export, the four email surfaces and the long-horizon letter scheduler belong on a worker, never in the request path.
- **Traffic is not a cost.** Every EU cloud server includes at least 20 TB per month, with additional traffic at €1.00/TB. With video hosted externally, nothing here approaches that.

## Why CX, and why not dedicated vCPU

Two choices that the verified prices decided, both differently from how they would have gone on 2024 pricing.

**The app tier is x86 (CX), not ARM (CAX), because ARM now costs more.** Hetzner's Ampere line used to match or undercut the Intel/AMD line; it no longer does at any tier:

| Spec | Shared x86 | Shared ARM | Difference |
|---|---|---|---|
| 2 vCPU, 4 GB, 40 GB | CX23 €5.49 | CAX11 €5.99 | ARM +9% |
| 4 vCPU, 8 GB, 80 GB | CX33 €8.49 | CAX21 €10.49 | ARM +24% |
| 8 vCPU, 16 GB, 160 GB | CX43 €15.99 | CAX31 €20.99 | ARM +31% |
| 16 vCPU, 32 GB, 320 GB | CX53 €29.49 | CAX41 €40.99 | ARM +39% |

Django and HTMX run equally well on either, so there is no longer an argument for the ARM line on this workload.

**The database host is shared, not dedicated, because the premium has become severe.** The reason to want dedicated cores on a database is real: app requests are short and stateless, so CPU steal from a noisy neighbour spreads a few milliseconds across many requests, whereas on Postgres the same steal lands inside a transaction that other requests are queued behind, and surfaces as p99 latency spikes and lock contention. But look at what isolation now costs:

| | Shared | Dedicated |
|---|---|---|
| Medium database host | CX43 — 8 vCPU, 16 GB, 160 GB — €15.99 | CCX13 — 2 vCPU, 8 GB, 80 GB — €42.99 |
| High database host | CX53 — 16 vCPU, 32 GB, 320 GB — €29.49 | CCX33 — 8 vCPU, 32 GB, 240 GB — €138.49 |

At Medium, dedicated cores mean paying 2.7× for a host with a quarter of the cores and half the RAM. That is not a defensible trade for a database holding ~3 GB of data. The recommendation is the shared CX host with a documented upgrade path: if p99 latency shows steal under real load, CCX13 costs a further €32.40/month all-in (£27.80) at Medium, and CCX33 a further €130.80 (£112) at High.

## Backup and availability posture

The base Ubicloud tier has no standby, which means a database host failure is a restore rather than a failover:

| | PITR from archive | Streaming replica |
|---|---|---|
| **Protects against** | Host loss, corruption, a bad migration, `DELETE` without `WHERE` | Host loss only |
| **RPO** (data lost) | Seconds to ~1 minute | ~0 synchronous, seconds asynchronous |
| **RTO** (time down) | Tens of minutes | Seconds to a couple of minutes |
| **Recovers a logical mistake** | Yes — the point of *point-in-time* | No, the replica replicates the mistake faithfully |

A replica is not a backup and a backup is not availability. For a pathway completed over weeks, tens of minutes of downtime is an accepted trade: no participant loses work, and client-side autosave should carry an in-progress section across a brief outage. Adding one Ubicloud standby is roughly a doubling of the Postgres line, not a re-architecture, should that judgement change.

Whichever option is chosen, restores must actually be rehearsed on a schedule. Plan 1's qualifier — "adequate at this scale provided restores are actually tested" — is the load-bearing clause.

## Self-managed Postgres alternative

The same profiles, same staging and email, running Postgres directly with pgBackRest archiving WAL to the Storage Box:

| Scenario | Configuration | Self-managed all-in | Saving vs Ubicloud |
|---|---|---|---|
| Low | Everything on one CX33 | €22 / £19 | €14–18 / £12–15 |
| Medium | CX43 app + CX43 database | €55 / £47 | €21–44 / £18–38 |
| High | LB11 + 2 × CX43 app + CX33 worker + CX53 database | €124 / £106 | €82–128 / £70–110 |

At Low the saving is most of the bill for perhaps an afternoon of setup, since Postgres shares the one host anyway. At High it is substantial money, but upgrades, WAL monitoring and restore rehearsals become a standing responsibility for a small team.

The gap has widened since Hetzner's price changes: cheap shared CX hosts make self-managing comparatively more attractive than it was, because the managed service is priced against dedicated-class hardware. The managed figures above still stand as the recommendation for Medium and High, on the grounds that a team this size should not be the on-call DBA — but it is now a closer call than the earlier draft suggested.

## Email volume

Scaleway Transactional Email's free tier is around 300 messages per month, which covers development and nothing more. The volume comes from the pathway itself. Per participant lifecycle, approximately:

| Surface | Messages |
|---|---|
| Magic-link logins (Plan 1 recommends no password storage, so every login is an email) | 10–20 |
| Observer invitations plus reminders | 10–16 |
| Mentor invitation and the four mentor briefs | 5 |
| Result summary and letter delivery | 2 |

Call it ~40 messages per completed pathway. Assuming the registered base completes over about a year: ~3,400/month at Low, ~17,000 at Medium, ~67,000 at High, at roughly €0.25–0.40 per thousand. If Google sign-in displaces magic links for most participants, halve those figures.

Cost is not the risk here — deliverability is. Most observer invitations go to personal mailboxes at the large consumer providers, which is precisely where a cold sending domain gets filtered. A dedicated transactional subdomain with SPF, DKIM and DMARC, warmed slowly and never mixed with marketing sending, matters considerably more than the €20.

## Price sources and verification

Hetzner figures were read on 19 September 2026 from the price feed the website itself renders from:

- `https://www.hetzner.com/_resources/app/data/app/live_data_prices.json`
- equivalently `https://website-price-api.hetzner.com/api/v1/products/{productId}`

Product identifiers were mapped to plan names from the `product-key` attributes on `/cloud/cost-optimized/`, `/cloud/general-purpose/`, `/cloud/load-balancer/` and `/storage/storage-box/`. Prices below are EU locations (FSN1/NBG1/HEL1), monthly, net of VAT. Note that the CPX11–CPX51 plans still listed on the site are **US-only** and priced far higher; the current EU line is CPX12–CPX62.

| Product | Spec | Monthly |
|---|---|---|
| CX23 / CX33 / CX43 / CX53 | 2/4/8/16 vCPU Intel-AMD, 4/8/16/32 GB | €5.49 / €8.49 / €15.99 / €29.49 |
| CAX11 / CAX21 / CAX31 / CAX41 | 2/4/8/16 vCPU Ampere, 4/8/16/32 GB | €5.99 / €10.49 / €20.99 / €40.99 |
| CCX13 / CCX23 / CCX33 | 2/4/8 dedicated vCPU, 8/16/32 GB | €42.99 / €85.99 / €138.49 |
| LB11 / LB21 / LB31 | Load balancers | €7.49 / €21.49 / €42.99 |
| BX11 / BX21 / BX31 / BX41 | Storage Box 1/5/10/20 TB | €3.20 / €10.90 / €20.80 / €40.60 |
| IPv4 address | per address | €0.50 |
| Backups | 20% of the server's price | — |
| Snapshots | per GB per month | €0.0143 |
| Traffic | 20 TB included per EU server, then per TB | €1.00 |

**Not verified:** Ubicloud managed Postgres and Scaleway TEM pricing — both domains were unreachable from this environment. Those two lines should be confirmed before the figures are used for budgeting.

## Not included

- **Video hosting** — external by decision; it adds no load to these hosts and is a separate vendor line.
- **Monitoring** — self-hosted GlitchTip and uptime checks fit on the worker host at High, and on the single app host at Low and Medium.
- **Object storage for participant uploads** — no requirement identified in the current scope.

The staging host is deliberately excluded from PITR. Restoring staging from a production backup is a data-protection event, not a convenience, and the pathway documents hold special category data under Article 9.
