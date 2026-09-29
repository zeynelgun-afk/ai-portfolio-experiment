# Expanded small-cap earnings and filing study (exploratory)

**Decision:** the evidence does not justify integrating a profitable trading rule. Keep this as a research hypothesis. A read-only research workflow could be tested prospectively after point-in-time data capture is built.

## Design and sample

- Deterministic selection of 20 currently active, US-listed, USD common-equity profiles with current market capitalization of $200m–$5bn and at least eight available earnings transcripts; the historical event cap was screened to the same range.
- Five-year window through 2026-09-29. The event sample is conditional on current survival and transcript coverage, so failed/delisted companies are missing.
- The earnings-release panel contains 323 events; 212 pass the historic-cap and price-window filters. They cannot be classified reliably with current estimates because historical consensus vintages are unavailable and statement period keys are missing on many earnings rows. Do not use this panel to claim an earnings-surprise edge.
- The filing panel contains 226 filing events; 211 have measurable price windows, but only 14 unique issuers contribute. Three same-quarter year-over-year directions are shown separately: revenue positive YoY, gross-margin expansion, and operating cash flow improvement. “Improving” requires all known indicators positive and at least two known; “deteriorating” requires at least two known and none positive; otherwise mixed/incomplete. This is a descriptive grouping, not a fitted score.
- Entry proxy is the close of the next NYSE session after the filing date. Returns use dividend-adjusted closes for 20 and 60 exchange sessions, compared with IWM and a broad sector ETF. Round-trip costs are assumed, not measured.

## Filing-date results versus IWM

| Operating group | Horizon | Filing events | Issuers | Event median gross | Event median excess | Event median net at 100 bp | Median issuer-mean excess | Median issuer-mean net at 100 bp | Leave-one-issuer-out mean excess range |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Improving | 20 | 40 | 11 | 3.21% | 0.40 pp | 2.21% | 0.60 pp | 1.75% | -0.62 to 1.34 pp |
| Improving | 60 | 40 | 11 | 4.85% | 0.76 pp | 3.85% | 4.31 pp | 7.68% | -0.47 to 5.59 pp |
| Deteriorating | 20 | 40 | 8 | 2.07% | -0.28 pp | 1.07% | -1.07 pp | 0.34% | -0.52 to 2.15 pp |
| Deteriorating | 60 | 40 | 8 | 0.84% | -0.41 pp | -0.16% | -1.37 pp | 2.34% | 1.61 to 5.95 pp |
| Mixed / incomplete | 20 | 131 | 14 | 1.23% | -1.34 pp | 0.23% | -0.13 pp | -0.51% | -0.59 to 0.16 pp |
| Mixed / incomplete | 60 | 131 | 14 | 1.17% | -3.90 pp | 0.17% | -3.30 pp | -0.42% | -2.57 to -1.58 pp |

Event-level median is not a portfolio return and issuer-balanced metrics are not an executable strategy. Improving has a mildly positive median excess, but removing one issuer can turn the average negative; sector-ETF comparisons are coarse and volatile. At the improving-group 60-session event median, assumed 250 bp round-trip cost leaves 2.35%, but this is not based on observed spreads, market impact, cash drag, or a portfolio weighting rule. The issuer-balanced 60-session cost-adjusted median is especially sensitive to the small issuer set and outliers.

## Why this is not enough to call profitable

1. **Survivorship and selection:** only current active transcript-covered names were sampled; the effective filing sample is 14 companies, with repeated quarterly observations.
2. **Point-in-time fundamentals:** vendor statement histories may contain retrospective restatements. Original filing values and their availability timestamps were not preserved in immutable snapshots.
3. **No reliable release surprise grouping:** estimate vintages and consistent quarter keys are missing; estimates may have been revised after the release.
4. **Event mismatch:** SEC filing accepted date can follow the earnings release and call. This tests a filing-triggered observation, not the earliest public news catalyst.
5. **Catalyst context is absent:** guidance, call commentary, material company news, sector narratives, financing/dilution, and peer announcements were not coded against contemporaneous timestamps. These can explain why the business changed or why price moved.
6. **Execution and inference:** transaction costs are scenarios, not historical bid-ask/impact; no issuer-cluster confidence interval, matched control, portfolio construction, or prospective holdout has been established.

## Integration brainstorm

A practical next integration is a **shadow research card**, not a buy/sell signal:

1. At every earnings release, filing, guidance update, or material company news item, create an immutable event record with source URL, publication/acceptance timestamp, source text hash, fiscal period, and the data version available at that time.
2. Separate event layers: (a) reported financial change and cash/dilution quality, (b) management guidance and call evidence, (c) company-specific news/catalysts, (d) sector/peer trend, and (e) price/volume reaction. Store positive evidence, counter-evidence, and unknowns independently.
3. Have the research process draft a thesis delta with citations and confidence; preserve the prior thesis and explain what changed. LLM extraction should never see future prices or outcome labels in historical evaluation.
4. Show the card in the research/watchlist workflow and send Telegram only for material new evidence, missing-data failures, and recovery; no order placement or automatic portfolio decision.
5. Run a prospective shadow cohort for at least 12 months. Freeze definitions first; capture delisted names and point-in-time fundamentals/news; use next-session executable prices, spread/impact estimates, sector/size controls, issuer-cluster confidence intervals, and compare against a plain benchmark. Promote to an actionable ranking only after the edge persists out-of-sample after realistic costs and risk metrics.

This architecture may improve research coverage even if it never becomes a profitable strategy. Its value should first be judged by evidence freshness, thesis-change accuracy, and missed-catalyst reduction; investment performance remains a separate unproven claim.

## Reproduction

Input snapshot: `output/earnings-expanded/20260929-5y-20/inputs.json`  
Analysis: `output/earnings-expanded/20260929-5y-20/replay-v5/report.json`  
Replay is deterministic and network-free:

```bash
python earnings_expanded_study.py \
  --replay output/earnings-expanded/20260929-5y-20/inputs.json \
  --output output/earnings-expanded/replay
```
