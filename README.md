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

The Saturday workflow combines four independently collected candidate channels:

- **Momentum:** Market gainers for emerging attention and trend research.
- **Dislocation:** Market losers for investigation of potential overreaction.
- **Structural universe:** A rotating US technology, industrial, energy and utilities company pool.
- **Insider purchases:** Reported open-market purchases from the latest insider feed.

The Scout selects 15–20 symbols from that measured universe; existing holdings are
retained. `state/discovery.json` records provider provenance and channel membership.
These are candidate signals: a decline does not establish undervaluation, and sector
membership does not prove a supply-chain bottleneck. Failed channels are explicit;
FMP is primary and yfinance is used only where a compatible backup is mapped.

Scout sends the current complete research pool to the AI Portföy Telegram channel on
its first run, then sends a new complete list with added/removed symbols only when
membership changes. Delivery state is stored in
`state/telegram_watchlist_state.json`; an unchanged pool produces no duplicate alert.

#### Cross-sector theme research inbox

After Scout updates the decision watchlist, a separate read-only radar scans recent
general news, daily industry performance, 20/60-session industry returns, and the
largest screened companies in leading US industries. A company qualifies only when
its 20- and 60-session total returns both exceed SPY and a cited news item is linked by
the theme review to its measured industry. News/article IDs and provider dates are
retained in `state/theme_research_inbox.json`; the weekly Telegram report also ranks
24 ETF theme proxies over 5 and 21 sessions and shows sampled FMP industry leaders.
Newly qualified names are shown separately. This inbox is not merged into
`state/watchlist.json` and does not issue trade decisions. Missing radar inputs send
a Telegram failure alert.

Industry performance and relative share-price strength are not direct fund-flow
measurements. The story-to-industry link is an AI annotation whose article and
industry IDs are checked against the supplied sources; this does not independently
prove the interpretation is correct. Uncited or out-of-universe links are discarded.
This is a discovery experiment, not a validated return edge.

News coverage records whether the provider excerpt or an independently fetched
article body was available. The reader tries a bounded set of public article pages;
paywalls and extraction failures remain explicitly excerpt-only. A separate supply-
chain research path requires a verbatim article quote and corroboration in a recent
issuer annual filing before admitting a product/component exposure candidate. It
keeps the official SEC filing link and does not modify the decision watchlist.

The Theme Tracker concept is now reproduced from dated provider data: a curated ETF
proxy board compares one-week and one-month total returns, while a separate dynamic
FMP-industry board ranks short-term movers. The supplied screenshot itself is not
ingested. Price movement is not fund flow; source coverage and integration limits
are documented in [`docs/theme_tracker_and_scout.md`](docs/theme_tracker_and_scout.md).

### 2. Specialist research — Multi-Agent Research Team (`weekly_data.py`)

Each analyst receives a separate, focused input dataset:

| Role | Inputs | Output |
|---|---|---|
| **Macro Strategist** | Available rates, yields and sector performance | Macroeconomic outlook |
| **Fundamental Analyst** | Up to eight dated quarters of income, balance-sheet and cash-flow data, valuation and insider evidence | Summary, bull case, bear case, invalidation and data gaps |
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

The Saturday model returns a **structured JSON research plan** without changing
holdings, cash, fills or live theses. The plan is queued in `state/weekly_plan.json`.
During an open NYSE session, refreshed research and prices are supplied for a new
decision; the model may revise or reject the weekend plan.

The session model returns a **structured JSON proposal**. Code validates the response schema,
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
pattern findings enter the consensus record. Unilateral objections remain visible in
`state/audit_disagreements.json` and are reported to Telegram without becoming automatic rule changes.

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
| **Weekly Round** | Saturday 06:00 UTC | Run discovery, research and audit using the last completed session; queue a plan without trading. |
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
access to investment files. It checks fresh session prices, cash/shares, all A-F
sections, thesis coverage and condition schemas before saving a recoverable transaction.
Saturday research stays active during exchange holidays; Sunday catch-up uses the same
completed session. Execution waits for an open NYSE session and a fresh decision. Quotes
are measured again after the model responds; session and freshness checks run before
committing. A recorded weekly slot cannot execute again. Weekly and intraday fills share
the same daily directional replay protection. The charter and strategy are unchanged.

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

