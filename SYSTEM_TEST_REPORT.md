# System test report — 28 September 2026

## Decision lifecycle extension — 29 September 2026

- 348 automated tests passed. Added coverage includes claim-to-position escalation,
  executable falsifiers, review expiry, evidence-bound condition changes, positive
  triggers, moving-average references, durable material-event replay prevention,
  unchanged holdings on HOLD stop updates, split-adjusted monitors and retry obligations.
- Prompt contract evaluation, Python compilation, actionlint, dashboard generation and
  generated JavaScript syntax validation passed. Production portfolio state was not
  changed by these tests.
- Isolated real-provider probes collected FMP evidence and called the production deep
  model. They exposed numeric-provenance false rejections for known claim labels and
  moving-average condition identifiers; narrow label handling and regressions fix these.
  Numeric factual claims still require bound evidence.
- The final live probe passed the main decision/monitor schema and reached independent
  semantic review. That reviewer failed exact-source citation validation after retries.
  No decision was accepted and no execution or Telegram test message was sent. Thus
  live end-to-end acceptance is NOT verified; offline passing tests do not establish
  investment correctness. Failed reviews stay pending for a subsequent scheduled run.
- Analyst target revision research is documented in `docs/analyst_revision_design.md`.
  Read-only MU target summary/news access was verified; no analyst trading signal,
  scoring weights or predictive-performance claim was enabled.
- Exact normalized news text is deduplicated across republication and regrouping;
  paraphrased reports of the same event can still need stronger semantic deduplication.
  Financial event identities are per metric, fiscal date, value and unit, not globally
  per filing. Existing legacy monitors are migrated through validated reassessment,
  not by inventing thresholds in a code migration.

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
- **Intraday crash consistency:** atomic portfolio writes and replay protection are present, but a
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


## Owner-authorized resilience follow-up — 28 September 2026

Implemented the requested weekly transaction gate, field-aware numerical provenance and
independent heartbeat with bounded automatic recovery. The charter hash is unchanged.

- Weekly decisions now return JSON to `weekly_round.py`; the model has no file tools.
  All A-F sections, cash/shares, measured weekly close, thesis coverage/conditions and
  watchlist dispositions must validate before persistence. The executor owns fills and
  log writing. A write-ahead journal can finish interrupted writes without requesting
  another decision; conflicting newer state is never overwritten.
- Saturday remains enabled, including holiday weekends. Friday holidays use the last
  completed exchange session. Sunday catch-up is allowed; recorded weekly slots cannot
  replay, including historical rounds predating this change.
- Numeric decision prose uses typed source references. Code renders company, metric,
  value, unit, observation time, source and snapshot. Intraday sources are issuer-scoped;
  old prose cannot authorize a number. Numeric trade/threshold choices remain free.
  Evidence or schema rejection retries at most three times, then fails closed.
- Weekly/intraday evidence artifacts retain the original measurement packet and source
  references for ninety days. Provider truth and semantic correctness of surrounding
  prose are not established by this structural check.
- Independent systemd watchdog: daily checks at 23:00 UTC (02:00 Europe/Istanbul), NYSE/holiday-aware intraday deadlines,
  separate closing-review deadline and Saturday weekly deadline. A green skipped detector
  does not count as a measurement. Missing jobs can be dispatched; only dependency-stage
  failures may be rerun. Running jobs block dispatch. No repair rewrites strategy or
  investment history, disables validation or replays a failed execution/commit.
- Repair limits: two attempts per incident, two-hour cooldown, four per UTC day; state
  and repair intent persist before API calls. Telegram distinguishes repair requested,
  unresolved incident and observed successful recovery.

Validation: 263 local tests, including 34 new resilience scenarios. Real OpenRouter
Haiku and Opus calls passed typed-evidence and weekly structured-proposal checks; invalid
schema/reference responses were rejected and corrected within the bounded retry loop.
The Opus scenario used synthetic inputs and wrote no investment records. It tests provider
integration, not profitability or production decision quality. Prompt inventory now has
nineteen entries (fourteen base templates plus five vetted adaptive reminders).

The watchdog runs on the owner's local machine independently of GitHub's scheduler.
Monitoring pauses when that machine is off or disconnected; persistent timers check on
return. An always-on external host remains necessary for uninterrupted monitoring.

