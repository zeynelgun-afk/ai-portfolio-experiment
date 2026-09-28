# AI Portfolio Experiment 🤖📈

**The hypothesis:** can a portfolio whose decisions are handed entirely to an AI — one that
must write down every move and own its consequences — beat the market over 12 months? What
is being measured is not compliance with rules, but what happens when free judgment is
combined with accountability.

- **Start:** 5 August 2026 · $100,000 (virtual — on paper, no real money)
- **Universe:** US large-cap technology plus semiconductor and AI infrastructure
- **Benchmarks:** SPY and SMH (each assumed bought with $100,000 on the same day)
- **Duration:** 12 months

## How it works

There are two kinds of decision round. **The weekly round builds the theses; the intraday
round keeps them alive during the week.**

**The weekly round** — every Saturday at 06:00 UTC, after the Friday close:

| Step | Who | What it does |
|---|---|---|
| 1. Measurement | `update.py` | Fetches prices, values the portfolio, computes the SPY/SMH comparison, flags exit levels → [REPORT.md](REPORT.md) · **makes no decisions** |
| 2. Decision | Claude (claude-code-action) | Analyses the data, writes a thesis, buys and sells, per [WEEKLY_INSTRUCTIONS.md](WEEKLY_INSTRUCTIONS.md) → [DECISION_LOG.md](DECISION_LOG.md) |
| 3. Thesis schema | Claude | Ties each thesis to measurable validity conditions → [theses.json](theses.json) |
| 4. Notification | Telegram + Issue | The weekly summary to Telegram; a ⚠️ Issue if a position closed below its exit level |
| Charter | [RULES.md](RULES.md) | Not a decision constraint; the principles of record honesty and measurement |

**The intraday round** — Mon-Fri 13:30-20:00 UTC, every 30 minutes. See
"Event-Driven Reassessment" below.

`update.py` in the weekly round never closes a position. It **flags** a position that
closed below its exit level; closing it, moving the level, or carrying it with a stated
reason is the AI's decision.

### Required secrets (Settings → Secrets → Actions)

- `OPENROUTER_API_KEY` — for the Claude decision round, via OpenRouter (without it the step
  is skipped and the experiment continues in mechanical mode)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — the weekly Telegram report (without them the
  step is skipped)
- `TELEGRAM_CHAT_ID_DM` — the intraday **thesis-level** notification (a personal DM, not
  the group). Without it only that step is skipped; the detector keeps measuring. Note that
  Telegram does not let a bot send the first message to a user, so the experiment's bot
  needs an open private chat with the recipient.

### Configurable variables (Settings → Variables → Actions)

| Variable | Default | What it does |
|---|---|---|
| `OPENROUTER_MODEL_FAST` | `anthropic/claude-haiku-4.5` | The fast model that rewrites a single claim |
| `OPENROUTER_MODEL_DEEP` | `anthropic/claude-opus-5.5` | The deep model that re-evaluates a whole thesis and produces the trade |
| `OPENROUTER_MODEL_AUDIT_A` | `anthropic/claude-opus-5.5` | Auditor A — same family as the decision-maker |
| `OPENROUTER_MODEL_AUDIT_B` | `openai/gpt-5.6-sol` | Auditor B — a different family, so the blind spots differ |
| `MAX_LLM_CALLS_PER_WEEK` | `60` | The weekly LLM call budget; once exceeded only `thesis`-level calls are made |
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | Point this at any OpenAI-compatible endpoint during an outage |

## Files