## Research depth and prospective measurement

`fundamentals.py` collects quarterly statements with issuer, period, currency and
publication checks. FMP is primary; a failed dataset can fall back as a whole to
quarterly yfinance statements. Margins, year-over-year revenue growth and net debt
are derived in code and enter the typed evidence ledger. Unavailable comparable
quarters, publication timestamps, management guidance and filing footnotes remain
explicit gaps. This is not a full filing/transcript ingestion system.

`research_metrics.py` freezes selected research candidates, channel membership,
agent reports, decisions and benchmark entry quotes at session execution. Future
5- and 20-session split/dividend-adjusted research returns are compared with SPY and SMH (reinvestment assumption). Missing or unmatured
observations remain pending. Channel groups can overlap, and the sample covers the
selected research universe; it does not establish causal agent contribution or
predictive power. Existing historical returns are not retroactively reconstructed.
Results appear in `RESEARCH_PERFORMANCE.md` after cohorts become available.

Advisory position weights and downside scenarios accompany decisions and are stored
with each cohort. They introduce no allocation cap or compulsory trade. Performance
measurement remains separate from prompt output-error monitoring; neither mechanism
trains model weights or automatically rewrites the investment strategy.

Only new session fills use the revised execution policy. Earlier paper fills remain
unchanged. Commissions, spread and slippage are still unmodeled, so these records
should not be described as executable brokerage returns.

