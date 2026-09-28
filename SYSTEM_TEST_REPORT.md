# System test report — 28 September 2026

## Scope and evidence boundaries

Baseline: `f9e4fce`; concurrent README-only commits were preserved. Tests covered data
collection, model adapters, deterministic checks, execution, logs, valuation, prompt
improvement, dashboard rendering and notification plumbing. Production holdings, trade
history, thesis records and benchmark references were not modified by the test runs.

## Verification completed locally

- 229 automated tests passed, including the isolated detector → thesis model adapter →
  executor → decision log → valuation → Telegram report-file scenario.
- Price/news threshold and hysteresis tests, malformed JSON, unavailable auditors,
  news retry, stale decision/quote refusal, duplicate execution, HOLD logging, failed
  lock-file recovery, negative-cash prevention and amendment export were exercised.
- Exchange-session tests cover weekends, 3 July 2026 (observed holiday), Thanksgiving,
  Christmas, winter hours, early close and post-close review. Saturday weekly analysis
  remains enabled at the owner's explicit instruction.
- 12 base English prompt templates plus five adaptive reminders inventoried; 18 structural/regression checks passed.
  This is not an automatic proof that every possible future English sentence is safe.
- `actionlint`, Python compilation and fatal-error static checks passed.
- Local source statement coverage: 67%; executor 94%, reassessment 88%, valuation 84%,
  number gate 93%. Network-heavy Scout/weekly collection and branch-management paths
  have lower offline coverage. This excludes coverage from the separate live probe.

## Live provider evidence (isolated copy)

The working code and data were copied to a temporary directory, with only the necessary
provider credentials passed through process environment variables. No secrets were
written to evidence files.

- `update.py`: exit 0, valuation/report generation completed.
- `weekly_data.py`: exit 0; AMD, ANET, MU and NVDA all returned data dated 25 September;
  4/4 symbols, 0 missing fields in this run, 0 research errors.
- Macro, fundamental and sentiment research returned valid outputs through the real
  provider. This verifies transport and expected shape, not investment correctness.
- `audit.py --no-prices`: exit 0; deterministic record audit generated.
- `detector.py --dry-run`: exit 0; live collection with no model reassessment or state write.
- Configured default model IDs were present in the live OpenRouter catalogue.

The complete current production decision workflow was not invoked: doing that can make
new paper-portfolio decisions. Its decision/execution chain was instead exercised in the
isolated deterministic test, and live provider calls were checked separately.

## Browser evidence

The public dashboard was loaded in Chromium. The equity chart's table toggle worked;
static fallback explicitly indicated that live prices were unavailable. Its missing
favicon was fixed in the template. The rebuilt page rendered at 390×844 and 1440×1000
with no horizontal overflow. The template now includes a mobile viewport and English
language metadata, avoids exposing partial holdings as a complete valuation, and escapes
embedded JSON against script-tag termination.

GitHub Pages has no Claude connector runtime. It is a published portfolio snapshot,
not a verified live quote terminal. That limitation is visible in the page.

## Corrections

1. Exchange calendar and second execution-time gate, including DST/holidays/early closes.
2. Quote timestamps and a maximum acceptable age; stale/unknown/future quotes cannot trade.
3. Decision bundle tied to its detector check; stale or unconsumed bundles fail visibly.
4. SELL/TRIM share one direction lock; the ledger reconstructs missing same-day locks.
5. Fractional overspending and invalid stops rejected; HOLD decisions logged.
6. Failed model assessments reported through a workflow health step, without cooldown;
   failed news-triggered deep reassessment restores the news cursor for retry.
7. A thesis handled by the deep model is excluded from the fast-model rewrite in the same run.
8. Missing/nonfinite/mismatched-date closes rejected; partial daily candles excluded;
   unset stops no longer crash valuation; benchmark differences labelled percentage points.
9. Weekly collection always includes actual holdings, uses unadjusted closes consistently,
   can be imported without running a collection, and flags incomplete research output.