- `portfolio.json` — current positions, cash, trade history (the single source of truth)
- `DECISION_LOG.md` — every decision, dated and reasoned (`#N` weekly, `S#N` intraday)
- `theses.json` — each position's thesis, its claims and their **measurable validity conditions**
- `REPORT.md` — the latest automated status report
- `history.csv` — the weekly value series (portfolio vs SPY vs SMH)
- `update.py` — the weekly measurement script (yfinance, no API key needed)
- `detector.py` — the intraday change detector (deterministic, no LLM)
- `reassess.py` — the LLM layer that rewrites a triggered claim or thesis
- `number_audit.py` — the gate that checks the AI's figures against the data it was given
- `execute_trade.py` — the layer that executes an intraday decision deterministically
- `state/` — the detector's memory (hysteresis, cooldown, trade lock, pending notes)
- `audit.py` — the deterministic audit scorecard (no LLM) → `AUDIT.md`
- `reviewers.py` — two adversarial auditors, consensus only → `AUDIT_LOG.md`
- `amend.py` — opens a pull request proposing an instruction amendment for a recurring fault
- `tests/` — tests for the detector, the number gate, the execution layer and the audit
  (`python -m unittest discover -s tests -t .`)
- `dashboard/` — the Thesis Watch live monitoring page (template + `build.py`)

## Event-Driven Reassessment

**The problem it solves:** the commentary written in the Saturday round went stale during
the week. When the price slipped below the 50-day average on a Monday, the file still read
*"+14.9% above the average"*. A system that thinks once a week is not wrong once a week —
it is wrong for six days.

**The principle:** *data flows continuously, commentary is updated only when the meaning
changes.* Asking an LLM "what is the situation?" every 30 minutes would be both expensive
and noisy; instead, deterministic Python answers "did the meaning change?", and the LLM is
only called once a threshold is crossed.

### The chain

```
detector.py          measure the conditions in theses.json (NO LLM)
   │                 exit code: 0 = nothing changed
   ├── code 10 ────▶ reassess.py — that claim only, fast model
   └── code 20 ────▶ reassess.py — the whole thesis, deep model + a decision
                          └──▶ execute_trade.py — execute it deterministically
                                   └──▶ portfolio.json + DECISION_LOG.md (S#N)
```

### Severity levels

Every condition in `theses.json` carries a severity — how badly it shakes a thesis:

| Severity | Meaning | Exit code | What happens |
|---|---|---|---|
| `warning` | A flag only | 0 | Recorded; appears in the 21:15 summary. The commentary does not change. |
| `claim` | One claim was shaken | 10 | Only that claim is rewritten by the fast model. No trade. |
| `thesis` | The thesis is in question | 20 | The deep model re-evaluates the whole position and **may trade**. |

### Anti-flapping

So that a price oscillating around a threshold does not produce a constant signal, three
layers:

1. **Hysteresis** — a condition counts as breached only after **2 consecutive checks**. If
   the price deviates more than 25% from the previous close (possibly a corrupt data bar),
   3 checks are required.
2. **Recovery band** — 1% of the threshold. A drop below 850 triggers; clearing it takes a
   move back above 858.5.
3. **Cooldown** — the same claim is not rewritten twice within 4 hours.

### The number gate

`WEEKLY_INSTRUCTIONS.md` has always said "never write a number without a source", and
round #7 broke exactly that rule — an "~80-90% market share" figure was written into the
NVDA thesis from memory. The instructions themselves prescribe the remedy: **"If writing a
rule down is not enough, the rule gets turned into data."** A prompt is not a firewall.

`number_audit.py` requires every figure in the AI's commentary to appear in the data block
or be derivable from it. If the model insists on an unsourced figure after being told which
one it is, the claim is **left unchanged**. Two distinctions keep the gate honest:

- **Decision parameters are not audited.** A new stop level or a share count is the
  decision itself, not a claim about the market; those are validated by
  `execute_trade.py`'s arithmetic. Conflating the two left the model unable to decide
  anything.
- **Indicator parameters are free.** "50d average", "RSI(14)", "20-day volume" are terms,
  not assertions.

### The full review (unknown unknowns)

Something we never tied to a threshold may have broken. Once a day, after the US close
(**21:15 UTC**), every claim is revisited in bulk by the fast model even when no threshold
was crossed. Once the weekly budget (`MAX_LLM_CALLS_PER_WEEK`, default 60) is exceeded only
`thesis`-level calls are made — a thesis-level trigger means an entire thesis is collapsing
and is not sacrificed to a budget.

