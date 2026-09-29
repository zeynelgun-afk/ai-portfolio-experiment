# Analyst target revision momentum — implementation and evaluation

Status: approved research/reassessment channel implemented on 29 September 2026.
It is not a standalone trading rule or a profitability-weighted score.

## Operational behavior

`analyst_revisions.py` collects FMP target news (paginated, bounded at ten pages) and
annual consensus estimates once per UTC date and symbol. Intraday detection covers
held positions; weekly collection also covers its research universe. First observations
are immutable in `state/analyst_revision_observations.json`; errors are explicit and
retry at the next daily observation. No-record responses are unknown, not neutral.
yfinance aggregates cannot reconstruct matching firm histories, so this dataset is
marked unavailable when FMP fails rather than fabricated from an incompatible fallback.

For each 7/30/90-day window, the latest observed nonzero revision per normalized firm
counts once. Reiterations do not erase an earlier revision within the window. Reported
unchanged observations and unpaired firms are separate. A missing predecessor is not
proof of initiation. Explicit initiation/resumption headlines start a new comparison
chain. A recognized firm in the headline that contradicts the provider's analyst-company
field quarantines that record; a recent conflict inhibits automatic routing.
Comparison is to the previous observed same-firm target, which
can predate the window by months; provider history need not contain every real update.
Baseline age is retained. Adjusted targets are compared without mixing raw bases;
event identities use raw reported targets and dates to survive split restatement.
Same-day conflicting values break the comparison chain; recent conflicts inhibit
automatic routing, while unrelated historical conflicts stay visible in coverage.

With complete bounded-provider coverage and no recent conflicts, at least two firms
in the dominant direction over 30 days request whole-thesis review. This is a declared
routing heuristic, not an optimized return threshold. Positive and negative events use
the same route. Successful reviewed decisions acknowledge the constituent events;
failure remains retryable. Analyst signals never bypass the execution lock or session
and quote safeguards. Existing decision/failure Telegram flows include these reviews;
daily collection failures and weekly evidence failures enter the alert chain.

## Multiple explanations, not an earnings-only gate

Every decision with analyst evidence must include `analyst_review` across four axes:

- Earnings: same-fiscal-period EPS/revenue consensus changes between actual observations.
- Company news: contracts, products, partnerships, regulation and other issuer events.
- Sector/theme: industry demand, rotation hypotheses, attention to a narrative and related news.
- Valuation: changes in multiples, discount rates, positioning or the growth story's perceived value.

Each axis records `reported_reason`, `context_only` or `unknown`, an assessment and bound
source IDs. A reported reason requires an attributable news source and independent
semantic checking. A contextual connection stays an inference. Price movements alone
do not establish fund flows, crowding or investor attention. Missing or unchanged EPS
does not veto company-news or sector/theme explanations. Target increases can still
coexist with valuation risk and opposing evidence. The original analyst rationale can
remain unknown even when market context is informative.

`ANALYST_REVISIONS.md` and the dashboard expose dated coverage. Accepted multi-axis
reviews persist with the thesis and decision history. `research_metrics.py` measures unique observed event cohorts after 20/60/120 exchange
sessions against SPY using total-return data, starting at the next session close. Revenue
consensus changes are tracked as a separate event cohort: same fiscal period, dated
provider snapshots over 7/30/90-day lookbacks, revision percentage, coverage-count
context, and next-session 20/60/120-session outcomes with explicit cost sensitivities
and path-risk measures. FMP does not expose analyst identities in this consensus series,
so coverage-count changes are not a count of analysts who raised or cut estimates. Records include insufficient/mixed
cases; immature or unavailable endpoints remain pending. This is before-cost research
performance with overlapping selected cohorts, not a tradable backtest or causal proof.

## Hypothesis

Recent upward revisions across independent analyst firms may identify improving
expectations worth reassessing. A high target level alone is not a revision, and a
recently published target does not establish a short investment horizon. Predictive
value and useful cutoffs remain untested.

