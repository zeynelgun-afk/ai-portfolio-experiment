# Analyst target revision momentum — design proposal

Status: brainstorming requested by the owner; not an enabled trading or scoring rule.

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