10. Research model choice is explicit rather than silently selecting the newest catalogue entry.
11. Scout output validated and saved atomically.
12. Prompt source/evidence policy shared across roles; indicator/count exemptions narrowed
    so invented `50%` or `5%` claims are not automatically accepted.
13. Prompt inventory, immutable charter hash, regression fixtures and CI added; amendment
    artifacts provide an owner-review fallback when Actions cannot open PRs.
14. Dashboard deployment follows successful portfolio workflows as well as manual pushes;
    misleading zero-latency/guaranteed-hallucination-elimination claims removed.

## Remaining improvements, in priority order

- **Weekly transaction gate:** the weekly Claude action can still edit portfolio files
  directly. Route weekly decisions through a structured proposal and deterministic
  executor too; test cash/trade/thesis invariants before committing the weekly round.
- **Field-aware numerical provenance:** matching numeric values is only a coarse gate.
  Associate every figure with a symbol, metric, timestamp and source so an existing number
  cannot be reused for an unrelated claim. The current gate does not establish semantics.
- **Historical watchlist membership:** deferral counters lack a dated candidate membership
  ledger. Newly discovered symbols can be counted against rounds before they entered the
  universe; fix this with forward-recorded membership, not invented retrospective dates.
- **Separate cadence/value series:** `history.csv` now includes ad hoc and intraday records.
  Weekly metrics should explicitly select weekly observations and preserve as-of timestamps.
- **Total provider budget:** the reassessment counter is not a global spend cap. Scout,
  research, news and auditors need shared usage/cost telemetry before claiming a total budget.
- **Prompt semantic evaluation:** add held-out scenarios and repeated model evaluations.
  A deterministic prompt gate and a few successful responses cannot establish improved
  reasoning or trading returns. Compare error rates, source fidelity and decision consistency.
- **Freshness watchdog:** workflow failure alerts do not detect a scheduled workflow that
  never starts. Add a separate heartbeat/watchdog and persistent last-success timestamps.
- **Crash consistency:** atomic portfolio writes and replay protection are present, but a
  journal spanning portfolio, lock and log files would make interrupted recovery complete.

## Bounded automatic prompt changes

The owner requested automatic improvement while retaining the investment logic. The
implemented default permits selecting only one of five prewritten evidence/format
reminders. It needs three recurring consensus findings plus 20 baseline model outcomes.
After 20 new outcomes, a failure-rate increase above 15 percentage points rolls back and
quarantines the reminder. Regression tests cover activation, insufficient evidence,
retention, rollback, quarantine, schema-error measurement and arbitrary-state-text refusal.
No reminder has yet been activated: production metrics must accumulate first. Free-form
strategy or charter rewrites are not automatically adopted. This scope was chosen to
preserve the owner's stated main logic; unrestricted rewriting was not enabled.

## Reference material

The exchange schedule uses [pandas-market-calendars session data](https://pandas-market-calendars.readthedocs.io/en/latest/usage.html).
The dashboard completion trigger follows [GitHub workflow event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), avoiding reliance on a bot-generated push starting another workflow.

## Deployment evidence

Implementation commit: `43baf48`.

- [System Checks 36407433789](https://github.com/zeynelgun-afk/ai-portfolio-experiment/actions/runs/36407433789): success; 229 tests passed on GitHub's Python 3.12 runner, prompt gate and dashboard build passed.
- [Pages deployment 36407433757](https://github.com/zeynelgun-afk/ai-portfolio-experiment/actions/runs/36407433757): success; the public page returned the corrected text.
- [Intentional failure drill 36407455420](https://github.com/zeynelgun-afk/ai-portfolio-experiment/actions/runs/36407455420): tests passed; only the explicitly labelled notification-drill step failed, as intended.
- [Automatic Telegram alert 36407518836](https://github.com/zeynelgun-afk/ai-portfolio-experiment/actions/runs/36407518836): launched by the failed workflow rather than manual notification dispatch. Delivery evidence was checked in its logs.

Production trading was not triggered. The bounded adaptation controller is installed,
but activation awaits enough production observations; no improvement in investment
performance is claimed.