## Verified provider capabilities

FMP `price-target-news` returned 100 MU records with date, analyst name/company, raw and
adjusted target, price when posted, publisher and source URL. In this bounded probe the
records spanned 2025-09-24 through 2026-09-28 and named 27 firms. This verifies access and
shape, not full universe/history completeness or target accuracy. `price-target-summary`
provides last-month/quarter/year averages and counts. These are overlapping activity
windows, not a time series of a fixed analyst cohort; their difference does not prove
same-analyst revisions. The news payload has no explicit previous-target field.

## Revenue consensus revision measurement

For each same-period annual revenue estimate, the system compares the current FMP
consensus with dated snapshots at or before 7/30/90-day cutoffs (allowing at most a
14-day gap between the cutoff and baseline). Each window reports its baseline timestamp,
elapsed days, fiscal period, percentage change, and provider coverage counts. Missing
snapshots, period mismatches, zero baselines, or conflicting currencies remain
unmeasured. The count of covering analysts is context only: a change from eight to nine
does not establish that one analyst upgraded, because identities and individual forecast
changes are not supplied. Prospective events receive separate 20/60/120-session outcome
records; they do not become trade instructions.

## Proposed measurements

- Compare each firm's latest eligible target with its own preceding dated target;
  distinguish initiations, unchanged reiterations, increases and decreases.
- Show independent-firm increase/decrease counts, revision breadth, median percentage
  revision and sample coverage over 7/30/90-day windows. Do not count syndicated news
  multiple times or count several updates from one firm as several independent votes.
- Keep target change, target-to-price gap and the stock's preceding price move separate.
  Check whether analysts merely followed a price rally and whether dispersion widened.
- Link source text to the reason: revenue/EPS estimate revision, margin outlook,
  valuation multiple or a changed forecast horizon. Missing reasons remain unknown.
- Compare EPS/revenue estimates for the SAME fiscal period across observation dates.
  Different forecast years are not historical revisions. Store prospective snapshots
  if point-in-time forecast history is unavailable.

## Data and evaluation boundaries

Normalize issuer identity, firm aliases, split basis, units and timestamps. Paginate
until the requested window and each required preceding observation are covered;
otherwise report incomplete coverage. Never interpret no records as no revisions.
Do not present provider-restated historical fields as known at the original event time.

Initially use this as research prioritization and an evidence-backed decision-review
trigger, with both positive and negative signals. Do not hard-code an automatic BUY
or pick arbitrary profitable-looking weights. Freeze observations prospectively and
measure subsequent returns/excess returns, coverage, turnover and costs over prespecified
horizons. Use out-of-sample/walk-forward comparisons before claiming predictive benefit.
The existing prospective research cohort machinery is a starting point, not causal proof.

## Sources

- https://site.financialmodelingprep.com/developer/docs/stable/price-target-summary
- https://site.financialmodelingprep.com/education/financial-analysis/building-singlestock-estimate--price-target-heatmaps-without-heavy-code

## Integrity and citation repair — 29 September 2026

Integrity version 2 checks explicit headline target amounts against raw provider targets,
keeps conflicting records with their original payload, URL and quarantine reason, and
narrows initiation detection so an issuer starting production is not mistaken for a
broker initiating coverage. Collection caches are versioned: upgrading validation creates
a new dated observation rather than silently reusing or overwriting the old snapshot.
Consistent later observations restore eligibility; tests verify immutable prior evidence.
This does not repair the provider's upstream data or assert an inferred firm identity.

The news assessor and independent semantic reviewer now select code-generated excerpt
IDs. Code restores the exact source ID and text; unknown IDs, modified snapshots and
extra quote text are rejected. Old saved exact-quote outputs retain strict validation
for read compatibility. The semantic reviewer still checks relevance, full context,
contradictions and uncertainty. Valid excerpts do not override an uncertain/unsupported
verdict. Reviews preserve selections, restored quotations and a source-bundle hash.
