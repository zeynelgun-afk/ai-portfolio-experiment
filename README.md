# AI Portfolio Experiment: Multi-Agent Research Architecture

**Specialist agents research. Independent auditors challenge. Market changes trigger reassessment.**

Meet an AI research team built to carry an investment idea from discovery to a
traceable portfolio decision. Macro, fundamental and news analysts contribute focused
research. A decision model brings their findings together, while evidence checks and
two independent auditors keep the process accountable.

The work continues after the weekly report. Scheduled market checks look for meaningful
changes, refresh affected claims and trigger a full thesis reassessment when needed.
Every stage contributes to a documented paper-trading experiment that can be inspected,
questioned and measured against SPY and SMH.

**One connected workflow: discover → research → decide → validate → monitor → review.**

### What makes the team different

- **Specialized perspectives:** Separate macro, fundamental and news research contexts.
- **Evidence-linked decisions:** Structured proposals checked against measured source fields.
- **Independent challenge:** Two auditors review the same record and surface shared findings.
- **Ongoing reassessment:** Important changes trigger targeted updates or a fresh thesis review.
- **Controlled improvement:** Recurring findings feed reviewed proposals and bounded prompt adaptation.

**The experiment:** Evaluate this research-and-decision process over 12 months in a
$100,000 virtual portfolio, with SPY and SMH as benchmarks.

- **Start Date:** 5 August 2026
- **Starting Capital:** $100,000 in a virtual portfolio
- **Universe:** Dynamic watchlist focused on technology, AI infrastructure, supply-chain bottlenecks and energy
- **Benchmarks:** SPY & SMH
- **Execution:** Paper trading; no broker orders

## Research architecture

The system combines **weekly research and portfolio decisions** with **intraday
monitoring and event-driven reassessment**. Its multi-agent architecture coordinates
separate LLM calls with specialized prompts and input datasets. It does not implement
a neural mixture-of-experts model or train model weights. The current research calls
run sequentially; separate roles do not imply concurrent execution.

### 1. Opportunity discovery — Scout Agent (`scout.py`)

The Saturday workflow runs a GPT-based Scout before collecting the weekly research
inputs. It requests up to 30 FMP articles and 10 market gainers, with yfinance used
only when the primary dataset fails validation. The prompt asks for 15–20 candidate
symbols around supply-chain bottlenecks, business pivots and related opportunities.
The validated watchlist also retains current holdings, so its final size may differ.

### 2. Specialist research — Multi-Agent Research Team (`weekly_data.py`)

Each analyst receives a separate, focused input dataset:

| Role | Inputs | Output |
|---|---|---|
| **Macro Strategist** | Available rates, yields and sector performance | Macroeconomic outlook |
| **Fundamental Analyst** | Valuation ratios, market capitalization and available insider transactions | Per-company fundamental thesis |
| **News & Sentiment Analyst** | News headlines, analyst targets and consensus grades | Per-company sentiment assessment |

The configured defaults use GPT, Claude and Gemini respectively; environment settings
can override the research models. Their outputs are assembled into each company's
**research dossier**. These opinions supply context, not independent proof of numerical
facts; measured fields and their provenance remain separate.

### 3. Portfolio decisions — Decision Model and Deterministic Execution (`weekly_round.py`)

A decision model receives the research dossiers, portfolio state and audit context.
`WEEKLY_INSTRUCTIONS.md` defines the investment mandate, including market overreaction,
conviction sizing, supply-chain effects and available insider/political-trading signals.
These are strategy instructions, not demonstrated sources of excess returns. The
instructions use Kelly terminology, but sizing remains a model decision rather than
a calibrated Kelly calculation.
A requested signal is usable only when supporting evidence is available.

The model returns a **structured JSON proposal**. Code validates the response schema,
measured prices, evidence references, thesis conditions and cash/share arithmetic before
recording accepted virtual transactions. The model has no direct file-writing or
broker-execution access. The detailed execution and replay safeguards are described below.

### 4. Monitoring — Event-Driven Reassessment (`detector.py`, `reassess.py`)

Scheduled checks run every 30 minutes within valid NYSE sessions. Price conditions use
deterministic thresholds, confirmation checks, hysteresis and a four-hour cooldown.
Unseen news can require a separate model assessment; unsuccessful news assessments
remain pending for retry.

- **Claim-level Update:** Refresh an affected claim when its measured condition changes.
- **Thesis Reassessment:** Re-evaluate the full thesis and propose an action when a thesis-level trigger occurs.
- **Freshness Metadata:** Retain update timestamps, triggers and supporting evidence with the resulting records.

