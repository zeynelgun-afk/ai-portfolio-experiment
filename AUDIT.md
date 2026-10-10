# Audit scorecard — 2026-10-10T13:38Z

Computed from the repository's own record: the decision log, the trade history, the thesis file and the permanent trigger log. No model produced any number on this page.

10 weekly rounds · 13 intraday decisions

## Label against action

A thesis marked BROKEN while the position was held — the instructions require an action or a different label:

- round #6: **AVGO** marked BROKEN, no trade that round

An unsettled label (BROKEN or WEAKENING) repeated for 3 rounds or more without an action:

- **AMD** — WEAKENING for 3 rounds, through round #7

## Exits, scored against what happened next

The one thing the decision-maker could not know at the time. A good decision can still have a bad outcome — this measures the outcome, not the reasoning.

| Date | Symbol | Action | Exit | Since | Move | Verdict |
|---|---|---|---|---|---|---|
| 2026-08-08 | SNDK | SELL | 1212.21 | 1581.82 | +30.5% | costly |
| 2026-08-22 | AVGO | SELL | 368.45 | 361.54 | -1.9% | neutral |
| 2026-09-05 | AVGO | SELL | 357.90 | 361.54 | +1.0% | neutral |

## Threshold quality

Based on 5 recorded checks. A condition that fires on most checks measures noise; one that has never fired was tied to a number that does not happen.

| Claim | Condition | Severity | Fired | Acted on | Quality |
|---|---|---|---|---|---|
| MU-1 | price_below_sma50_pct | claim | 0 | 0 | never fired |
| MU-1 | stop_proximity_pct | warning | 0 | 0 | never fired |
| MU-1 | volume_ratio_20d | claim | 0 | 0 | never fired |
| MU-1 | daily_change_pct | thesis | 0 | 0 | never fired |
| MU-1 | sector_etf_change_pct | claim | 0 | 0 | never fired |
| MU-1 | daily_change_above_pct | claim | 0 | 0 | never fired |
| MU-1 | fundamental_below | claim | 0 | 0 | never fired |
| MU-2 | earnings_approaching | warning | 5 | 0 | noisy |
| MU-2 | price_below | thesis | 0 | 0 | never fired |
| MU-2 | daily_change_pct | thesis | 0 | 0 | never fired |
| MU-2 | fundamental_below | thesis | 0 | 0 | never fired |
| MU-2 | fundamental_below | claim | 0 | 0 | never fired |
| MU-2 | fundamental_above | claim | 0 | 0 | never fired |
| AMD-1 | price_below_sma50_pct | thesis | 0 | 0 | never fired |
| AMD-1 | fundamental_below | thesis | 0 | 0 | never fired |
| AMD-1 | fundamental_below | claim | 0 | 0 | never fired |
| AMD-1 | fundamental_below | claim | 0 | 0 | never fired |
| AMD-1 | stop_proximity_pct | warning | 0 | 0 | never fired |
| AMD-1 | daily_change_pct | claim | 0 | 0 | never fired |
| AMD-1 | sector_etf_change_pct | claim | 0 | 0 | never fired |
| AMD-2 | price_below | claim | 0 | 0 | never fired |
| AMD-2 | volume_ratio_20d | claim | 0 | 0 | never fired |
| AMD-2 | daily_change_pct | claim | 0 | 0 | never fired |
| ANET-1 | price_below_sma50_pct | thesis | 0 | 0 | never fired |
| ANET-1 | fundamental_below | thesis | 0 | 0 | never fired |
| ANET-1 | fundamental_below | thesis | 0 | 0 | never fired |
| ANET-1 | stop_proximity_pct | warning | 0 | 0 | never fired |
| ANET-1 | daily_change_pct | claim | 0 | 0 | never fired |
| ANET-1 | sector_etf_change_pct | warning | 0 | 0 | never fired |
| ANET-1 | earnings_approaching | warning | 0 | 0 | never fired |
| ANET-1 | price_above_sma50_pct | warning | 0 | 0 | never fired |
| NVDA-1 | price_below_sma50_pct | claim | 0 | 0 | never fired |
| NVDA-1 | stop_proximity_pct | warning | 0 | 0 | never fired |
| NVDA-1 | daily_change_pct | claim | 0 | 0 | never fired |
| NVDA-1 | sector_etf_change_pct | claim | 0 | 0 | never fired |
| NVDA-2 | price_below | thesis | 0 | 0 | never fired |
| NVDA-2 | volume_ratio_20d | claim | 0 | 0 | never fired |
| NVDA-2 | earnings_approaching | warning | 0 | 0 | never fired |
| NVDA-3 | fundamental_below | thesis | 0 | 0 | never fired |
| NVDA-3 | fundamental_below | claim | 0 | 0 | never fired |
| NVDA-3 | fundamental_below | claim | 0 | 0 | never fired |
| NVDA-3 | fundamental_below | claim | 0 | 0 | never fired |

## Decision cadence

| Cadence | Trades | Buys | Exits | Gross traded |
|---|---|---|---|---|
| weekly | 9 | 6 | 3 | 126,421 $ |
| intraday | 0 | 0 | 0 | 0 $ |

## Commentary health

All 8 claims carry an assessed status.