Financial-statement and discovery endpoints follow the [FMP API documentation](https://site.financialmodelingprep.com/developer/docs).

## Economic thesis monitoring and evidence review

New weekly theses must include an economic condition when measured fundamentals are
available: revenue growth, gross/operating margin, operating/free cash flow or debt.
The detector uses a freshly collected quarterly snapshot, explicit units and its
existing confirmation logic. Missing/stale evidence blocks reassessment for that
issuer; it never means the thesis passed. An assessed report is deduplicated until
its period, value or condition changes. Old thesis thresholds are not invented or
retroactively rewritten; migration happens at the next successful weekly decision.

News checks require provider article/excerpt text, publication date, issuer and URL.
Each assessment records exact source quotes, affected claim IDs, counterevidence and
uncertainty. Headline-only or partially missing packets stay pending and generate
assessment errors. These are provider excerpts, not independently scraped full text.

A separate model challenges factual and causal assertions before weekly proposals
or intraday thesis edits can pass. Unsupported/uncertain drafts leave existing text
unassessed and produce no associated decision. Attributed forecasts remain forecasts;
quoting an analyst does not establish their prediction as fact. The reviewer is still
a fallible model, not a proof engine. Its English prompt is included in `prompt_eval.py`.
`OPENROUTER_MODEL_REVIEW` selects it (default `openai/gpt-4o`). Review calls count toward
the claim budget; existing thesis-level emergency budget exceptions remain unchanged.
Evidence is retained in workflow artifacts and `state/violations.json` for intraday work.

## Corporate actions and return basis

Before scheduled analysis/trading, `corporate_actions.py` validates the active USD
issuer identity and reconciles FMP split/dividend events. The first successful run
establishes an explicit prospective boundary; no earlier entitlement is guessed.
Splits rescale shares, entry price, stop and price thresholds while preserving cost.
Dividends become non-spendable receivables on the ex-date and cash on the payment date,
including when the holding was sold after entitlement. Events/payment credits are
idempotent and share the atomic transaction journal with portfolio state.

Accounting changes are committed before Telegram notification or subsequent trades.
Missing providers, changed issuer identity, conflicting revisions or late events that
cross recorded trades stop the workflow and use the existing Telegram failure path.
Ticker renames, mergers, special distributions, cash-in-lieu, withholding and taxes
are not automatically inferred. FMP event data has no equivalent Yahoo payment-date
fallback: it fails closed. Ordinary historical return datasets do have a whole-packet
Yahoo fallback; FMP remains primary and the two are not fetched routinely together.

Research comparisons use dividend/split-adjusted series and a reinvestment assumption;
actual portfolio dividends remain cash/receivables. Benchmarks adopt this basis only
prospectively and retain earlier recorded history. The dashboard includes receivables
in equity, but they cannot finance purchases; adjusted benchmark comparisons are
available at the recorded close, not synthesized from unadjusted live quotes.
Costs/slippage and exceptional corporate events remain explicit limitations.

Endpoints and adjustment conventions follow the [FMP API catalogue](https://site.financialmodelingprep.com/developer/docs)
and [historical price API guide](https://site.financialmodelingprep.com/how-to/fmp-historical-price-apis-from-light-charts-to-dividendadjusted-analysis).
The separate, non-GitHub watchdog remains deferred at the owner's request.


## Decision lifecycle (29 September 2026)

Claim reassessment now escalates a newly invalid claim or multiple weakened claims to a
whole-position decision in the same run. Failed deep reviews remain pending for retry.
Legacy decisions request an initial monitoring review; the migration does not invent
financial thresholds or force trades. Both adverse and supportive news can open review.

Every production decision response must supply a complete claims/conditions replacement,
an executable falsifier reference, issuer-specific evidence IDs, an old/new explanation
and a future review deadline within one week. HOLD has the same requirements. Expiry
opens review even if no price threshold crossed. A non-HOLD proposal made outside a
session stays marked for fresh session reassessment; stale orders are never replayed.

Price relative to the current SMA50/SMA200 can be monitored as a percentage, avoiding
frozen moving-average price thresholds. Completed daily bars supply the averages.
Removing or changing existing conditions, or lowering an exit reference, requires
changed non-price evidence. The independent model reviews the proposed change against
the previous state; this remains fallible semantic judgement, not a truth guarantee.
HOLD can update its reviewed exit reference without creating a fictitious fill.

`state/decision_history.json` retains before/after decision snapshots. Weekly history is
written in the same atomic bundle as its portfolio/thesis update. Intraday history and
source artifacts retain the rationale, monitored conditions and review deadline.
Telegram includes the changed evidence, resulting decision, falsifier and next review.

Daily directional locks still apply to ordinary price/review events. A verified new
news/report event can reopen the same direction after another full decision review.
Code supplies event IDs; the model cannot authorize its own exception. Executed IDs are
retained in the fill ledger for crash recovery, including across dates. Exact repeated
news text is deduplicated across publication URLs and batch groupings; semantic
paraphrases are not guaranteed to be the same detected event. Session, freshness,
nonnegative cash and owned-share checks still apply. No condition mandates a trade.

Analyst target revision momentum is documented in
[docs/analyst_revision_design.md](docs/analyst_revision_design.md) as a research review channel.

### Analyst revision research

Analyst targets now form an additional **research and decision-review channel**. FMP
observations are collected daily and matched by firm across 7/30/90-day windows;
syndicated reports and repeated unchanged targets do not count as independent votes.
Two or more firms in the dominant 30-day revision direction can request reassessment,
with coverage checks and persistent event acknowledgement. This is a routing heuristic,
not a standalone buy/sell signal or an exception to trading/session safeguards.

Reviews separately examine **earnings, company news, sector/theme attention and valuation**.
Improving EPS is not a prerequisite. Analyst-stated reasons, contextual hypotheses and
unknowns have separate evidence statuses and source references. Missing estimate history
means unknown earnings support; it does not invalidate news or narrative evidence.

See [dated observations](ANALYST_REVISIONS.md) and the
[implementation/evaluation design](docs/analyst_revision_design.md). First snapshots are
recorded; prospective 20/60-session excess-return measurements remain pending until
mature. No predictive advantage or cost-adjusted profitability has been established.