This is periodic polling, not a continuous market-data stream or zero-latency execution.
Detection and response depend on the next scheduled run, confirmation rules, provider
availability and model response time. A trigger can lead to HOLD; it does not require a trade.

### 5. Independent review and bounded improvement (`audit.py`, `reviewers.py`)

A deterministic scorecard summarizes recorded decisions and outcomes. Two auditors
from different model families independently review the same evidence; only matching
pattern findings enter the consensus record.

Recurring consensus findings can produce an instruction-change proposal through
`amend.py`. The weekly workflow currently exports a review artifact rather than
applying a free-form rewrite. Separately, `prompt_adapt.py` can select from five vetted
reminders once its evidence thresholds are met, with monitoring and rollback. Neither
path trains model weights or demonstrates improved investment performance. See the
prompt-improvement sections below for the activation and review boundaries.

## Scheduled workflows (GitHub Actions)

| Workflow | Schedule or trigger | Purpose |
|---|---|---|
| **Intraday Detector** | Weekday 30-minute schedule, gated by the NYSE session calendar | Measure conditions and assess unseen news; trigger validated reassessment when needed. |
| **Post-close Review** | Weekdays at 21:15 UTC, trading days only | Run the full-review path after the session. |
| **Weekly Round** | Saturday 06:00 UTC | Run discovery, research, audit and the weekly portfolio decision using the last completed session. |
| **Daily Watchdog** | Daily 23:00 UTC / 02:00 Europe/Istanbul | Detect missed or stuck jobs, request bounded recovery and notify Telegram. |
| **Pages Deployment** | Relevant data/dashboard pushes, successful weekly/detector runs, or manual dispatch | Generate a static HTML dashboard with Python and publish it to GitHub Pages. |

GitHub Actions schedules are subject to runner delays. The dashboard displays generated
snapshots; it is not a React application or a streaming quote terminal.

## Repository structure

- `scout.py` — Dynamic watchlist discovery.
- `weekly_data.py` — Data collection and specialist research dossiers.
- `market_data.py` — FMP-first data routing with validated yfinance fallback.
- `detector.py` — Session-aware condition checks and news assessment.
- `reassess.py` — Claim updates and thesis-level proposals.
- `weekly_round.py` / `execute_trade.py` — Validated weekly and intraday virtual execution.
- `evidence.py` — Typed references linking numerical claims to measured source fields.
- `portfolio.json` / `theses.json` — Virtual portfolio state and measurable thesis conditions.
- `WEEKLY_INSTRUCTIONS.md` — Decision model instructions and investment mandate.
- `audit.py` / `reviewers.py` — Deterministic scoring and independent model review.
- `amend.py` / `prompt_adapt.py` — Reviewed proposals and bounded automatic prompt reminders.
- `watchdog.py` — Daily monitoring and limited recovery.
- `dashboard/` — Python-generated static portfolio and thesis dashboard.

## Running components locally

Install `requirements.txt` and configure the provider credentials required by the
component before running it. Scout and research calls use external services and can
incur charges; the first two commands below update local research/watchlist files.

```bash
# Discover a watchlist
python scout.py

# Collect data and produce specialist research dossiers
python weekly_data.py

# Inspect detector behavior without writing detector state (can still call providers)
python detector.py --dry-run

# Generate the scorecard and request independent model review
python audit.py --review
```

> This is an experimental paper-trading system, not financial advice. Technical
> checks verify defined software behavior; they do not prove investment quality,
> provider accuracy or future returns.

## Session and execution integrity

The NYSE session calendar gates intraday runs: no data/model/trade steps on weekends or
exchange holidays, and no trades after early closes. Daily post-close reviews run only
on trading days. The **Saturday 06:00 UTC weekly round stays enabled** and evaluates
the last completed session. Session times and delayed quote timestamps are validated
again before execution. The decision bundle must refer to the same detector check.
SELL and TRIM share one daily sell-direction lock; the trade ledger also prevents replay
if writing the separate lock file was interrupted. HOLD decisions are recorded too.

## Prompt improvement without strategy drift

The 14 base prompt templates and five adaptive reminders are English. `prompts/runtime_policy.md` provides
shared role boundaries and evidence handling. It adds no position cap, cash target or
compulsory investment action. `prompts/contract.json` records the policy version and
charter hash. `python prompt_eval.py` reports source hashes and runs deterministic
regressions; passing them is not proof of semantic correctness or investment quality.