### Intraday trading — why the LLM does not write to portfolio.json

The decision belongs to the AI (charter version 2), but **executing it is arithmetic.**
`execute_trade.py` carries out the decision as given, after validating that:

- **The price is not taken from the LLM.** The fill price is the intraday bar measured by
  the detector.
- No trade happens if the price source is not live (if it fell back to the daily close).
- No trade happens when the market is closed; the decision carries to the Saturday round
  with its reasoning.
- Cash cannot go negative and more shares than are held cannot be sold.
- The same direction is not traded twice in one day (`state/trade_lock.json`).

None of these says *"this decision is wrong"* — only *"this trade cannot be done with
these numbers"*. **A decision that was not executed is written to the log with its reason
too**; nothing fails silently.

Before any mutation, `portfolio.json` is snapshotted and written atomically, so
`python execute_trade.py --rollback` restores the pre-trade state. The `DECISION_LOG.md`
entry is never removed — the record of a decision is not erased.

### Notification

- **`thesis` level / a trade** → Zeynel's DM immediately (`TELEGRAM_CHAT_ID_DM`), falling
  back to the group channel if the DM cannot be reached, and the step goes red if neither
  holds.
- **`claim` level** → no immediate notification; it goes out in bulk in the 21:15 full
  review summary.

### Thesis Watch — the live monitoring page

The dashboard under `dashboard/` shows the same split on screen: **measurement is
deterministic, commentary is generative.**

- **The measurement** arrives live from the viewer's own FMP connector (price, daily change,
  50d/200d averages, the sector ETF). The threshold comparison happens in the browser,
  using the same logic as `detector.py`.
- **The commentary is not baked into the page.** A "what is this claim's status right now?"
  button sends the question to the agent together with the live measurements; the answer is
  generated fresh each time. There is a free-form question console at the bottom.
- **An unmeasurable condition says `unmeasurable`.** The live connector does not provide a
  20-day average volume, so the `volume_ratio_20d` condition is not measured on the page —
  it is not guessed.
- **There is no hysteresis or cooldown on the page**; that memory lives in
  `state/violations.json`. The page shows a single instantaneous measurement, and the page
  never trades.

Because the theses change every Saturday, the page is rebuilt and republished:

```bash
python dashboard/build.py   # theses.json + portfolio.json → dashboard/thesis-watch.html
```

Then republish to the same artifact URL from a Claude session. The template
(`dashboard/thesis-watch.template.html`) is what you edit; the generated HTML is not — a
hand-edited one-off page would be stale commentary by the second round, which is the very
problem the page exists to solve.

## The audit layer

The experiment's weakest link was never the decisions — it was that the weekly human audit
it depends on was not happening. An audit that does not happen is not a safeguard, so the
parts of it that can be computed are computed, and the part that cannot is put to two
independent auditors who have to agree.

**`audit.py` — the deterministic scorecard (no LLM).** Everything on it is derived from
the repository's own record:

- **Label against action** — a thesis marked BROKEN while the position is held is a rule
  violation the instructions forbid. It is now checked rather than trusted. (Running it
  over the existing record found one, in round #6.)
- **Exits scored against what happened next** — the one thing the decision-maker could not
  know at the time. SNDK, sold at 1212 $ and 46.7% higher a month later, becomes this
  number rather than a paragraph of regret.
- **Threshold quality** — from `state/triggers.jsonl`, a permanent append-only log. A
  condition firing on most checks measures noise; a `thesis`-level condition that has never
  fired was tied to a number that cannot happen.
- **Decision cadence** — weekly trades against intraday trades, the question charter
  version 3 added.
- **Commentary health** — claims stuck on `unassessed` mean the LLM layer is rejecting its
  own output and nobody noticed.

**`reviewers.py` — two auditors, two model families, consensus only.** An auditor reading
the same data as the decision-maker produces a correlated second guess, and an auditor from
the same model family shares its blind spots. So the auditors are fed the scorecard first —
they argue from what happened — and **a finding is recorded only when both report the same
pattern.** Findings use a closed taxonomy, because free text cannot be matched across two
models and the second auditor would be decoration.

The auditors judge reasoning, never outcomes, and may not propose trades: an auditor that
starts trading has stopped auditing. When the same pattern survives consensus three times it
stops being an incident and becomes a gap in the instructions — the audit says so and the
owner decides, exactly as charter rule 4 requires. It proposes; it never applies.

**`amend.py` — the loop closes.** `WEEKLY_INSTRUCTIONS.md`'s version history is a list of
moments where a human noticed a failure pattern and turned it into a rule; versions 6, 7
and 8 all came from that, and nobody was doing it any more. So when a pattern survives
consensus three times, `amend.py` writes a proposed amendment and **opens a pull request**.

Three guarantees make "it proposes, it never applies" real, and all three are enforced in
code rather than requested in a prompt:

1. **Only `WEEKLY_INSTRUCTIONS.md`** — not the charter, not the code, not the portfolio or
   the theses. A process that can rewrite the charter or the executor is not proposing, it
   is governing.
2. **Insertion only.** Removing a constraint is the one edit that can make the system less
   safe, and it is exactly the edit an AI under audit has an interest in making. The
   validator re-derives the original file from the amended one and rejects anything that
   is not a pure addition.
3. **A branch and a pull request, never a merge and never the default branch.** One
   proposal per pattern: re-proposing the same amendment every week would train the owner
   to close the tab, which is the same failure as an audit nobody reads.

The amendment prompt is told to prefer a rule that becomes *checkable* — a required line, a
number that must be written — over one that restates the prohibition more loudly, because
restating it more loudly is what already failed.

The audit runs in the weekly workflow **before** the decision round, so the AI walks in with
its own failure patterns in front of it rather than discovering them a week later; the
amendment step runs after the push, so its branch is cut from the updated default branch.

### Running it by hand

```bash
python detector.py --dry-run                      # measures, writes nothing
python detector.py --fixed-data tests/sample.json # no network, fixture data
python reassess.py --code 10 --dry-run            # no LLM call; prints the prompt
python execute_trade.py --dry-run                 # says what it would do, does nothing
python execute_trade.py --rollback                # restore the pre-trade snapshot
python audit.py                                   # the deterministic scorecard
python audit.py --review                          # + the two adversarial auditors
python reviewers.py --dry-run                     # print both auditor prompts, no calls
python amend.py --dry-run                         # show what would be proposed, touch nothing
python -m unittest discover -s tests -t .         # 178 tests
python dashboard/build.py                         # rebuild the live dashboard
```

Actions → **Intraday Detector** → Run workflow also runs it manually (the `full_review`
checkbox revisits every claim).

> ⚠️ This is an experiment, not investment advice.


## Failure monitoring

`Telegram Failure Alert` watches failures of the weekly round, intraday detector,
dashboard deployment and manual Telegram report. It sends the failed step names and
run URL to the group, retries delivery and falls back to `TELEGRAM_CHAT_ID_DM`.
Both destinations failing makes the alert workflow fail as well. Its manual dispatch
sends an explicitly labelled test notification and does not run portfolio decisions.

The detector requires `FMP_API_KEY` and `OPENROUTER_API_KEY` in Actions secrets.
`OPENROUTER_MODEL_NEWS` overrides the news model; otherwise it uses
`OPENROUTER_MODEL_FAST` or the existing Haiku default. Unavailable or ambiguous news
assessments remain pending for retry. Valid price-triggered decisions can complete,
then the news-health step marks the run failed so an alert is sent. News fetch errors,
audit errors, unusable auditor responses and Scout errors also fail visibly.
`--dry-run` does not call the news model. Failed workflows do not silently roll back
already recorded decisions; inspect the linked run and decision log before retrying.