API references: [dispatch a workflow](https://docs.github.com/en/rest/actions/workflows)
and [read runs / rerun failed jobs](https://docs.github.com/en/rest/actions/workflow-runs).


Runtime notification transport: the local environment has no Telegram destination ID,
so the installed watchdog uses the existing GitHub Telegram workflow and repository
secrets. No secrets were exported. Detection is independent of GitHub scheduling, but
notification delivery in this mode still needs GitHub API/runners. Direct Telegram mode
is implemented and requires the local target chat ID and matching bot credentials.


## Daily cloud migration — 28 September 2026

Supersedes the local-runtime limitation above. The production watchdog now runs on GitHub
Actions daily at 23:00 UTC (02:00 Europe/Istanbul), with direct Telegram delivery using
repository secrets. Local monitoring is disabled during migration. Repair limits and
incident history are persisted on a separate `watchdog-state` branch, with conditional
SHA updates before repair dispatch. Delayed jobs evaluate the prior daily deadline;
predeployment missing runs do not trigger retrospective repairs. GitHub-wide outages
remain a shared dependency. Local regression suite: 267 tests passed, including remote
checkpoint failure blocking dispatch, SHA updates and delayed-deadline evaluation.


## FMP-primary / yfinance-fallback — 28 September 2026

Central provider routing replaces unconditional Yahoo queries. Primary failure, empty
or malformed data, issuer mismatch and stale timestamps permit failover; normal FMP
success leaves Yahoo idle. Both providers undergo identical price/session validation.
A full price series belongs to one provider. News cursors use a consistent timestamp
separator across providers; original publication stamps remain in the evidence.

Live read-only verification: AMD, MU, ANET, NVDA, SPY and SMH closes all used FMP with
25 September as the last completed session. AMD returned 507 history rows; fundamentals,
earnings, news and detector prices/news used FMP. A patched Yahoo sentinel confirmed
zero backup calls. An injected FMP outage then fetched a real Yahoo backup (ten daily
rows, same latest session). Neither probe wrote portfolio, thesis or trade records.

Provider failures/failover are archived and summarized to Telegram once per workflow.
FMP-only optional enrichment is not silently replaced by non-equivalent Yahoo metrics.

Final provider verification: 282 tests passed. An isolated weekly collection also
completed for all four holdings with FMP serving history, earnings, fundamentals and
news for every holding. Forward P/E was explicitly unavailable for all four; no
second provider or non-equivalent ratio was substituted merely to fill that optional
field. The isolated run skipped LLM research and did not modify production records.

## 2026-09-28 — Session execution and research depth upgrade

Owner-authorized change: weekend research remains scheduled, but new weekly fills
require an open NYSE session and renewed research/decision/quote validation. Earlier
portfolio history is preserved. The charter hash was updated only for this execution
boundary; position sizing authority remains unchanged.

Validation:
- 303 offline tests passed, including weekend/holiday/after-close refusal, stale/future
  quote rejection, session repricing, shared directional replay protection, queued-plan
  execution once, quarterly provenance, fallback coverage and prospective horizon checks.
- Prompt inventory/regressions, actionlint and static dashboard build passed.
- Read-only live FMP probe: AMD income, balance sheet and cash flow each returned eight
  quarters; fourteen derived/source facts were available. Four discovery feeds answered.
- Injected FMP statement outage: actual yfinance backup returned five valid AMD quarters.
  An empty historical Yahoo column was excluded without discarding current statements.
- Isolated one-company live research run: all three model roles succeeded. Fundamental
  output contained summary, bull_case, bear_case, invalidation and data_gaps. No portfolio,
  live thesis or trade records were modified by this probe.
- Live sector-response inspection exposed averageChange mapping and coverage issues;
  collector now uses the last completed session and preserves sector/exchange/date.

Limits: future 5/20-session cohorts do not yet exist and no performance improvement is
claimed. No end-to-end scheduled session fill was triggered during validation. Guidance
and filing footnotes are explicitly unavailable, transaction costs remain unmodeled,
and channel attribution is observational rather than causal. Provider/model probes are
point-in-time checks, not guarantees of future availability.


## Economic evidence and corporate actions — follow-up to `74a522d`

- 325 automated tests pass. The 22 added behavioral checks cover fresh/stale quarterly
  evidence and units, report-specific trigger deduplication, missing-data trade blocking,
  weekly economic-condition requirements, review-call budget reservation, exact citations,
  partial/uncertain news, unsupported semantic claims, split/reverse-split cost invariance,
  dividend entitlement/payment idempotency after sale, revised/late events, issuer currency,
  interrupted accounting-journal recovery and adjusted-return fallback.
- Python compilation, workflow actionlint, the English prompt inventory/regression gate
  (20 entries including reminders), dashboard build and generated JavaScript syntax pass.
- Read-only FMP probes returned 507 rows each for MU/SPY raw/adjusted return series with
  latest completed date 2026-09-25. SPY event parsing returned 136 historical events.
  MU returned 10/10 usable news excerpts; issuer identity/currency checks succeeded.
- An isolated live corporate initialization verified all four current issuer identities
  and SPY/SMH benchmark anchors without changing cash, positions or trade history. The
  production portfolio files were not written by these tests.
- A real independent-model probe initially rejected an attributed forecast too broadly.
  The English reviewer instructions were corrected to distinguish reporting a forecast
  from asserting that it occurred. The bounded repeat accepted the explicitly attributed,
  uncertain analyst forecast and rejected the same forecast presented as confirmed
  earnings with all risks eliminated. This is a small behavioral probe, not a statistical
  accuracy claim or proof of investment quality.
- Provider outage and adjusted Yahoo fallback were exercised with deterministic fixtures;
  no real Yahoo outage/failover or actual dividend/split in the live portfolio is claimed.
- Existing historical portfolio records remain untouched. Corporate accounting activates
  prospectively on the next scheduled workflow; economic thresholds migrate at the next
  successfully reviewed weekly decision. Exceptional actions/ambiguous identity require
  reconciliation rather than guessed trades. Non-GitHub watchdog work stays deferred.
- Existing unrelated ResourceWarnings in amendment/auditor file reads do not fail tests.