The improvement loop is: recorded fault → two-auditor consensus → recurring pattern →
minimal insertion proposal → evaluation and owner review. The existing three-consensus
threshold remains. Proposals must describe a regression scenario and preserve legitimate
behavior. Explicit evidence-check bypasses and compulsory trade/position limits are rejected.

When Actions is allowed to create PRs, the proposal branch gets `System Checks` and
requires owner review. Otherwise `amend.py --export-only` publishes a `prompt-proposals`
artifact with the proposed diff and source hash (90-day retention). No charter or live
instruction is changed by exporting a proposal. Review packets are marked in the state
to avoid repeatedly proposing the same amendment. The repository currently uses this
artifact fallback. The permission to approve PRs was not enabled.

`System Checks` runs regression tests, the isolated detector → model adapter → executor →
report scenario, prompt evaluation and a dashboard build. Model responses in those tests
are fixtures; live provider checks are documented separately in `SYSTEM_TEST_REPORT.md`.
Failures are routed through the Telegram alert workflow. Its notification drill deliberately
fails **only the test workflow**, without modifying portfolio state.


### Bounded automatic prompt adaptation

`prompt_adapt.py` can select one of five versioned evidence reminders in
`prompts/adaptations.json`; it cannot generate free-form instructions, impose trades,
change portfolio weights or merge code. Activation requires three audit consensuses for
the matching pattern and at least 20 recorded model outcomes as a baseline. Only one
reminder is changed at a time. After 20 further outcomes, an error-rate increase of more
than 15 percentage points removes and quarantines the reminder. Rollback is persisted
immediately and raises a Telegram-notified workflow failure. Transport, JSON, numerical
gate and supported schema failures are monitored; this metric is not a measure of
investment profitability or a causal proof of prompt quality.

`state/prompt_metrics.json` and `state/prompt_adaptation.json` are populated by future
production runs. No reminder is activated until the evidence threshold is met. Novel
free-form rewrites remain review proposals; bounded automatic selection is separate.


## Validated weekly execution and independent recovery

`weekly_round.py` now receives a structured proposal instead of giving the model write
access to investment files. It checks measured closing prices, cash/shares, all A-F
sections, thesis coverage and condition schemas before saving a recoverable transaction.
Saturday stays active during exchange holidays; Sunday catch-up uses the same completed
session. A recorded weekly slot cannot execute again. The charter and strategy are unchanged.

`evidence.py` binds numeric prose to a company, metric, unit, observation time, source and
snapshot. References are rendered by code. Discretionary trade sizes and condition
thresholds remain model choices. Unknown references, raw numeric prose and invalid response
schemas trigger bounded retries, then rejection and the existing Telegram failure chain.
GitHub artifacts retain measurement/evidence packets for ninety days. This proves which
supplied field was cited; it does not prove provider accuracy or the semantics of every
surrounding sentence. Research opinions are not independent quantitative sources.

`watchdog.py` runs daily on GitHub Actions at 23:00 UTC (02:00 Europe/Istanbul), monitors missing/stuck jobs and requests
only bounded, idempotency-protected recovery. Repair requests, unresolved incidents and
verified recovery are reported to Telegram. It never rewrites strategy, disables a gate or
replays an execution/commit failure. See [installation and limits](ops/README.md).


## Data provider priority

FMP is the primary provider. `market_data.py` requests yfinance only after a primary
request fails, is empty/invalid, mismatches the issuer or returns stale price data.
There are no routine duplicate requests or provider averaging. Each symbol/dataset
selects one provider; a price-history series is replaced as a whole, never spliced.
This routing covers valuation, weekly history/fundamentals/earnings/news, intraday
measurement, exit-score prices and Scout market-pulse discovery.

NYSE-session, finite-value, timestamp and execution gates remain active on both paths.
Provider choice is recorded in source evidence and fills. Failover or unavailable data
is summarized to Telegram once per workflow and archived in `provider-routing` artifacts.
If both providers fail, missing prices cannot become trades. FMP-specific optional
insider/consensus/sector enrichment has no fabricated Yahoo equivalent: gaps remain
explicitly unavailable. A valid FMP fundamental snapshot does not trigger a second
provider merely for optional forward P/E; that field stays unknown when absent.

FMP endpoints: [daily prices](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full),
[earnings](https://site.financialmodelingprep.com/developer/docs/stable/earnings-company)
and the [API catalogue](https://site.financialmodelingprep.com/developer/docs).
