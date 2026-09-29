# AI Portfolio Experiment — Charter

**Start:** 5 August 2026 · **Virtual capital:** $100,000 · **Duration:** 12 months (target end: 5 August 2027)

> **Version 4 — 28 September 2026.** The whole system moved to English when the repository
> went public. Nothing about the rules changed; only the language and the file names did.
> `DENEY_KURALLARI.md` is now `RULES.md`, `HAFTALIK_TALIMAT.md` is
> `WEEKLY_INSTRUCTIONS.md`, `KARAR_GUNLUGU.md` is `DECISION_LOG.md`, and the schema keys
> in `portfolio.json` / `theses.json` are English. The historical entries in the decision
> log were translated at the owner's explicit instruction; the original Turkish text
> remains in the git history.
>
> **Version 3 — 27 September 2026.** The decision cadence moved from weekly to
> event-driven. The only decision moment used to be the Saturday round, and the commentary
> written there went stale during the week: for a price that had slipped below the 50-day
> average on a Monday, the file still read "+14.9% above the average". Now `detector.py`
> measures the thesis validity conditions every 30 minutes during the session, and if a
> threshold is crossed the AI decides the same day — including executing a trade. The
> owner's decision: fully autonomous, no approval gate. The reasoning and the schema are
> in the README's "Event-Driven Reassessment" section.
>
> **Version 2 — 8 August 2026.** The charter was simplified: the detailed decision rules
> were removed and the decision was handed entirely to the AI. For the reasoning and the
> previous version, see the audit record in DECISION_LOG.md.

## Hypothesis

The AI makes the decisions. The constraint is not the number of rules; it is that every
decision carries a **written rationale** and a measurable outcome.

The question being measured: *can an AI that has been set free but must write down every
move and own its consequences beat the market over 12 months?*

**The owner's goal:** 3-5x in one year. **The AI's note on the record:** that goal is
statistically extreme; playing for it means accepting high concentration and 30-50%
drawdowns along the way. The experiment measures that tension too. A realistic bar for
success: beating the S&P 500 by a clear margin over 12 months.

## Universe

US large-cap technology plus semiconductor and AI infrastructure. Spot equities only; no
leverage and no options. (This is not a strategy constraint — it exists so the benchmark
comparison stays meaningful.)

## Decision authority — entirely the AI's

All of the following are at the AI's discretion. There is no upper bound, no lower bound
and no mandatory threshold:

- The number of positions, the weight in any single name, the cash ratio
- Entry and exit timing; adding, trimming, taking profit
- Stop and exit levels, and when to move them
- Carrying a position into or out of an earnings report
- How concentrated to be, how long to wait
- **When a decision is made.** The decision moment is not limited to the Saturday round;
  a decision can be made and executed intraday during the week (see "Decision moments"
  below).

One condition takes the place of the rules: **the rationale is written down.**
Doing nothing is also a decision, and it is written down too.

## Decision lifecycle — owner-authorized 29 September 2026

A newly invalid claim or multiple weakened claims opens whole-position review.
Each new decision carries executable falsifier conditions and a review deadline of at
most one week; expiry requests fresh review, not a forced trade. Thesis text and monitors
are versioned together. Both supportive and adverse evidence can request review.
Moving-average conditions use measured current averages. Changing/removing old thresholds
requires changed non-price evidence and an explicit explanation; a falling price alone
cannot excuse moving the threshold. Decision history retains the previous and new states.

## Decision moments

There are two kinds of decision round, and both carry the same obligation to account for
themselves.

1. **The weekly research round** — Saturday 06:00 UTC. A full research plan using
   the `WEEKLY_INSTRUCTIONS.md` template is queued without changing holdings or live
   theses. In the next eligible NYSE session it is reassessed with fresh inputs; only
   then may validated orders update the portfolio and `theses.json`.
2. **The intraday round** — Mon-Fri 13:30-20:00 UTC, every 30 minutes. An automated
   detector (`detector.py`) measures the validity conditions in `theses.json`
   deterministically. If a threshold is crossed, the AI either rewrites only the affected
   claim (`claim` level) or re-evaluates the position's whole thesis and **executes a
   trade** (`thesis` level).

**The limits on the intraday round — not strategy constraints, but measurement and data
integrity constraints:**

- **The price is not taken from the AI.** The fill price is the intraday bar measured by
  the detector. A number in the AI's sentence never becomes a trade.
- **No threshold produces a decision until it is confirmed on two consecutive checks**
  (three if the price deviates more than 25% from the previous close). A corrupt data bar
  is filtered out at the cost of one cycle; a genuine crash is still caught within 60
  minutes.
- **The arithmetic is validated:** cash cannot go negative, more shares than are held
  cannot be sold, and repeated execution of the same material event is forbidden. The same-direction
  daily lock remains the default; a separately verified new news/report event may reopen
  a decision after fresh review, with event identities recorded in the fill ledger. These do not
  judge the decision; they only say "this trade cannot be done with these numbers".
- **Numbers are audited.** Every figure in the AI's commentary must appear in the data it
  was given or be derivable from it (`number_audit.py`). A figure written from memory is
  not a style problem, it is a break in the record.
- **No trade when the market is closed**; the decision is recorded with its reasoning and
  carries to the Saturday round.
- **Every intraday decision is written to the log** (an `S#N` entry), including the ones
  that were not executed.

## Invariant principles

These are not strategy constraints; they are what keeps the experiment measurable and
honest.

1. **Every decision goes into the log:** the thesis, the entry, the exit plan, and *the
   signal that would show the thesis is wrong* (what would make me change my mind). Since
   version 3 that signal is also written into `theses.json` as a **measurable condition** —
   if the way a thesis can be refuted lives only in prose, nobody can check it during the
   week.
2. **Changing your mind is allowed; changing it silently is not.** If you are departing
   from what you said in the previous round, say so explicitly. What is being audited is
   not accuracy but accountability.
3. **Numbers are never invented.** Prices, ratios and fundamentals are written only from a
   tool, with their date. If it cannot be fetched, it is not written — the thesis is
   stated without numbers.
4. **The AI may not change this file or `WEEKLY_INSTRUCTIONS.md`.** It proposes changes;
   the owner rules on them during the audit.
5. **No retroactive correction.** New fills are recorded only during an open NYSE session at measured session prices.
   Saturday research is queued and reconsidered in-session before execution. Slippage
   and commission remain unmodeled (this is a paper experiment). A thesis, once written, is not
   prettied up afterwards.
6. This experiment is not investment advice and must not be copied one-for-one with real
   money.

## Measurement

- **Benchmarks:** SPY (S&P 500) and SMH (the semiconductor index), each assumed to have
  been bought with $100,000 on the same date. The reference prices are recorded in
  `portfolio.json`.
- **Quantitative:** total return, maximum drawdown (weekly basis), hit rate, number of
  trades. Since version 3 the trade count can be read separately for the weekly and the
  intraday rounds: intraday trades are tagged `"source": "intraday_autonomous"` in
  `trade_history`. A new question to measure: *is the intraday decision more accurate than
  the weekly one?*
- **Qualitative:** the quality of the reasoning — looking back, did the thesis hold, and if
  it did not, did the AI admit it or bend the rationale to fit the outcome?
- Every decision lives in `DECISION_LOG.md`; the portfolio state lives in
  `portfolio.json`.
