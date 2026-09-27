# Decision Log — AI Portfolio Experiment

Every entry: the date, the decision, the thesis, the risks, the stop, the review trigger.

**There are two record types:**

- `## #N — <date> · WEEKLY ROUND` — the Saturday 06:00 UTC decision round. A full record
  (sections A-F, the `WEEKLY_INSTRUCTIONS.md` template). This is the round that builds the
  theses.
- `## S#N — <date> <time> UTC · INTRADAY DECISION` — an event-driven round during the week.
  When `detector.py` measures that a thesis validity condition's threshold has been crossed
  (confirmed on 2 consecutive checks), the deep model re-evaluates the position's thesis; the
  decision is executed deterministically by `execute_trade.py`. A short record: the trigger,
  the fill, the thesis assessment, the reasoning, the falsifier. Decisions that were not
  executed are written here with their reason too — nothing fails silently.

Intraday decisions are numbered separately with an `S#` prefix; the weekly round numbering
(`#N`) is unaffected. Every intraday trade appears in `portfolio.json` → `trade_history`
tagged `"source": "intraday_autonomous"`.

> **Language note (28 September 2026).** The repository went public and the whole system
> moved to English. Entries #1-#10 were originally written in Turkish and were translated at
> the owner's explicit instruction; the original text remains in the git history. The charter
> rule "no retroactive correction" still stands — nothing was reasoned differently, only
> restated in another language.

---

## #1 — 2026-08-05 · INITIAL PORTFOLIO SETUP

**Market context:** the AI infrastructure rally continues; semiconductors took a sharp
correction at the end of July and yesterday (4 Aug) was a strong bounce day (+6-13% moves
across an SMH-like basket). The S&P 500 set a new record. The memory super-cycle
(HBM/DRAM/NAND) is the hottest front in the theme.

**Screening result (14 candidates):** ORCL and SMCI were eliminated (price below both the 50-
and 200-day averages, trend broken). PLTR was eliminated (+29.5% yesterday — the no-chasing
rule). MSFT/GOOGL/NVDA were eliminated (high quality but not enough beta for a 3-5x target;
NVDA can be reconsidered later). TSM/MRVL/VRT are on the watchlist (below the 50-day average,
awaiting confirmation of a turn).

### BUY: MU — 30% (30,000 $, 33.6072 shares @ 892.67 $)
**Thesis:** the principal player in the memory super-cycle. Latest quarter: revenue 41.5 bn $
(+345% year over year), gross margin 84.6%, EPS 25.04 $. TTM P/E ~20, forward P/E ~5-6.
Analyst consensus Buy (57 buy / 11 hold), median target 1,512 $. Technically: 29% off its high,
the 738-770 $ support held twice, RSI 48. A strong trend inside a correction — the asymmetry
favours us.
**Risk:** if the cycle turns, margins collapse (declines of 60-70% have happened historically).
SK Hynix HBM competition. Weekly swings of ±20% are normal.
**Stop:** weekly close < 730 $. **Trigger:** the 22 September earnings report — review before it.

### BUY: AMD — 20% (20,000 $, 38.5668 shares @ 518.58 $)
**Thesis:** the only real alternative to NVDA in the AI accelerator market; momentum in the MI
series. Technically the healthiest picture: price > 50d (513) > 200d (313), 11% from its high.
Joined the bounce yesterday with +7%.
**Risk:** competitive pressure from NVDA; a high expectations multiple.
**Stop:** weekly close < 440 $.

### BUY: SNDK — 15% (15,000 $, 10.507 shares @ 1,427.62 $)
**Thesis:** the pure play on the AI storage / NAND front; the portfolio's highest risk-reward
leg. 39% off its high, with a +10.8% reversal signal yesterday; the 200-day average (849) is
far below — the primary trend is intact. A range of 40 $ → 2,354 $ within the year is evidence
of the strength (and the volatility).
**Risk:** NAND is far more cyclical than HBM; the correction could deepen. That is why this
has the widest stop.
**Stop:** weekly close < 1,100 $.

### BUY: ANET — 15% (15,000 $, 78.736 shares @ 190.51 $)
**Thesis:** the leader in AI data-center network hardware; the stock BROKE its 52-week high
yesterday (190.5 > the previous high) — a momentum entry. Price > 50d (167) > 200d (146).
**Risk:** the breakout could prove false (a bull trap).
**Stop:** weekly close < 160 $.

### BUY: AVGO — 10% (10,000 $, 23.9143 shares @ 418.16 $)
**Thesis:** custom AI chips (XPU) plus networking; the portfolio's "ballast" leg. Price > 50d >
200d, 16% from its high.
**Risk:** low beta — its contribution to a 3-5x target is limited; its role is to soften
declines.
**Stop:** weekly close < 350 $.

### CASH — 10% (10,000 $)
Dry powder for a sharp correction. MRVL/TSM/VRT become candidates if they confirm a turn.

**The portfolio's character:** 90% invested, 5 positions, all of them in the AI infrastructure
theme — deliberate concentration. This portfolio's one large risk is the theme itself: if the
AI spending cycle breaks, all of them fall together. That is the price of an aggressive target.

**Next review:** ~12 August 2026 (weekly) or whenever the owner asks.

---

## #2 — 2026-08-05 · WEEKLY ROUND (FIRST-DAY CHECK)

**Market context:** the portfolio was set up yesterday (5 August). The data is based on the 4
August close; the market is not open yet (06:29 UTC). AMD's and ANET's earnings came out
yesterday, SNDK's are today.

**Technical position — current holdings:**
- **MU (892.67 $):** price < SMA50 (969) but >> SMA200 (525), RSI 49. 1mo -9.4%, 3mo +72.6%.
  Stop 730 $ (+22.3% away). Earnings 23 September. Safe zone.
- **AMD (518.58 $):** price > SMA50 (514) >> SMA200 (315), RSI 48. 1mo -6.1%, 3mo +46.3%.
  Stop 440 $ (+17.9% away). Earnings yesterday (4 Aug). Safe zone.
- **SNDK (1427.62 $):** price < SMA50 (1705) >> SMA200 (855), RSI 44. 1mo -18.2%, 3mo +30.2%.
  Stop 1100 $ (+29.8% away). Earnings TODAY (5 Aug) — the result is not known yet. Safe zone.
- **ANET (190.51 $):** price >> SMA50 (168) >> SMA200 (146), RSI 65. 1mo +9.9%, 3mo +10.3%.
  Stop 160 $ (+19.1% away). Earnings yesterday (4 Aug). The strongest picture.
- **AVGO (418.16 $):** price > SMA50 (395) > SMA200 (365), RSI 59. 1mo +11.8%, 3mo +0.3%.
  Stop 350 $ (+19.5% away). Earnings 2 September. Healthy momentum.

**Watchlist notes:**
- **NVDA (211.94 $):** price > 50d > 200d, RSI 50, 1mo +8.4%. A healthy trend — could be
  considered in later rounds for higher beta.
- **MSFT (492.81 $):** RSI 81 (OVERBOUGHT), 1mo +27.4%. Dangerous territory — no entry.
- **PLTR (162.66 $):** RSI 69 (close to overbought), 1mo +22.7%. Aggressive momentum but far
  too hot.
- **TSM/MRVL:** below the SMA50, awaiting confirmation of a turn (as stated in the initial plan).
- **VRT (269.93 $):** RSI 39, 3mo -17.8%. Weak — could be dropped from the watchlist.

**Stop check:** no position is near its stop level. The tightest distance is AMD's at +17.9%
(stop 440 $, price 518.58 $). Every position is in the safe zone.

### DECISION: NO TRADES

**Reasoning:**
1. The portfolio was only just set up (< 24 hours). Far too early for the weekly check cycle;
   discipline requires seeing at least a week of how the positions develop.
2. SNDK's earnings are today but the results have not been released. Trading before seeing the
   market's reaction means acting on an assumption (contrary to the charter).
3. AMD's and ANET's earnings are known to have been yesterday, but the market is not open yet;
   the price effect will be watched in today's session.
4. No stop breaches, and no position requires urgent intervention.
5. Cash is 10% (10,000 $) — enough powder for an opportunity, no need to rush.

**Risk note:** SNDK's earnings are today — expect volatility. The position is 15% of the
portfolio and the stop is +29.8% away; even if the report disappoints, that stop distance
absorbs an uncomfortable decline. The earnings impact should still be assessed at the next
check (on a weekly basis).

**Watchlist action:**
- **VRT:** 3-month return is negative, RSI weak. A decision to drop it could be taken next round.
- **NVDA:** a candidate to add for higher beta at the next check (if cash allows).

**Next review:** 12 August 2026 (a full weekly round) plus an assessment of the SNDK/AMD/ANET
earnings impacts.

---

## #3 — 2026-08-08 · WEEKLY ROUND

**Market context:** three days of consolidation in the AI infrastructure theme. The portfolio
lost 4.04% (4.3% behind SPY, 5.3% behind SMH). Semiconductors are weak and the correction in
the memory super-cycle theme is deepening. Macro: uncertainty is high and sector volatility
continues.

**Technical position — current holdings (7 August close):**

- **MU (892.67 → 877.57, -1.7%):** price < 50d (971), no 200d available, RSI 50.9 (neutral).
  1mo -10.4%, 3mo +17.5%. Stop 730 (+20.2% away). Earnings 23 September. The trend is weakening
  but the stop is safe. The weekly 50d support broke — momentum is losing strength.

- **AMD (518.58 → 483.36, -6.8%):** price < 50d (514), RSI 46.9. 1mo -13.4%, 3mo +6.2%.
  Stop 440 (+9.9% away) — **THE TIGHTEST STOP DISTANCE**. Earnings 3 November. The 50d support
  broke slightly; the next weekly close is critical (Friday 11 Aug). The risk of a stop breach
  is rising.

- **SNDK (1427.62 → 1212.21, -15.1%):** price << 50d (1688, 28% below it), RSI 44.3 (weak).
  1mo **-36.7%**, 3mo -22.4% — **THE PORTFOLIO'S WORST PERFORMANCE**. Stop 1100 (+10.2% away).
  Earnings 6 November. Momentum is entirely broken; it has lost the 50d level completely. The
  NAND cycle is far more volatile than HBM and the correction may keep deepening. The stop
  distance is tight; waiting another week could carry the losses down to the stop level.

- **ANET (190.51 → 188.67, -1.0%):** price > 50d (171), no 200d available, RSI 63.1 (strong).
  1mo +0.9%, 3mo +33.1%. Stop 160 (+17.9% away). Earnings 3 November. **THE PORTFOLIO'S
  STRONGEST TECHNICAL PICTURE** — it is holding the 50d support and momentum is solid.

- **AVGO (418.16 → 427.76, +2.3%):** price > 50d (395), no 200d available, RSI **73.6
  (OVERBOUGHT)**. 1mo +6.9%, 3mo -0.4%. Stop 350 (+22.2% away). Earnings 2 September (25 days
  out). **THE ONLY WINNING POSITION**, but RSI is in overbought territory; there is short-term
  pullback risk.

**Stop check:** no position has breached its stop yet. The riskiest: AMD (+9.9%) and SNDK
(+10.2%). AMD's close this Friday (11 August) is the critical level — below 440 $ the position
is CLOSED per the charter.

**Watchlist highlights:**
- **NVDA (223.96):** 50d (206) below the price, RSI 65.6. 1mo +6.2%, strong momentum. Earnings
  26 August (18 days out — right at the edge of the earnings rule). Worth considering but not
  urgent.
- **PLTR (172.01):** price >> 50d (133), RSI 70, 1mo +35.7%. FAR TOO HOT — the no-chasing rule
  applies.
- **MSFT (499.99):** RSI **81.4 (VERY OVERBOUGHT)**, 1mo +29.8%. Dangerous, no entry.
- **TSM (420.04):** around the 50d (426), RSI 57.2. Awaiting confirmation of a turn (stated in
  the earlier plan).
- **VRT (272.40):** below the 50d (301), RSI 44, 1- and 3-month returns negative. A weak trend —
  could be dropped from the watchlist.

### DECISION 1: SELL — SNDK (a proactive loss cut)

**Trade:** 10.507 shares of SNDK @ 1,212.21 $ → **+12,737 $ cash**

**Thesis (closing):** SNDK's entry thesis is broken. Even if the "AI storage / NAND front" theme
persists, it has become plain that the NAND cycle is far more volatile than HBM and that the
correction can keep deepening. Down 15% in three days; down 36.7% over the last month — the
portfolio's worst performance. The price is 28% below the 50d; momentum is thoroughly broken and
there is no reversal signal (RSI 44, weak). The 1,100 $ stop has not been breached yet, but the
distance is only +10.2% — another week of decline triggers the stop and the loss grows further
(it would become -23%).

**The risk-management principle:** stop discipline says "close it if the weekly close breaches
the level", but that does not prevent a **proactive exit** when the thesis itself breaks. SNDK's
thesis is plainly broken; waiting for the stop breach mechanically enlarges the loss. Freeing up
cash for stronger opportunities is the disciplined move. That an aggressive target (3-5x)
requires sound risk management was stated at the initial portfolio setup — this is the first
application of that discipline.

**Loss:** -2,263 $ (-15.1%). **New portfolio weights:** MU 30.7%, AMD 19.4%, ANET 15.5%,
AVGO 10.7%, CASH 22.7% (22,737 $).

**Risks:** if SNDK turns from here (say NAND demand explodes) we will have sold early. But the
current technicals and momentum show no reversal signal whatsoever; the most likely scenario is
a continued decline. Limiting the loss takes priority over catching a better asymmetry.

### DECISION 2: HOLD — MU, AMD, ANET, AVGO

**MU:** the trend weakened (below the 50d) but the stop distance (+20.2%) is comfortable. Watch
the price action into the 23 September earnings; hold unless the stop is breached. The thesis
still holds (the memory super-cycle); only the timing may have been early.

**AMD:** **A CRITICAL LEVEL** — stop 440 $, distance +9.9%. If this Friday's close (11 August)
is below 440 it **WILL BE CLOSED** (per the charter). If it stays above 440, hold; the AI
accelerator thesis is intact, this is just sector consolidation. Whether the stop was breached
will be assessed at the next check (12 August or early in the week).

**ANET:** the portfolio's healthiest position. Holding the 50d support, momentum strong (RSI
63). Showing strength with a minimal loss (-1%). Hold.

**AVGO:** RSI 73.6 is in overbought territory and earnings are 25 days out. There is pullback
risk but no stop danger yet (+22.2% away) and the thesis is not broken (custom AI chips plus
networking). The charter says "part of the cost may be taken out of a position that has
doubled" — AVGO is only +2.3% and has not doubled. Realising profit is discretionary; **hold**
for now and reassess before the earnings report (end of August).

### DECISION 3: NO NEW POSITIONS

**Cash:** 22,737 $ (22.7% of the portfolio). The charter allows 0-30% cash — the current level
is near the edge but permitted.

**Why no new positions?**
1. **NVDA:** strong (price > 50d, RSI 65.6, 1mo +6.2%) but earnings are on 26 August (18 days
   out). The charter: "no new full position is opened with less than a week to earnings" — so no
   entry after 19 August. An entry is possible now, but there is no hurry; clarifying the stop
   situation of the existing positions (AMD) first is the more disciplined order.

2. **PLTR:** FAR TOO HOT (RSI 70, 1mo +35.7%). The no-chasing rule still applies.

3. **MSFT:** overbought (RSI 81.4). A pullback should be waited for.

4. **TSM/MRVL:** at or below the 50d, awaiting confirmation of a turn. No clear signal yet.

5. **VRT:** weak momentum (1- and 3-month negative). Could be dropped from the watchlist.

**Strategy:** the cash is kept as powder. After AMD's Friday stop check (11 August) the picture
will be clearer. If AMD is closed, cash rises to ~42%; if it holds, the current 22.7% cash waits
for a firmer entry opportunity (a turn in TSM, a pullback in NVDA, or a fresh screen). Disciplined
waiting rather than rushing.

### PORTFOLIO CHARACTER (after SNDK)

**Positions:** 4 names (MU, AMD, ANET, AVGO) — all in the AI infrastructure theme.
**Cash:** 22.7% (22,737 $)
**Risk profile:** cutting SNDK removed the most volatile leg; the portfolio is slightly more
balanced but still aggressive (the theme concentration remains). AMD's stop risk is the biggest
uncertainty.

**Performance (since inception):** -4.04% (including the SNDK loss). 4.3% behind SPY, 5.3%
behind SMH. A poor start, but only three days have passed — this is the period in which
long-term discipline gets tested.

**The biggest lessons so far:**
1. NAND is far more volatile than HBM — it turned out that even SNDK's stop distance (about 30%)
   was not enough.
2. Entries on the "bounce day" after a correction (5 August) may have been early — the
   consolidation continued.
3. Rather than waiting for stop discipline to fire, **a proactive exit when the thesis breaks**
   is also part of the discipline.

**Next review:** Friday 11 August (AMD's stop check — critical) and 12 August (a full weekly
round). If AMD is closed, a new-position strategy will be set against the increased cash.

---

## #4 — 2026-08-15 · WEEKLY ROUND

**Market context:** semiconductors entered a recovery trend. Risk appetite increased and the AI
infrastructure theme began to strengthen again. The portfolio gained 0.28% (0.37% behind SPY,
1.82% behind SMH). After ten days of consolidation, momentum returned in MU and AMD.

### A. Data status

Data was fetched in full for 12/12 symbols. Price, 50/200d SMA, RSI, return data and earnings
dates are present for every position. No missing fields.

**News scan:** 5 headlines each for 12 symbols (60 headlines in total). Worth noting:
- **MU:** "Micron Stock Edges Back Toward $1,000. How Far It Could Go." — the memory super-cycle
  is gaining momentum and analyst targets are rising.
- **SNDK:** "Sandisk stock surges as Wall Street cheers flash memory maker's bullish outlook" and
  "SanDisk CEO reveals what's next after explosive 3,150% stock rally" — the CEO's optimistic
  remarks confirmed a recovery in NAND demand. **Critical note:** we sold SNDK on 8 August at
  1212.21 $ and it is now 1641.11 $ (+35.4%). That was an early sale.
- **AVGO:** "AI Infrastructure Stocks: Billions of Reasons to Stay Bullish", yet the stock is
  weakening (-8.1% on the week). While the sector rises broadly, AVGO is consolidating.
- **Druckenmiller news:** increased his AMD and Amazon positions and reduced some
  semiconductors (hedge-fund flow is rotating toward AI accelerators).

### B. The cause of the move

**MU (892.67 → 971.66, +10.7%):** the momentum of the memory super-cycle. Analyst notes support
the approach to the 1,000 $ level; HBM demand is strong. A broad recovery wave across
semiconductors on rising risk appetite — MU is the momentum leader. Sector rotation (mega-caps
such as MSFT/GOOGL consolidate while semiconductors bounce).

**SNDK (1212.21 → 1641.11, +35.4%):** the CEO's optimistic guidance. A recovery in NAND demand —
Wall Street is repricing SNDK's 3,150% annual rally story. We sold on 8 August saying "momentum
broken, 28% below the 50d, thesis broken" — **but the NAND cycle turned far faster than
predicted and a technical recovery was triggered.** This confirmed that NAND is more volatile
than HBM, but this time the volatility worked against us rather than for us.

### C. Thesis health check

**MU (971.66 $) — memory super-cycle / HBM leadership → VALID**
It regained the 50d (960.65); price > 50d > 200d (552.44). Momentum is strengthening (RSI 56.3,
1mo +14.5%, 3mo +34.1%). Last round said "below the 50d, the trend is weakening" — this round we
see the trend has come back. Earnings 23 September (39 days out). Stop 730 $ (+33.1% away, very
comfortable).

**AMD (514.39 $) — AI accelerator / the NVDA alternative → VALID**
It regained the 50d (510.4) and the stop crisis passed. Last round said "if Friday closes below
440 it will be closed, the most critical level" — it stayed above 440 and the position survived.
Price > 50d > 200d (324.33), momentum stable (RSI 53.7, 1mo +3.8%, 3mo +21.3%). Druckenmiller
increasing his AMD position (a 13F filing) supports the thesis. Stop 440 $ (+16.9% away, back in
the safe zone).

**ANET (198.82 $) — leader in AI data-center network hardware → VALID**
The portfolio's steadiest performance. Price >> 50d (173.89) >> 200d (148.26), momentum strong
(RSI 59.7, 1mo +17.9%, 3mo +40.0%). It cleared its 52-week high and held the level; the bull-trap
risk did not materialise. Stop 160 $ (+24.3% away).

**AVGO (392.99 $) — custom AI chips / the networking front → WEAKENING**
Last round it was the only winning position (+2.3%, RSI 73.6 overbought). This round it fell 6.0%
and RSI dropped to 46.5 (back to normal from overbought, but momentum has been lost). Down 8.1%
on the week, 7.4% over three months — while the sector rises broadly, AVGO is consolidating. The
price is just above the 50d (390.33) by 2.66 $, very thin. Earnings 2 September (18 days out —
at the edge of the earnings rule). Stop 350 $ (+12.3% away, no danger yet). **The thesis is not
broken yet but momentum has weakened; if it loses the 50d next round, or if the stop distance
falls under +10%, it should be reassessed.**

### D. Decisions

#### DECISION 1: HOLD — every position (MU, AMD, ANET, AVGO)

**Thesis:** every position sits well above its stop level and the underlying theses hold. MU and
AMD regained the 50d (a strengthening signal), ANET is the momentum leader, and AVGO is weakening
but carries no stop risk yet. The AI infrastructure theme is in a recovery trend — the
consolidation appears to be over.

**Risk:** if AVGO's loss of momentum continues it could lose the 50d (390.33). Earnings are 18
days out, so volatility may rise. But the stop distance (+12.3%) is comfortable for now.

**Exit plan:** the stop levels are kept as they are (MU 730, AMD 440, ANET 160, AVGO 350). A
weekly close below those levels triggers a mechanical sale. Whether AVGO loses the 50d (390.33)
will be watched next round — if it does, trimming the position can be considered.

**The signal that would show the thesis is wrong:**
- MU: if it loses the 50d again before earnings (23 September) and approaches the stop (below 800).
- AMD: if it loses the 50d (510) and stays below it for three consecutive days — that could
  signal market-share loss to NVDA.
- ANET: if momentum breaks and it loses the 50d (173.89) — that would mean the breakout was
  false (a bull trap).
- AVGO: if the stop distance falls below +10% (around 370 $), or if it loses the 50d before
  earnings (2 September).

#### DECISION 2: NO NEW POSITIONS

**Cash:** 22,737 $ (22.7% of the portfolio). The charter places no limit on the cash ratio — the
current level is disciplined.

**Why no new positions?**

1. **NVDA (225.16 $):** a strong picture (price > 50d > 200d, RSI 63, 1mo +11%, earnings 26
   August). **However:** earnings are 11 days out. Last round (#3) this note was recorded: *"The
   charter: 'no new full position is opened with less than a week to earnings' — so no entry after
   19 August."* It is now 15 August — the earnings window closes in 4 days (on 19 August). **There
   are 3-4 days left for an NVDA entry, but rushing is not the right move.** We have seen momentum
   recover in AMD and MU; waiting one more round to catch a pullback, or waiting for clarity after
   the earnings report, is healthier.

2. **TSM (426.35 $):** around the 50d (425.06, +1.29 $). Last round said "awaiting confirmation of
   a turn". There is a very thin break above the 50d but it is not clear (RSI 54.3, neutral). Wait
   one more round — 2-3 closes above the 50d would confirm the turn.

3. **MRVL (222.02 $):** still below the 50d (238.07) by 6.7%. No reversal signal. Earnings 27
   August (12 days out) — at the edge of the earnings rule. Skip.

4. **PLTR (174.04 $):** still far too hot (RSI 68.1, 1mo +31.5%). The no-chasing rule applies.

5. **VRT (293.84 $):** around the 50d (296.74, 1% below it). Down 20.8% over three months — a weak
   trend. Could be dropped from the watchlist.

**Strategy:** the cash stays as powder. The existing 4 positions are solid and there is no need to
rush an addition. Next round (22 August): NVDA's earnings will have passed (26 August) and the
confirmation of a turn in TSM will be clearer. This is a time for patient waiting.

### E. Theme risk

**Portfolio:** 4 positions (MU, AMD, ANET, AVGO) — all in the AI infrastructure theme. 100%
concentration.
**Cash:** 22.7% — a buffer if the theme breaks.

**The risk of falling together:** if the AI spending cycle breaks (mega-caps cutting capex, a
signal that the AI investment bubble is bursting) every position falls together. That risk was
accepted deliberately at the outset — the price of an aggressive target (3-5x). But the theme has
started to strengthen right now; the risk level is lower than it was last round.

**Is the cash enough?** 22.7% cash is ENOUGH to protect the positions in a 30% theme correction
(77,282 $ portfolio × 0.3 = 23,184 $ of cushion). The cash buffer comes into play before the stop
levels trigger in a theme break. The current cash level is disciplined.

**Diversification assessment:** a position outside AI infrastructure (say the mega-caps
MSFT/GOOGL) could be opened to lower the theme risk, but that lowers beta and reduces the
contribution to a 3-5x target. The charter permits it, but the current strategy is kept for now —
the theme is in a strengthening trend.

### F. Accounting for myself

**1. What did I say last round, and what did I do this round?**

**Last round (#3, 8 August):**
- **AMD:** "if Friday (11 August) closes below 440 it WILL BE CLOSED (per the charter)" → AMD
  stayed above 440, the position was held, and it regained the 50d. **No departure — it went as I
  said.**
- **MU, ANET, AVGO:** I said HOLD → I held. **No departure.**
- **NO NEW POSITIONS:** I said "NVDA can be considered but there is no hurry; clarifying AMD's stop
  situation comes first" → I opened no new position. **No departure.**
- **SNDK:** I sold at 1212.21 $, saying "thesis broken, momentum broken, the stop distance is tight
  (+10.2%), a proactive loss cut" → **SNDK is now 1641.11 $ (+35.4%).**

**THERE IS A DEPARTURE — the early SNDK sale:**
I sold SNDK saying "thesis broken, the NAND cycle is far more volatile than HBM, the correction can
deepen". The broken-thesis rationale was correct (28% below the 50d, momentum broken, 1mo -36.7%).
BUT the NAND cycle turned **far faster than predicted** — with the CEO's optimistic remarks and
Wall Street's support, SNDK gained 35.4% in a week. **Where I was wrong:** I underestimated the
speed of the NAND cycle. I exited early saying "the stop distance is tight (+10.2%), waiting
another week enlarges the loss" — but the market's turn arrived before the stop triggered.

**I am not bending the rationale to the outcome:** the sale decision was made with the right data
for that day (momentum broken, far below the 50d, a tight stop). But NAND's volatility runs both
ways — fast on the way down and fast on the way back up. I have learned this lesson: in highly
volatile cyclical positions the stop distance should be wider, or a technical reversal signal (a
return to the 50d, say) can be waited for. If I am going to exit proactively at a 15% loss, I
should have kept the symbol on the watchlist for a re-entry opportunity at the next check — I did
not remove SNDK from the list, but I did not actively track it either.

**2. Where last round's thesis turned out wrong:**

The SNDK thesis: "the NAND cycle is far more volatile than HBM, the correction can deepen." → YES
it is volatile, but it also turned UPWARD very fast. What the thesis missed: I did not account for
the **speed of the turn** in the NAND cycle. Because the company fundamentals (CEO guidance) can
change quickly, a technical recovery can arrive before the stop triggers. **I am carrying the
lesson into later rounds.**

**3. Where this round's decision could mislead me:**

**The decision not to enter NVDA:** I said "the earnings window closes in 4 days but I am not
rushing; I will wait one more round". If NVDA's earnings come in very strong and the stock gains
20%, I will have missed the window. But earnings risk runs both ways — if it disappoints,
protecting the existing positions will have been the better call. **I accept the risk: waiting for
NVDA's earnings may mean missing the opportunity. But discipline requires it — waiting for clarity
rather than rushing an entry.**

**The decision to hold AVGO:** I said "weakening but no stop risk yet". If AVGO loses the 50d
(390.33) and approaches its stop before earnings (below 360), I will have been late to trim. If it
has lost the 50d next round I will consider trimming — but holding is the disciplined call for now.

**Next review:** 22 August 2026 (Saturday — the next weekly round). AVGO's 50d status, the market
reaction after NVDA's earnings (26 August) and the confirmation of a turn in TSM will be watched.

---

## #5 — 2026-08-22 · WEEKLY ROUND

**Market context:** semiconductors consolidated on the week. The portfolio was -2.86% (SPY -0.73%,
SMH -2.66%). The AI infrastructure theme is choppy; the mega-caps (MSFT/GOOGL) are steady while
semiconductors correct.

### A. Data status

Data was fetched in full for 12/12 symbols (based on the 22 August 2026 close). Price, 50/200d
SMA, RSI, returns and earnings dates are present for every position. No missing fields.

**News scan:** 60 headlines in total across 12 symbols. Worth noting:

- **MU:** "Micron's AI boom rolls on with $10 billion Iowa data center" — a 10-year, 10 bn $ R&D
  investment was announced (starting in 2027). "Micron Fell 7%. Is This an Opportunity to Buy?" —
  opportunity pieces after the weekly correction. The memory super-cycle theme continues.

- **AMD:** "AMD Investors Must Be Ready For Major News On Aug. 26" — the upcoming NVDA earnings
  will be a test for the AI accelerator sector. "The Best Semiconductor Stock to Buy Isn't AMD or
  Qualcomm: It's Nvidia" — the competitive-pressure narrative continues.

- **AVGO:** "Broadcom Is Down 6.2% After Google Expands AI Chip Ties With Marvell" — Google
  expanding its partnership with MRVL reflected badly on AVGO (competition in custom AI chips).
  The stock is weakening.

- **MRVL:** "Google Is Getting Paid in Marvell Stock Warrants for Buying Marvell's Chips" — the
  Google partnership is strengthening and the stock is +6.8% on the week. It broke above the 50d.

- **SNDK:** "SanDisk Makes a Quiet Move Into AI's Next Boom" — the story of expanding from NAND
  into AI storage. The stock is 1596.08 $ (we sold on 8 August at 1212.21 $, missing a 31.7% gain).

### B. The cause of the move

No position moved more than ±10% on the week. But AVGO's -6.2% week (the worst in the portfolio)
and its loss of the 50d are critical:

**AVGO (418.16 → 368.45, -11.9% in total on a portfolio basis):** the expansion of the Google-MRVL
partnership signals rising competition in the custom AI chip market. AVGO risks losing its position
as the preferred supplier for the "AI XPU" theme to MRVL. The stop distance narrowed (+12.3% →
+5.3%) and earnings are 11 days out (2 September). ***Last round (#4, 15 August) said this:*** *"AVGO
→ WEAKENING… The thesis is not broken yet but momentum has weakened; if it loses the 50d next round,
or if the stop distance falls under +10%, it should be reassessed."* → Both conditions occurred.

### C. Thesis health check

**MU (966.78 $) — memory super-cycle / HBM leadership → VALID**
Price > 50d (964.54, +2.24) > 200d (570.95), RSI 54.3 (healthy). 1 week -0.5%, 1 month +5.0%,
3 months +28.8%. Stop 730 $ (+32.4% away, very comfortable). Earnings 23 September (32 days out).
The 10 bn $ R&D announcement supports the thesis. It is holding the 50d support and momentum is
stable.

**AMD (473.25 $) — AI accelerator / the NVDA alternative → WEAKENING**
Price < 50d (510.23, -36.98 / -7.25%), > 200d (329.86). RSI 45.8 (weak). 1 week -8.0%, 1 month
-9.3%, 3 months +1.2%. Stop 440 $ (+7.6% away — TIGHT!). Earnings 3 November (73 days out). Last
round it had regained the 50d (514.39); this round it lost it again. NVDA's earnings are on 26
August — if NVDA's guidance comes in very strong, competitive pressure on AMD increases. ***The
thesis is not broken yet, but losing the 50d signals weakening momentum. The stop distance is
tight; the next round is critical.***

**ANET (188.65 $) — leader in AI data-center network hardware → VALID**
Price > 50d (177.36, +11.29) >> 200d (149.06). RSI 51.7 (neutral). 1 week -5.1%, 1 month +8.4%,
3 months +22.5%. Stop 160 $ (+17.9% away). Earnings 3 November. It is holding the 50d support
despite the weekly correction. The portfolio's steadiest position.

**AVGO (368.45 $) — custom AI chips / the networking front → BROKEN**
Price < 50d (388.43, -19.98 / -5.14%), ≈ 200d (368.3, +0.15). RSI 38.7 (weak). 1 week -6.2%,
1 month -3.5%, 3 months -10.9%. Stop 350 $ (+5.3% away — VERY TIGHT!). Earnings 2 September (11
days out). ***Last round's warning: "reassess if it loses the 50d or if the stop distance falls
under +10%" — both conditions occurred.*** The Google-MRVL partnership weakened AVGO's custom AI
chip thesis. Momentum is broken and volatility risk ahead of earnings is high. The thesis is broken.

### D. Decisions

#### DECISION 1: TRIM — AVGO (position cut in half)

**Trade:** SELL 11.96 shares of AVGO @ 368.45 $ → **+4,406 $ cash** (half the position remains:
11.96 shares)

**Thesis (the reason for trimming):** last round (#4) warned explicitly: *"it should be reassessed
if it loses the 50d or if the stop distance falls under +10%."* Both conditions occurred:
- It lost the 50d (388.43 → price 368.45, 5.14% below it)
- The stop distance narrowed to +5.3% (well under +10%)

**The risk-management principle:** the thesis is broken, but rather than closing the position
entirely I am halving it:
1. **The negative scenario carries more weight:** the Google-MRVL partnership threatens AVGO's
   position in the custom AI chip market. Earnings are 11 days out; if guidance is weak the stop
   could trigger. Rather than closing fully, I reduce the exposure by trimming.
2. **The positive scenario is still possible:** AVGO is sitting on its 200d support (368.45 vs
   368.3). Earnings could come in strong and it could regain the 50d. Holding half preserves that
   possibility.
3. **Discipline:** a warning was given last round, the conditions occurred, and action was taken.
   No silent departure.

**Position update:**
- Before: 23.9143 shares at a 418.16 $ cost basis (a 10,000 $ entry)
- Sold: 11.96 shares @ 368.45 $ (4,406 $ cash)
- Remaining: 11.95 shares at a 418.16 $ cost basis (5,000 $ of entry cost)
- **New weight:** ~5% (halved from the previous 9.1%)

**Loss:** on the 11.96 shares sold: (368.45 - 418.16) × 11.96 ≈ -594 $ (an 11.9% loss on half the
position). The remaining 11.95 shares keep the 418.16 $ cost basis — the stop stays at 350 $
(+5.3% away).

**Exit plan (for the remaining half):** stop 350 $ unchanged — close it entirely on a weekly close
below that. Earnings 2 September — if it cannot regain the 50d (388.43) and approaches the stop
(below 360), consider closing before the report. If it regains the 50d and earnings come in
strong, the position can be rebuilt.

**The signal that would show the thesis is wrong:** if the earnings guidance (2 September) is weak
and it approaches the 350 stop — close fully. If earnings are strong, it regains the 50d, and RSI
climbs above 50 — the thesis can be repaired and the position rebuilt.

#### DECISION 2: HOLD — MU, ANET

**MU:** the thesis holds, it is above the 50d, and the stop distance is very comfortable (+32.4%).
The 10 bn $ R&D announcement supports the memory theme. Earnings are 32 days out (23 September) —
carrying the position is disciplined. Stop 730 $ retained.

**ANET:** the steadiest position. Holding the 50d support, momentum solid. The -5.1% week is within
normal volatility. Stop 160 $ retained (+17.9% away).

**Exit plan:** stop levels unchanged (MU 730, ANET 160). A weekly close below them triggers a
mechanical sale.

**The signal that would show the thesis is wrong:**
- MU: if it loses the 50d before earnings (23 September) and approaches the stop (below 800).
- ANET: if it loses the 50d (177.36) and stays below it for three consecutive days — a momentum
  break signal.

#### DECISION 3: WATCH — AMD (one more round)

**AMD:** it lost the 50d (510.23 → price 473.25, 7.25% below) and the stop distance is tight
(+7.6%). ***But there is no stop breach yet and NVDA's earnings arrive on 26 August — a critical
test for the AI accelerator sector.***

**Decision:** watch one more round. See how AMD reacts after NVDA's earnings (26 August). If NVDA's
guidance comes in very strong and AMD approaches its stop (below 450), an interim assessment can be
made. If AMD holds the stop, hold it until the next round on 29 August.

**Risk:** the stop distance is tight (+7.6%). Another 7% weekly decline (≈440 $) triggers the stop.
If NVDA's earnings disappoint and the sector sells off, AMD could be dragged down too.

**Why I am not trimming now:** I trimmed AVGO because a warning had been issued last round and both
conditions occurred. There was no warning for AMD; the 50d loss appeared this round. Discipline:
trimming two positions in the same round pushes the portfolio into excessive cash (27.5%). I am
granting AMD one more round of waiting — but the stop is absolute.

**Exit plan:** stop 440 $ — close on a weekly close below it. After NVDA's earnings (26 August), an
interim assessment if AMD falls below 450.

**The signal that would show the thesis is wrong:** if NVDA's earnings come in very strong and the
guidance shows the AI accelerator market concentrating on NVDA — AMD's "NVDA alternative" thesis
weakens.

#### DECISION 4: NO NEW POSITIONS

**Cash:** after the AVGO trim, 22,737 + 4,406 = **27,143 $ (27.5% of the portfolio)**.

**Why no new positions?**

1. **NVDA (214.72 $):** earnings 26 August (4 days out). ***Last round (#4, 15 August) said
   this:*** *"Earnings are 11 days out… no entry after 19 August."* → The earnings window closed on
   19 August. It is now 22 August — no entry (the earnings rule). It can be assessed after the
   report (at the next round on 29 August).

2. **MRVL (237.04 $):** it broke the 50d (233.82 → price 237.04, +1.38% above it) with strong
   momentum (1 week +6.8%, 1 month +22.0%, RSI 55.8). The Google partnership news is positive.
   ***But earnings are 27 August (5 days out).*** The earnings rule: "no new full position with
   less than a week to earnings" — 5 days is at the edge. It can be assessed after the report (at
   the next round on 29 August). Waiting for the report is more disciplined than rushing an entry.

3. **TSM (418.95 $):** still below the 50d (424.52, 1.31% below it). Last round said "awaiting
   confirmation of a turn" — there is still no clear signal. RSI 50.4 (neutral), 1 week -1.7%. Wait
   one more round.

4. **PLTR (179.94 $):** RSI 69.4 (close to overbought), 1 month +46.4%. Still far too hot. The
   no-chasing rule applies.

5. **VRT (261.95 $):** far below the 50d (293.89, 10.86% below it), RSI 42.2 (weak), 1 week -10.9%,
   3 months -20.0%. Momentum broken — could be dropped from the watchlist.

**Strategy:** cash rose to 27.5%. NVDA's and MRVL's earnings land on 26-27 August — both will be
clear by the next round (29 August). AMD's reaction after NVDA's report will be watched. This is a
time for patient waiting — waiting for clarity rather than rushing an entry.

### E. Theme risk

**Portfolio:** 3.5 positions (MU 33.4%, AMD 18.8%, ANET 15.3%, AVGO 5% — a half position) — all in
the AI infrastructure theme. 72.5% invested, 27.5% cash.

**The risk of falling together:** if the AI spending cycle breaks (NVDA's earnings coming in very
weak, mega-caps cutting capex) every position falls together. That risk was accepted deliberately at
the outset. ***But this round I reduced the theme concentration by trimming AVGO — I partially
exited the custom AI chip front and lowered the exposure.***

**Cash: NOT a protective cushion but buying power.** 27.5% cash does not protect the portfolio (an
unleveraged virtual portfolio); it is powder for a decline. ***What I am waiting for:*** (1) the
sector reaction after NVDA's earnings — if AI accelerators sell off hard, an entry opportunity in
AMD or TSM. (2) After MRVL's earnings — if the Google partnership is confirmed and it stays above
the 50d, a new position. (3) An addition to the existing positions (MU/ANET) if they correct. The
cash will not be held passively; it is waiting for an opportunity.

**Diversification:** opening a position outside AI infrastructure lowers the theme risk but also
lowers beta (less contribution to a 3-5x target). The charter permits it, but the AI theme remains
the core strategy for now. The increase in cash has already balanced the theme risk somewhat.

### F. Accounting for myself

**1. What did I say last round, and what did I do this round?**

**Last round (#4, 15 August):**
- **HOLD MU, AMD, ANET, AVGO:** I held — but I halved AVGO. **THERE IS A DEPARTURE (explained
  below).**
- **NO NEW POSITIONS:** "NVDA can be considered but there is no hurry" → I opened no new position.
  **No departure.**
- **The AVGO warning:** *"AVGO → WEAKENING… it should be reassessed if it loses the 50d next round
  or if the stop distance falls under +10%."* → Both conditions occurred and I trimmed the
  position. **No departure — it went as I said.**

**THERE IS A DEPARTURE — I trimmed AVGO rather than holding it fully:**
Last round I said "HOLD" but gave an explicit warning: "*it should be reassessed if it loses the 50d
next round or if the stop distance falls under +10%*". Both conditions occurred this round:
- It lost the 50d (388.43 → 368.45, 5.14% below it)
- The stop distance narrowed to +5.3% (well under +10%)

**I am writing the departure down explicitly:** I said "HOLD" but I had given a conditional warning.
When the conditions occurred I acted. No silent departure — I wrote the warning last round and
applied it this round. **This is not a departure but the execution of a conditional plan.** Still,
the word "HOLD" could have been read as absolute; to be clearer I should have used a "HOLD, BUT…"
format last round.

**2. Where last round's thesis turned out wrong:**

**The AVGO thesis:** "custom AI chips / the networking front → WEAKENING but not yet broken." → This
round it BROKE. The expansion of the Google-MRVL partnership signalled that AVGO could lose its
position in the custom AI chip market to MRVL. Last round I said "the thesis is not broken yet" —
this round the market showed it was (the 50d loss, RSI 38.7, -6.2% on the week). **Where I was
wrong:** I had hoped "earnings could come in strong and it could regain the 50d" — but it broke
before the report, with 11 days still to go. The competition news gave the signal to act without
waiting for earnings. **I am carrying the lesson into later rounds:** in a position facing
competition news, trimming at the moment of technical breakdown is better than waiting for earnings.

**The NVDA window:** last round I said "the decision not to enter NVDA: the earnings window closes in
4 days but I am not rushing". **Did I miss the opportunity?** NVDA is now 214.72 $ (225.16 last
round, a 4.6% fall). By not entering I avoided a loss. Earnings are 26 August — waiting for the
report proved right rather than missing the window. If NVDA's earnings come in strong and it gains
20%, I will have missed the window. But earnings risk runs both ways — if it disappoints, protecting
the existing positions will have been the better call. **I accept the risk: waiting for NVDA's
earnings may mean missing the opportunity. But discipline requires it.**

**3. Where this round's decision could mislead me:**

**The decision to hold AMD:** I said "it lost the 50d and the stop distance is tight (+7.6%) but I
will wait for NVDA's earnings". If NVDA's earnings come in weak and the AI accelerator sector sells
off, AMD could approach its stop (below 450) or trigger it (440). Then I could regret it: "I trimmed
AVGO but should have considered trimming AMD in the same round." **But discipline requires this:** a
warning had been given for AVGO last round and the conditions occurred; there was no warning for
AMD. Trimming two positions in the same round pushes the portfolio into excessive cash. I am
granting AMD one more round of waiting — but the stop is absolute.

**The decision not to close AVGO entirely:** I sold half and held half. If earnings (2 September)
come in very weak and AVGO falls to its stop (350), I could regret not closing fully. But it is
sitting on its 200d support (368.45 vs 368.3); earnings could come in strong and it could regain the
50d. **Holding half preserves the positive scenario — but that also means preserving half the loss.**

**The decision not to enter MRVL:** I said "earnings are 5 days out, I will wait". If MRVL's earnings
come in very strong and the stock gains 20%, I will have missed the window. But the earnings rule
says "no new full position with less than a week to earnings" — 5 days is at the edge. **Discipline
requires it: waiting for clarity rather than rushing an entry.**

**Next review:** 29 August 2026 (Saturday — the next weekly round). The market reaction after NVDA's
earnings (26 August) and MRVL's earnings (27 August), AMD's situation, and whether AVGO regained the
50d will be watched.

---

## #6 — 2026-08-29 · WEEKLY ROUND

**Market context:** the sector consolidation continues. The portfolio was -2.76% (SPY -0.03%, SMH
-0.47%). Semiconductors were mixed on the week; NVDA's and MRVL's earnings have passed.

### A. Data status

**CRITICAL DATA GAP:** the weekly_data.py script could not fetch price, SMA or return data (every
value was NaN). RSI, earnings dates and news headlines did come through.

**Alternative source used:** REPORT.md (the Friday 28 August closing prices, produced by update.py).

**Missing data:**
- SMA50/200: absent → no 50d/200d support analysis is possible
- 1-week / 1-month / 3-month returns: absent → weekly momentum analysis is limited
- Detailed price history: absent → no trend analysis is possible

**News scan:** 60 headlines across 12 symbols. Worth noting:

- **MU:** "Intel Sold Its NAND Memory Business for About $9 Billion. Micron Is Now Worth More Than
  Twice What Intel Is." — Intel's exit from memory strengthens MU's market position. "Jim Cramer
  Shared Why Micron Technology Shares Didn't Rise On Shortage News" — the supply-shortage news has
  not been fully priced in yet.

- **AMD:** "Broadcom vs. AMD: Which AI Chip Stock Has the Better Risk-Reward?" — the comparison with
  AVGO continues. No company-specific news.

- **AVGO:** "Broadcom's Debt Deal Could Reach $100 Billion in the AI Buildout's Latest
  Mega-Financing" — a 100 bn $ debt deal; the AI investment plan is large. "Jobs report, Broadcom
  results pose next hurdles for stock market rally" — the earnings report (2 September) is a
  critical test for the market relative to expectations.

- **MRVL:** "Stock Market Today, Aug. 28: Marvell Slides 10% on Softer Fiscal 2028 Guidance and
  Google Deal Timing" — THE EARNINGS RESULT: earnings were strong but the 2028 guidance was soft and
  the stock fell 10%. There is a risk the Google deal slips. "Marvell Fell After Its Google Deal. Why
  Did Investors Sell These Two AI Optics Stocks Too?" — MRVL's decline dragged the optics sector down
  with it.

- **NVDA:** "Wall Street is turning Nvidia's AI chips into a new futures market: Chart of the Day" —
  NVDA chips are trading like a futures market. The earnings result is not clear from the headlines
  but the current momentum looks strong.

**Symbol count:** 12/12 (for RSI and news), but price data 0/12 (from weekly_data.py).

### B. The cause of the move

No position moved more than ±10% on the week:

- **MU:** 966.78 → 935.39 (-3.2%, the 28 Aug close per REPORT.md)
- **AMD:** 473.25 → 476.67 (+0.7%)
- **ANET:** 188.65 → 201.09 (+6.6%)
- **AVGO:** 368.45 → 371.54 (+0.8%)

Every move is within normal volatility. No ±10%+ move requires special investigation.

### C. Thesis health check

**DATA LIMITATION:** without the SMAs, "above / below the 50d" analysis is impossible. The assessment
is limited to price action, RSI and news.

**MU (935.39 $, the 28 Aug close per REPORT.md) — memory super-cycle / HBM leadership → VALID**
Down 3.2% against last round (from 966.78). RSI 51.0 (neutral, weekly_data.json). Stop 730 $ (+28.1%
away per REPORT.md — very comfortable). Earnings 23 September (portfolio.json) / 30 September
(weekly_data.json — there is an inconsistency; I am taking portfolio.json as the basis: 23 September,
25 days out). Intel's exit from NAND increases MU's market power. A mild correction is normal.
**The 50d status is unknown (no SMA data) — that is a critical gap.**

**AMD (476.67 $) — AI accelerator / the NVDA alternative → WEAKENING (unchanged)**
Up 0.7% against last round (from 473.25). RSI 47.4 (weak). Stop 440 $ (+8.3% away per REPORT.md —
TIGHT, but above it on the weekly close, so the stop held). Earnings 3 November. Last round's warning:
"it lost the 50d, reassess after NVDA's earnings" → **the 50d status is unknown (no SMA data).** NVDA's
earnings have passed but the result is not clear from the headlines. AMD moved minimally (+0.7%) — the
stop held but momentum is still weak (RSI 47.4). **The thesis is weakening but there is no stop
breach; the technical picture is only half available, so wait one more round.**

**ANET (201.09 $) — leader in AI data-center network hardware → VALID**
Up 6.6% against last round (from 188.65 — the strongest weekly performance). RSI 59.2 (healthy).
Stop 160 $ (+25.7% away — very comfortable). Earnings 3 November. **The portfolio's steadiest
position.** A +6.6% week is a show of strength. **The 50d status is unknown, but the price advance
suggests momentum is intact.**

**AVGO (371.54 $, half position) — custom AI chips / the networking front → BROKEN (unchanged)**
Up 0.8% against last round (from 368.45 — a minimal recovery). RSI 43.9 (weak, a slight improvement
from 38.7 last round). Stop 350 $ (+6.2% away per REPORT.md — TIGHT, but above it on the weekly
close). Earnings **2 September (3 days out — CRITICAL!)**. Last round the position was trimmed in
half and the thesis was labelled "broken". The 100 bn $ debt deal shows the scale of the AI
investment plan, but **the Google-MRVL competition theme persists** (MRVL's 10% post-earnings fall
came from the risk the Google deal slips). **The 50d status is unknown.** The minimal recovery (+0.8%)
and the slight RSI improvement (43.9) are positive, but **earnings are 3 days out and volatility risk
is very high.** The thesis is still broken.

### D. Decisions

**DATA GAP WARNING:** without the SMAs and detailed returns, technical analysis is impossible. Last
round (#5) said "whether it regained the 50d will be watched" — that analysis could not be done.
The decisions are limited to price action, stop distances and news.

#### DECISION 1: HOLD — MU, ANET, AMD

**MU:** the stop distance is very comfortable (+28.1%), the thesis holds (Intel's exit strengthens
it), and earnings are 25 days out (23 September). A -3.2% week is a normal correction. **The 50d
status is unknown, but because the stop distance is comfortable, carrying the position is safe.** Stop
730 $ retained.

**ANET:** +6.6% on the week, the strongest performance; RSI 59.2 healthy; the stop distance very
comfortable (+25.7%). The thesis holds and momentum is strong. Stop 160 $ retained.

**AMD:** the stop held (+8.3% away) and the price moved minimally (+0.7%). RSI 47.4 is still weak.
Last round said "reassess after NVDA's earnings" — **NVDA's earnings have passed but the result is
not clear from the headlines, and AMD moved +0.7% rather than -0.7% (a mild recovery).** **The 50d
status is unknown — a critical gap.** No stop breach → hold one more round. **Warning: the stop
distance is tight (+8.3%); a weekly close below 440 $ triggers a mechanical sale.** Stop 440 $
retained.

**Exit plan:** stop levels unchanged (MU 730, ANET 160, AMD 440). A weekly close below them triggers a
mechanical sale.

**The signal that would show the thesis is wrong:**
- MU: if it approaches the stop before earnings (below 800) — though without the 50d status I cannot
  set a precise trigger.
- ANET: if it approaches the stop (below 180) — a momentum break signal.
- AMD: a weekly close below 440 $ → a mechanical sale.

#### DECISION 2: WATCH — AVGO (the half position)

**Situation:** 11.95 shares at a 418.16 $ cost basis, price 371.54 $ (an 11.1% loss). Stop 350 $
(+6.2% away — TIGHT). Earnings **2 September (3 days out).**

**Decision:** hold the half position and wait for earnings. Last round (#5) the position was trimmed
in half with this note: *"Earnings 2 September — if it cannot regain the 50d and approaches the stop
(below 360), consider closing before the report."* → The price is 371.54 $, i.e. above 360. **The 50d
status is unknown (no SMA data) — a critical gap.** RSI 43.9 (a slight improvement from 38.7 last
round). The 100 bn $ debt deal shows the scale of the AI investment plan.

**Why I am not closing now:** the price is above 360 and the 350 stop held on the weekly close.
Earnings are 3 days out — closing now means exiting without waiting for the report at all. Last round
said "the positive scenario is still possible; holding half preserves that possibility."
**Discipline: wait for earnings, then decide.**

**Risk:** if earnings disappoint (the effect of Google's competition, weakness in the 2028 guidance)
the stock could fall to its stop (350). Then I could regret it: "I should have closed before the
report." But the 100 bn $ debt deal shows how serious the AI investment plan is — earnings could come
in strong.

**Exit plan:** stop 350 $ — a mechanical sale on a weekly close below it. Reassess after the report
(the 5 September Friday close / the 6 September Saturday round). If earnings are strong and **it
regains the 50d** (checkable next round if SMA data is available), the position can be rebuilt. If
earnings are weak and it approaches the stop, the remaining half is closed.

**The signal that would show the thesis is wrong:** if the earnings guidance (2 September) is weak
and the Google-competition theme strengthens → close fully.

#### DECISION 3: NO NEW POSITIONS

**Cash:** 27,142 $ (27.9% of the portfolio, per REPORT.md).

**Why no new positions?**

**A CRITICAL LIMITATION:** without the SMAs and detailed returns, no technical entry analysis is
possible. I cannot answer critical questions like "did it break the 50d, is it sitting on the 200d
support". **The data gap alone prevents opening a new position.**

**Watchlist notes (limited to the news):**

1. **NVDA:** earnings have passed (26 August). Headlines: "AI chips into a new futures market", "AI
   lobbying gains new foothold" — momentum looks strong. RSI 61.3 (healthy). **But there is no price
   or SMA data — no entry analysis is possible.** It can be assessed with complete data next round.

2. **MRVL:** the earnings result is clear: "Slides 10% on Softer Fiscal 2028 Guidance and Google Deal
   Timing" — earnings strong but guidance soft, the stock fell 10%. There is a risk the Google deal
   slips. RSI 56.3 (neutral). **Entering now is risky because of the guidance weakness.** Wait until
   the Google deal is clearer.

3. **TSM:** RSI 55.2. Headlines: "Taiwan Semiconductor Stock Looks Stretched As Its 363% Run
   Continues", "Billionaire Stanley Druckenmiller Just Bought Taiwan Semiconductor Stock." — stretched
   after a long rally. **No price or SMA data — cannot be assessed.**

4. **PLTR:** RSI 69.1 (close to overbought). Headlines: "Can PLTR Stock Live Up To Its Multiple?",
   "Pentagon AI surge comes with a question investors can't ignore" — the multiples are high and the
   risk has risen. Still far too hot.

**Strategy:** cash is 27.9% — clarity will come after AVGO's earnings (2 September). A new position is
risky given the data gap; NVDA, TSM and MRVL can be assessed with complete data at the next round (5
September). **Waiting for data and clarity rather than rushing an entry.**

### E. Theme risk

**Portfolio:** 4 positions (MU 32.3%, AMD 18.9%, ANET 16.3%, AVGO 4.6% — a half position, weights per
REPORT.md) — all in the AI infrastructure theme. 72.1% invested, 27.9% cash.

**The risk of falling together:** if the AI spending cycle breaks, every position falls together. That
risk was accepted deliberately at the outset and still stands. Last round the theme concentration was
partly reduced by halving AVGO — a partial exit from the custom AI chip front.

**Cash: NOT a protective cushion but buying power.** 27.9% cash does not protect the portfolio (an
unleveraged virtual portfolio); it is powder for a decline. **What I am waiting for:** (1) clarity
after AVGO's earnings (2 September) — if the report is strong and the sector recovers, an entry in
NVDA or TSM. (2) An opportunity to add to the existing positions (MU/ANET) if they correct. (3) **Once
the data gap is fixed**, assessing the watchlist symbols with complete technical analysis. The cash
will not be held passively; it is waiting for an opportunity and for clarity.

**Diversification:** opening a position outside AI infrastructure lowers the theme risk but also lowers
beta (less contribution to a 3-5x target). The AI theme remains the core strategy for now. The cash
ratio (27.9%) already balances the theme risk somewhat.

### F. Accounting for myself

**1. What did I say last round, and what did I do this round?**

**Last round (#5, 22 August):**
- **HOLD MU, ANET:** I held. **No departure.**
- **WATCH AMD:** "reassess after NVDA's earnings" → NVDA's earnings passed, AMD recovered slightly
  (+0.7%), the stop held. I held. **No departure — the watch continues.**
- **WATCH AVGO (the half position):** "wait for earnings; reassess if it falls below 360" → the price
  is 371.54 $ (above 360) and I held. **No departure.**
- **NO NEW POSITIONS:** "NVDA and MRVL can be assessed after their earnings" → the reports came out
  but I opened no new position because of the data gap. **No departure — discipline: do not open a new
  position when data is missing.**

**NO DEPARTURES.** I did everything I said I would last round.

**2. Where last round's thesis turned out wrong:**

**The AMD thesis:** "WEAKENING — it lost the 50d, reassess after NVDA's earnings." → **The 50d status
is unknown (no SMA data this round) — it could not be checked.** But AMD's stop held and it recovered
slightly (473.25 last round, 476.67 this round). If it regained the 50d (checkable next round), the
thesis may have escaped its weakening. **I cannot say where I was wrong because the critical data is
missing.** I kept the "weakening" label for this round.

**The AVGO thesis:** "BROKEN — the Google-MRVL competition." → **The thesis is still broken.** MRVL fell
10% after its earnings (weak guidance, a risk the Google deal slips), which could be positive for AVGO
(less competition), but AVGO's own report has not arrived yet (2 September). The minimal recovery
(+0.8%) and the slight RSI improvement (43.9) are positive, but **upgrading the thesis from "broken"
to "weakening" before the report would be premature.** I will reassess after the report.

**The MRVL assessment:** last round I said "MRVL can be assessed after its earnings (27 August)". The
result: earnings strong but the 2028 guidance soft, the stock down 10%, a risk the Google deal slips.
**Where I was wrong:** I had thought positively — "the Google partnership is strengthening" (last
round's watchlist) — but the report surfaced the timing risk. **The lesson:** large partnerships like
Google carry timing risk; waiting for the report was the right call, and by not entering I avoided a
10% decline.

**3. Where this round's decision could mislead me:**

**THE DATA-GAP RISK — THIS ROUND'S BIGGEST RISK:** I decided without the SMAs and detailed returns.
Last round I said "whether it regained the 50d will be watched" — I could not perform that check.
**I said "hold" without knowing whether AMD or AVGO had regained the 50d. If they have lost it and
momentum has weakened further, I could regret missing the warning "because of a data gap" next round.**
But the prices in REPORT.md are weekly closes and the stop checks could be done — the stops held, which
is the most critical discipline. **The 50d status is unknown but stop discipline was preserved.**

**The AVGO earnings risk:** I said "wait for the report". If the report comes in very weak and the
stock falls to its stop (350), I could regret it: "I should have closed before the report; I had a
chance to exit while the price was above 360." But the 100 bn $ debt deal shows how serious the AI
investment plan is — earnings could come in strong. **I accept the risk: waiting for the report means
risking a stop trigger.**

**The risk of not opening a new position:** I said "no new positions because of the data gap". If NVDA
gains 15% next round and I missed it because of the data gap, I could regret it: "I could at least have
entered NVDA using the prices in REPORT.md." But **entering without knowing the 50d status means
gambling rather than analysing.** Discipline: do not open a new position when data is missing. **The
lesson:** I need to fix the data-collection script or find a backup source — a data gap means a lost
opportunity.

**Lesson calibration:**
- **Hypothesis (not yet a behaviour change):** the data-collection script is having trouble in the
  GitHub Actions environment. It must be fixed next round — a backup data source (computing the SMAs
  myself from history.csv prices, or a different API). I am not drawing the lesson "never trade when
  data is missing" from this single event — as long as the stops hold, carrying the existing positions
  is disciplined. But the "do not open a new position" rule stands: do not enter without technical
  analysis.

**Next review:** 5 September 2026 (Saturday — the next weekly round). The market reaction after AVGO's
earnings (Tuesday 2 September), AMD's and AVGO's 50d status (SMA data), and complete technical analysis
for NVDA / TSM / MRVL. **Fixing the data-collection script is critical.**

---

## #7 — 2026-09-05 · WEEKLY ROUND

**Market context:** semiconductors are in a recovery trend. The portfolio was -0.74% (SPY -0.15%, SMH
-1.51%). The AI infrastructure theme is strengthening; the memory and network hardware leaders gained
momentum.

### A. Data status

Data was fetched in full for 12/12 symbols (based on the Wednesday 4 September close). Price, 50/200d
SMA, RSI, return data and earnings dates are present for every position. **No missing fields — last
round's data gap is resolved.**

**Data-integrity gate check:** the `last_price` and `sma50` fields were checked one by one for every
position (instructions version 6, step 3). Every field is populated. `_meta.missing_data` = [] (empty).

**News scan:** 60 headlines in total across 12 symbols. Worth noting:

- **MU:** "Micron Stock Closes Above $1,000" — a close above 1,000 $. "David Tepper Sold 41% of His
  Micron Shares and It Is Still His Second-Biggest Holding" — large investors are taking profit but the
  position is still large. "Dow Jones Futures: Nvidia, Micron, Sandisk Flash Buy Signals" — a buy
  signal.

- **AMD:** "AMD's Data Center Revenue and EPS to Double by 2027" — analyst reports project growth in
  2027. "Here's the Real Reason Nvidia Is Buying Hugging Face" — an NVDA move, competitive pressure.
  "Shares Down 19%, It's a Buy" — buy-the-dip pieces after the 19% fall.

- **ANET:** "ANET Rises 37.3% in Six Months: Is There More Room to Grow?" — the valuation question
  after a six-month rally. "How Much Track Is Left For ANET Stock?" — is the growth sustainable.

- **AVGO:** "Broadcom (AVGO) Stock Is Down After Q3 Earnings: Is It Too Soon to Buy the Dip?" —
  **THE EARNINGS RESULT: a decline after Q3.** "Jim Cramer Says 'Someone Must Know Something' About
  Broadcom's Post-Earnings Share Dip" — a Cramer warning that something may lie behind the
  post-earnings fall. "Why Broadcom CEO Called Anthropic and OpenAI 'Two Geniuses in the Middle of
  Mongolia'" — a CEO interview emphasising AI investment.

- **SNDK:** "SanDisk Soars on S&P 100 Inclusion; Hedge Fund Ownership More-Than-Doubles" — **ADDED TO
  THE S&P 100**, hedge fund ownership doubled. "Dow Jones Futures: Nvidia, Micron, Sandisk Flash Buy
  Signals" — a buy signal. **We sold on 8 August at 1212.21 $; it is now 1740.00 $ (+43.5% in a month).**

- **NVDA:** "I'm Confident This Stock Will Double by 2030" — a long-term growth projection. No
  company-specific news; momentum is strong.

- **TSM:** "Prediction: Taiwan Semiconductor Stock Will Surge by 22% Before 2026 Ends" — a year-end
  target. "Japan, U.S. advance $550 billion investment pact with AI, chips in focus" — macro support.

### B. The cause of the move

No position moved more than ±10% on the week. **No move requires special investigation.** Weekly
performance:
- MU: 935.39 → 1016.59 (+8.7%; the 1-week return in weekly_data.json: +9.0%)
- AMD: 476.67 → 477.57 (+0.2%; 1-week in the data: +2.6%)
- ANET: 201.09 → 193.78 (-3.6%; 1-week in the data: -0.8%)
- AVGO: 371.54 → 357.90 (-3.7%; 1-week in the data: -3.0%)

**AVGO earnings detail (Monday 2 September):** an extra yfinance query was run. The report came out on
2 September, and afterwards:
- 2 September (report day): 367.24 $ (-0.7%)
- 3 September: 357.16 $ (-2.7%) — a sharp fall
- 4 September: 357.90 $ (+0.2%) — a minimal recovery

A total decline of 2.7% after the report. From the headlines: "a decline after Q3", the Cramer warning.
The report may have met expectations, but the guidance or competitive worries disappointed the market.

### C. Thesis health check

**MU (1016.59 $, the 4 September close) — memory super-cycle / HBM leadership → VALID and STRENGTHENING**
Price >> 50d (938.26, +8.3% above it) >> 200d (606.34, +67.7% above it). **Last round (#6, 29 August)
the 50d status was unknown (a data gap) — this round it is confirmed with complete data: WELL above the
50d.** RSI 60.1 (healthy momentum). 1 week +9.0%, 1 month +15.8%, 3 months +7.1%. Stop 730 $ (+39.3%
away per REPORT.md — very comfortable). Earnings 30 September (portfolio.json and weekly_data.json
agree; 25 days out). Headlines: a first close above 1,000 $, David Tepper's second-biggest holding (he
is taking profit but keeps a large position), a buy signal. **The thesis is strengthening — it broke
the 50d, momentum is strong, and carrying the position into earnings is disciplined.**

**AMD (477.57 $) — AI accelerator / the NVDA alternative → WEAKENING (unchanged)**
Price < 50d (499.27, 4.3% below it), > 200d (341.0, +40.0% above it). **Last round the 50d status was
unknown — this round it is confirmed: still below the 50d.** RSI 49.7 (close to neutral, a slight
improvement from 47.4 last round). 1 week +2.6%, 1 month -1.2%, 3 months -2.6%. Stop 440 $ (+8.5% away
per REPORT.md — TIGHT, but above it on the weekly close). Earnings 3 November. Last round said
"reassess after NVDA's earnings" — NVDA's report passed on 26 August, AMD recovered slightly (+2.6% on
the week) but did not regain the 50d. Headlines: "EPS to double by 2027", "a buy opportunity after the
19% fall" — the fundamentals are strong but the technical momentum is weak. **The thesis is weakening:
below the 50d, the stop is tight. Not broken yet, but next week is critical. The 440 $ stop is
absolute — a breach means a mechanical sale.**

**ANET (193.78 $) — leader in AI data-center network hardware → VALID**
Price > 50d (182.93, +5.9% above it) >> 200d (151.94, +27.5% above it). RSI 53.2 (healthy). 1 week
-0.8%, 1 month +2.7%, 3 months +23.9%. Stop 160 $ (+21.1% away per REPORT.md — comfortable). Earnings
3 November. A minimal -0.8% weekly correction, holding the 50d support. Headlines: "up 37.3% in six
months, is there more room to grow?" — the valuation question is asked but the technicals are solid.
**The portfolio's steadiest position. The thesis holds and momentum is strong.**

**AVGO (357.90 $, half position) — custom AI chips / the networking front → BROKEN (and FELL AFTER
EARNINGS)**
Price << 50d (383.66, 6.7% below it), < 200d (369.03, 3.0% below it). **Last round (#6, 29 August) the
50d status was unknown — this round it is confirmed: below both the 50d and the 200d.** RSI 38.1 (weak,
worse than the 43.9 of last round). 1 week -3.0%, 1 month -16.3% (the portfolio's worst one-month
performance), 3 months -9.6%. Stop 350 $ (+2.3% away per REPORT.md — **VERY TIGHT, A CRITICAL ZONE!**).
The earnings report **PASSED on 2 September**, followed by a 2.7% decline (3 September: 357.16 $).
Headlines: "a decline after Q3", the Cramer warning ("someone must know something"), "is it too soon to
buy the dip?". Last round (#6, 29 August) said this: *"if the earnings guidance (2 September) is weak
and it approaches the stop — close fully."* → **Both conditions occurred: a post-earnings decline plus
a stop distance narrowed to +2.3%.** The CEO emphasises AI investment but the market was not convinced.
**The thesis is broken, the post-earnings decline confirmed it, and the stop is very tight — time to
close fully.**

### D. Decisions

#### DECISION 1: CLOSE — AVGO (close the remaining half entirely)

**Trade:** SELL 11.9571 shares of AVGO @ 357.90 $ → **+4,279 $ cash**

**Thesis (the reason for closing):** last round (#6, 29 August) warned explicitly: *"if the earnings
guidance (2 September) is weak and it approaches the stop — close fully."* Both conditions occurred:

1. **A post-earnings decline:** after the 2 September report the stock fell 2.7% (3 September:
   357.16 $). Headlines: "a decline after Q3", the Cramer warning ("someone must know something"), "is
   it too soon to buy the dip?". The report may have met expectations but the market was not convinced —
   guidance or competition worries persist.

2. **The stop distance is very tight:** stop 350 $, price 357.90 $ — only +2.3% away. One bad week (a
   2% fall) triggers the stop. It is 6.7% below the 50d (383.66) and 3.0% below the 200d (369.03). RSI
   38.1 (weak, worse than the 43.9 of last round). Momentum is entirely broken.

3. **The thesis is broken:** the custom AI chip theme ("AVGO's XPU leadership") was weakened by the
   Google-MRVL competition (round #5, 22 August). Last round (#6) I had hoped "earnings could come in
   strong and it could regain the 50d" — but the post-earnings decline refuted the thesis. The CEO
   emphasises AI investment (the headline about "Anthropic and OpenAI") but the market was not
   convinced. MRVL's guidance weakness (last round) could have been positive for AVGO (less
   competition), yet AVGO's own report disappointed the market too.

**The risk-management principle:** stop discipline says "close it if the weekly close breaches the
level", but **waiting for the stop to trigger in a broken-thesis position whose stop is only +2.3%
away mechanically enlarges the loss.** The thesis broke in #5 (22 August), #6 (29 August) waited for
the report, the post-earnings decline arrived (2 September) — there is no longer a reason to hold. Last
round I said "holding half preserves the positive scenario" — the positive scenario did not materialise.

**Loss:** entry: 23.9143 shares @ 418.16 $ (a 10,000 $ total cost).
- The first trim: 11.96 shares @ 368.45 $ (round #5, 22 August, a -594 $ loss)
- This sale: 11.9571 shares @ 357.90 $ → (357.90 - 418.16) × 11.9571 ≈ **a -721 $ loss**
**Total AVGO loss:** -594 - 721 = **-1,315 $ (-13.2% against the total entry).**

**New portfolio weights:** MU 34.4%, AMD 18.6%, ANET 15.4%, CASH 31.6% (31,421 $).

**The lesson:** when a thesis breaks (it broke in round #5), waiting for the earnings report was
legitimate (I halved the risk), but once the post-earnings decline arrived, exiting immediately is the
disciplined move. Holding on an expectation that "it could fall further" while the stop distance is
under +5% enlarges the loss. **Once a technical breakdown is confirmed after earnings: discipline, not
hope.**

#### DECISION 2: HOLD — MU, ANET

**MU:** the thesis holds and is strengthening. It broke the 50d (price 1016.59 $ > 50d 938.26 $), which
could not be checked last round because of the data gap — this round it is confirmed. A first close
above 1,000 $, David Tepper's second-biggest holding (he keeps a large position even while taking
profit), buy-signal headlines. RSI 60.1 (healthy), stop distance +39.3% (very comfortable). Earnings 30
September (25 days out) — carrying the position is disciplined. Stop 730 $ retained.

**ANET:** the portfolio's steadiest position. Holding the 50d support (price 193.78 $ > 50d 182.93 $),
RSI 53.2 (healthy), stop distance +21.1% (comfortable). The minimal -0.8% weekly correction is within
normal volatility. 3 months +23.9% — momentum is strong. Stop 160 $ retained.

**Exit plan:** stop levels unchanged (MU 730 $, ANET 160 $). A mechanical sale on a weekly close below
them.

**The signal that would show the thesis is wrong:**
- MU: if it loses the 50d before earnings (30 September) and approaches the stop (below 800 $).
- ANET: if it loses the 50d (182.93 $) and stays below it for three consecutive days — a momentum break
  signal.

#### DECISION 3: WATCH — AMD (one more round, the last chance)

**AMD:** below the 50d (price 477.57 $ < 50d 499.27 $, 4.3% below it), the stop tight (+8.5% away). Last
round (#6) the 50d status was unknown (a data gap) — this round it is confirmed: still below the 50d.
RSI 49.7 (close to neutral, a slight improvement from 47.4 last round). 1 week +2.6% (a mild recovery).
**But there is no stop breach yet and the fundamentals are strong:** headlines say "EPS to double by
2027", "a buy opportunity after the 19% fall".

**Decision:** watch one more round. **The last chance — the third "weakening" round.** Round #4 (15
August): "AMD → WEAKENING, it lost the 50d". Round #5 (22 August): "AMD → WEAKENING, it lost the 50d
again, reassess after NVDA's earnings". Round #6 (29 August): "AMD → WEAKENING, the 50d status is
unknown (a data gap)". **This round (#7): "AMD → WEAKENING, confirmed below the 50d."** Three
consecutive rounds of "weakening" — next round it either regains the 50d (the thesis survives) or the
stop triggers or I decide to trim. **Discipline: closing two positions in the same round (AVGO + AMD)
pushes the portfolio into excessive cash (~50%). I am giving AMD a last chance — but the stop is
absolute.**

**Risk:** the stop distance is tight (+8.5%). Another 8% weekly decline (≈440 $) triggers the stop.
NVDA's momentum is strong (I am entering NVDA below), which could add competitive pressure on AMD.
**If it does not regain the 50d next round, or approaches the stop (below 450 $), the position will be
trimmed or closed.**

**Why I am not trimming now:** (1) I closed AVGO; closing a second position in the same round pushes
the portfolio into excessive cash. (2) AMD's fundamentals are strong (the 2027 growth projection); only
the technical momentum is weak. (3) The stop has not been breached — stop discipline requires this. But
**this is the last chance; if there is no improvement next round I will act.**

**Exit plan:** stop 440 $ — a mechanical sale on a weekly close below it. If it does not regain the 50d
next round (12 September), or approaches the stop (below 450 $), trimming or closing fully will be
considered.

**The signal that would show the thesis is wrong:** (1) NVDA's momentum comes in very strong and AMD
takes no market share — the "NVDA alternative" thesis weakens. (2) The stop triggers before it regains
the 50d. (3) It stays below the 50d next round and the technical momentum weakens further.

#### DECISION 4: OPEN A NEW POSITION — NVDA

**Trade:** BUY NVDA, target weight 15% (a ~15,000 $ position)

**Cash arithmetic (after the AVGO sale):** 27,142 $ (existing) + 4,279 $ (the AVGO sale) = **31,421 $
of total cash**

**Position detail:**
- Target position: 15,000 $ / 230.36 $ ≈ **65.11 shares of NVDA @ 230.36 $**
- New cash: 31,421 $ - 15,000 $ = **16,421 $ (16.4% of the portfolio)**

**Thesis:** NVDA is the undisputed leader of the AI accelerator market. The momentum of its current
generation (the Blackwell architecture), a dominant share of data-center GPU demand, and a software
ecosystem lock-in (CUDA). AMD is positioned as the "alternative", but competition may take years to
catch NVDA's lead. SpaceX's "NVDA only" decision (the headline: "Elon Musk Committed SpaceX to Building
Exclusively on Nvidia") and the Hugging Face acquisition (the headline: "Here's the Real Reason Nvidia
Is Buying Hugging Face") strengthen its hold on the AI ecosystem.

**Technical picture:** price 230.36 $, 50d 210.57 $ (the price +9.4% above it), 200d 196.53 $ (the price
+17.2% above it). RSI 60.4 (healthy momentum, not overbought). 1 week +5.9%, 1 month +2.9%, 3 months
+10.4% — momentum is strong and steady. Earnings 17 November (73 days out) — the earnings rule is not a
problem (well over a week). Above the 50d and well above the 200d — the trend is strong.

**Why I am entering now:**
1. **The technicals are solid:** above the 50d and the 200d, RSI 60.4 (not overbought), momentum strong.
2. **The earnings rule is not a problem:** earnings are 73 days out (17 November), far more than a week.
3. **Opportunity cost:** I deferred NVDA in earlier rounds saying "wait for earnings" (#4, #5, #6). The
   report passed on 26 August and momentum is strengthening. Deferring further means losing the
   opportunity.
4. **Portfolio balance:** AVGO was closed and cash rose to 31.6%. The cash will not be held passively
   (the reminder in instruction section E). Entering NVDA raises beta without reducing the theme risk
   (still AI infrastructure).
5. **AMD risk:** AMD is weakening and may be closed next round. Entering NVDA strengthens the "AI
   accelerator" front with the leader.

**Risk:** NVDA's high valuation (elevated multiples) makes it sensitive to expectations. If the report
(17 November) misses, a sharp decline is possible. But momentum is strong and the technicals are solid —
the asymmetry favours us.

**Stop level:** 190 $ (on a weekly close basis). Price 230.36 $, stop distance +21.3% (comfortable).
10% below the 50d (210.57 $). If a weekly close comes in below 190 $, momentum has broken completely —
a mechanical sale.

**Exit plan:** stop 190 $ — a mechanical sale on a weekly close below it. Assess the technical picture
before the report (the week before 17 November, ~10 November): if it is above the 50d with strong
momentum, hold; if it has lost the 50d, or RSI is falling from overbought (>70), consider trimming.

**The signal that would show the thesis is wrong:**
- The guidance in the report (17 November) comes in weak and signals a slowdown in the AI spending
  cycle.
- It loses the 50d (210.57 $) and stays below it for three consecutive days — a momentum break signal.
- AMD or other competitors begin taking market share (NVDA's dominance weakens).

**New portfolio weights (after the NVDA entry):**
- MU: 34.4%
- AMD: 18.6%
- ANET: 15.4%
- NVDA: 15.1% (new)
- CASH: 16.4% (16,421 $)

#### DECISION 5: WATCHLIST — the deferral counter (the mandatory format)

Instruction section D: "every line in the watchlist section starts with `SYMBOL — deferred: N/3`."

**TSM — deferred: 1/3**
Price 428.91 $, 50d 420.41 $ (the price +2.0% above it), 200d 371.83 $ (the price +15.3% above it). RSI
56.8, 1 week +2.7%, 1 month +2.1%. **It broke the 50d!** Earlier rounds said "awaiting confirmation of a
turn" — this round it is above the 50d. Headlines: "Will Surge 22% Before 2026 Ends", "Japan, U.S.
advance $550B investment pact". Earnings 15 October (40 days out). **Why I am not entering this round:**
I entered NVDA (a 15% weight); opening two new positions at once spreads the portfolio too thin (each
stays at a small weight and contributes less to a 3-5x target). TSM has gained momentum — it can be
assessed next round. **The first deferral.**

**MRVL — deferred: 1/3**
Price 223.55 $, 50d 220.65 $ (the price +1.3% above it), 200d 151.71 $ (the price +47.4% above it). RSI
51.1, 1 week +3.2%, 1 month +2.2%, 3 months -22.6%. Above the 50d, with a recovery under way. But last
round's (#6) earnings result: "earnings strong but the 2028 guidance soft, a risk the Google deal
slips". This round's headline: "Marvell Raised Its Outlook but Fell as Google Chip Revenue Stayed
Distant" — it raised guidance but the Google revenue stayed distant. **Why I am not entering this
round:** the guidance uncertainty persists and there is a risk the Google deal slips. Entering NVDA
strengthened the AI chip front — there is no hurry with MRVL. It can be assessed next round if the
Google deal becomes clearer. **The first deferral.**

**SNDK — deferred: 1/3**
Price 1740.00 $, 50d 1550.25 $ (the price +12.2% above it), 200d 1003.97 $ (the price +73.3% above it).
RSI 61.2, 1 week +17.2%, 1 month +43.5%, 3 months +6.0%. **Added to the S&P 100**, hedge fund ownership
doubled. Headlines: "a buy signal". **But:** we sold on 8 August at 1212.21 $ (round #3, a -15.1% loss).
It is now 1740.00 $ — an early sale, a large opportunity missed (+43.5% in a month). **Why I am not
entering this round:** (1) I entered NVDA; opening two new positions at once spreads the portfolio too
thin. (2) RSI 61.2 — a hot zone; there may have been a buying wave after the S&P 100 inclusion, with
short-term pullback risk. (3) **The psychological load:** selling SNDK at 1212 $ and buying it back at
1740 $ means committing the early-sale error twice. Discipline: do not pay the market twice. If we see a
correction next round (say below 1600 $, a test of the 50d) it can be assessed. **The first deferral
(the first reassessment since the sale).**

**PLTR — DROP FROM LIST**
Price 174.33 $, RSI 54.2, 1 week -6.4%, 1 month +1.3%, 3 months +27.7%. Price >> 50d (149.89 $, +16.3%
above it). **Why I am dropping it:** earlier rounds repeatedly said "far too hot, RSI overbought, the
no-chasing rule". This round it fell 6.4% on the week and RSI eased to 54.2 — it is cooling. But 3
months +27.7% (still a hot zone). Headlines: "won a 127 million $ Army production order but fell 6%; has
the valuation finally caught up?" — valuation worries have begun. **PLTR does not have 3-5x potential**
(it has already done +27.7%) and its contribution to the portfolio is limited. Keeping it on the
watchlist creates an opportunity cost. I am dropping it.

**VRT — DROP FROM LIST**
Price 280.53 $, 50d 282.7 $ (the price 0.8% below it), RSI 54.9, 1 week +9.1%, 1 month +3.0%, 3 months
-6.6%. **Why I am dropping it:** earlier rounds repeatedly said "below the 50d, weak momentum, could be
dropped". This round there is a +9.1% weekly recovery but it has not quite reached the 50d (0.8% below
it). 3 months -6.6% — the long-term trend is weak. Headlines: "a utility agreement, AI data-center power
infrastructure", "a 1.45 bn $ AI power investment" — the story is interesting but the technicals are
weak. **VRT's momentum risk is high and its stop distance would be tight.** Keeping it on the watchlist
creates an opportunity cost. I am dropping it.

**Deferral status for the next round (12 September):**
- TSM: 2/3 (a second deferral) or open a position
- MRVL: 2/3 (a second deferral) or open a position
- SNDK: 2/3 (a second deferral) or open a position
**On the third deferral (3/3):** either open a position or drop it from the list. Waiting indefinitely
is forbidden (instruction section D).

### E. Theme risk

**Portfolio:** 4 positions (MU 34.4%, AMD 18.6%, ANET 15.4%, NVDA 15.1% — new) — all in the AI
infrastructure theme. 83.6% invested, 16.4% cash.

**The risk of falling together:** if the AI spending cycle breaks (mega-caps cutting capex, the AI
investment bubble bursting) every position falls together. That risk was accepted deliberately at the
outset — the price of an aggressive target (3-5x). **But this round AVGO was closed (a complete exit
from the custom AI chip front) and NVDA was added (the AI accelerator front strengthened with the
leader) — the theme concentration is unchanged but the quality was raised.** NVDA is the dominant
player; AVGO was wrestling with competitive risk.

**Portfolio composition detail:**
- Memory: MU (34.4%) — the HBM/DRAM super-cycle
- AI accelerators: AMD (18.6%, weakening) + NVDA (15.1%, new, the leader)
- Network hardware: ANET (15.4%) — the data-center network leader
**Diversification:** the three main fronts of AI infrastructure (memory, processors, networking) are
covered. But ALL THREE depend on the AI spending cycle — a break in the theme hits them together.

**Cash: NOT a protective cushion but buying power.** 16.4% cash (16,421 $) does not protect the
portfolio (an unleveraged virtual portfolio); it is powder for a decline. **What I am waiting for:** (1)
an opportunity to add to the existing positions (MU/ANET/NVDA) if they correct sharply. (2) If AMD is
closed next round, cash rises to ~37% — then an entry into one of TSM/MRVL/SNDK. (3) An unexpected
opportunity (SNDK falling to 1600 $, a test of the 50d). The cash will not be held passively; it is
HELD, waiting for an opportunity.

**Diversification assessment:** opening a position outside AI infrastructure (the mega-caps MSFT/GOOGL,
say) lowers the theme risk but also lowers beta (less contribution to a 3-5x target). The charter
permits it, but the AI theme remains the core strategy for now. **I accept the risk: an aggressive
target (3-5x) requires aggressive concentration.**

### F. Accounting for myself

**1. What did I say last round, and what did I do this round?**

**Last round (#6, 29 August):**

- **HOLD MU, ANET:** I held. **No departure.**

- **WATCH AMD:** "reassess after NVDA's earnings, hold as long as the stop holds" → NVDA's earnings
  passed (26 August), AMD recovered slightly (+2.6% on the week), the stop held. I held. **No
  departure.**

- **WATCH AVGO (the half position):** "wait for earnings, reassess if it falls below 360 $. If the
  earnings guidance (2 September) is weak and it approaches the stop — close fully." → The price is
  357.90 $ (it fell below 360 $), a 2.7% post-earnings decline, the stop distance narrowed to +2.3%.
  **I closed it. No departure — both conditions occurred and I acted as I said I would last round.**

- **NO NEW POSITIONS:** "opening a new position is risky because of the data gap; NVDA/TSM/MRVL can be
  assessed with complete data next round." → The data gap was resolved this round and I entered NVDA.
  **THERE IS A DEPARTURE (explained below).**

**THERE IS A DEPARTURE — I opened a new position (NVDA):**
Last round I said "no new positions because of the data gap". This round the data is complete and I
entered NVDA. **I am writing the departure down explicitly:** last round I said "NVDA can be assessed
with complete data next round" — this round complete data arrived and I assessed it. **This is not a
departure but the execution of a conditional plan.** Last round's reasoning: "entering without knowing
the 50d status means gambling." This round's reasoning: "above the 50d (230.36 $ > 210.57 $), the
technicals are solid, momentum is strong, earnings are 73 days out — the entry conditions are now met."
**No silent departure — last round I said "it can be assessed with complete data", and this round I
made that assessment and entered.**

**The AVGO closing decision — consistency with last round:**
Last round (#6, 29 August) I said: *"if the earnings guidance (2 September) is weak and it approaches
the stop — close fully."* Both conditions occurred:
1. A 2.7% post-earnings decline (the guidance did not convince the market)
2. The stop distance narrowed to +2.3% (it fell below 360 $)

I closed it. **No departure — the conditions I named last round occurred and I acted.** Last round I
said "the positive scenario is still possible; holding half preserves that possibility" — the positive
scenario did not materialise.

**2. Where last round's thesis turned out wrong:**

**The AVGO thesis:** "BROKEN — the Google-MRVL competition. Earnings could come in strong and it could
regain the 50d." → **I WAS WRONG.** A 2.7% post-earnings decline, it did not regain the 50d (still 6.7%
below it), and it lost the 200d too (3.0% below it). Last round I had hoped "the 100 bn $ debt deal shows
how serious the AI investment plan is, earnings could come in strong" — but the market was not
convinced. Cramer's "someone must know something" warning proved right. **Where I was wrong:** hoping
for a post-earnings recovery. The CEO emphasises AI investment (the Anthropic/OpenAI remarks) but the
market either finds the guidance weak or is pricing in the effect of the Google-MRVL competition. **The
lesson:** when a thesis breaks (it broke in round #5), waiting for the report was legitimate (I halved
the risk), but "earnings could come in strong" is a wish, not a thesis. Last round I violated my own
instructions: instruction section C says, *"'could recover', 'earnings may come in strong', 'the
positive scenario is still possible', 'I will wait and see' are forbidden — those are wishes, not
theses."* **Last round's reason for holding AVGO rested on exactly that kind of wish. I am not repeating
that error this round — the thesis broke, the report confirmed it, I closed it.**

**The early SNDK sale (round #3, 8 August) — still a regret:** we sold at 1212.21 $ and it is now
1740.00 $ (+43.5%). It was added to the S&P 100 and hedge fund ownership doubled. **Where I was wrong:**
I underestimated the speed of the NAND cycle's turn. I admitted this last round (#4): "NAND's volatility
runs both ways — fast on the way down and fast on the way back up." But this round I decided not to
re-enter SNDK (deferred 1/3). **Why?** (1) RSI 61.2 — a buying wave after the S&P 100 inclusion, with
short-term pullback risk. (2) The psychological load: sell at 1212 $, buy at 1740 $ — committing the
early-sale error twice. **Lesson calibration (a hypothesis, not yet a behaviour change):** the early
sale happened in SNDK; that does not become the lesson "all early sales are wrong". SNDK's thesis (the
NAND cycle) was highly volatile and I had kept the stop distance tight (+10.2%) — I mismeasured the
speed of the cycle. **But the early AVGO sale (this round) WAS RIGHT — a post-earnings decline, a tight
stop, a broken thesis.** I am not drawing the lesson "never sell early" from a single event. Every
position has its own thesis and its own stop discipline.

**THE DATA-GAP RISK (last round) — resolved this round:** last round (#6) I said "the 50d status is
unknown, I could be missing the warning". This round the data is complete and the 50d statuses are
confirmed. **Checking this round the positions I held last round (MU, AMD, ANET, AVGO):** MU is well
above the 50d (holding was right), AMD is confirmed below the 50d (weakening; I gave it a last chance),
ANET is above the 50d (holding was right), AVGO is confirmed below both the 50d and the 200d (I closed
it, the right call). **The "hold" decisions I made last round despite the data gap were confirmed this
round — only AVGO turned out to have deteriorated, and I closed it.**

**3. Where this round's decision could mislead me:**

**The decision to hold AMD (the last chance):** three consecutive rounds with the "weakening" label.
Last round "the 50d status was unknown", this round "confirmed below the 50d". The stop is tight
(+8.5%). **I have given it a last chance — next round it either regains the 50d or I act.** If AMD's
stop triggers next round or it deteriorates further, I could regret it: "I should have closed AMD
alongside AVGO this round." My reasons: (1) I closed AVGO; closing two positions in one round pushes the
portfolio into excessive cash. (2) AMD's fundamentals are strong (2027 EPS growth). (3) The stop has not
been breached. **But I accept the risk: if AMD deteriorates next round, my "last chance" decision will
have been wrong.**

**The decision to enter NVDA:** I said "above the 50d, momentum strong, 73 days to earnings". If NVDA
falls 10% next round (question marks over the AI spending cycle, say), I could regret it: "I closed
AVGO, cash was high, there was no need to rush." But **the opportunity-cost risk was greater:** I
deferred NVDA in earlier rounds saying "wait for earnings", the report passed on 26 August, and momentum
is strengthening (1 week +5.9%). Deferring further meant missing the opportunity. **I accept the risk:
the timing of the NVDA entry may be early, but discipline says "if the technicals are solid, earnings
are far off, and there is cash — enter".**

**The TSM / MRVL / SNDK deferral decision (1/3):** I said "not entering" for all three. If all three
gain 15% next round, I could regret it: "I could have entered TSM instead of NVDA, or opened two
positions." My reasons: (1) I entered NVDA; opening two new positions at once spreads the portfolio too
thin (each stays at a small weight). (2) TSM only just broke the 50d (awaiting confirmation), MRVL's
guidance is uncertain, SNDK's RSI is 61.2 (hot). **Discipline: open one new position per round and watch
the others. I have three rounds of deferral available.**

**The decision not to enter SNDK (the psychological load):** I said "sell at 1212 $, buy at 1740 $ —
committing the early-sale error twice". If SNDK gains another 30% in later rounds, I could regret it: "I
surrendered to the psychological load and behaved without discipline." But (1) RSI 61.2 (a buying wave
after the S&P 100 inclusion), (2) I have deferral room (1/3), (3) if I see a correction next round (a
test of the 50d, around 1550 $) I will assess it. **I accept the risk: I sold SNDK early, and not buying
it back now may be a second error — but chasing it at a high RSI would be a third.**

**Lesson calibration:**
- **Hypothesis (not yet a behaviour change):** the early AVGO sale was right (a post-earnings decline, a
  broken thesis). The early SNDK sale was wrong (I mismeasured the speed of the cycle). **The two events
  balance each other — I am drawing neither "sell early" nor "never sell". The lesson: when a thesis is
  broken, trimming or closing is disciplined; when it is not broken, waiting for the stop is
  disciplined.** AMD's thesis is weakening but not broken — I am waiting for the stop. AVGO's thesis was
  broken and the report confirmed it — I closed it.

- **A behaviour change (two independent observations, the same direction):** (1) the early SNDK sale
  (round #3), (2) AVGO trim-wait-close (rounds #5, #6, #7). **In both positions I acted once the stop
  distance was tight.** In SNDK I cut at a 15% loss with the stop +10.2% away — the market turned and
  the loss became a +43% move I missed. In AVGO I cut half at an 11% loss with the stop +5.3% away
  (round #5) — it deteriorated further after earnings, and I cut the rest with the stop +2.3% away
  (round #7). **What they share: in both the stop was kept tight and I acted early.** But SNDK had a
  cycle turn and AVGO had a post-earnings decline. **The lesson (not yet clear; one more round of
  observation is needed):** if the stop distance is under +5% and the thesis is broken (as with AVGO) —
  cut. If the stop distance is over +10% and the thesis is cyclical (as with SNDK) — wait; a cycle turn
  is possible. **But this is still a hypothesis — if AMD approaches its stop next round (under +5%) I
  will test this lesson.**

**Next review:** 12 September 2026 (Saturday — the next weekly round). **CRITICAL:** AMD's 50d status
(did it regain it, or move further away?) and its stop distance (how close to 440 $?). NVDA's first week
(is it above the 50d?). TSM / MRVL / SNDK deferral (2/3 or an entry). MU/ANET stop checks.

---

## #8 — 2026-09-12 · WEEKLY ROUND

**Market context:** semiconductors were mixed on the week. The portfolio was -0.97% (0.06% behind SPY, 0.28% ahead of SMH). The AI infrastructure theme is steady, with a recovery visible in memory and accelerators.

### A. Data status

Data was fetched in full for 10/10 symbols (based on the Friday 11 September 2026 close). Price, 50/200d SMA, RSI, return data and earnings dates are present for every position. **No missing fields.**

**Data-integrity gate check:** the `last_price` and `sma50` fields were checked one by one for every position and every watchlist symbol assessed (instruction step 3). Every field is populated. `_meta.missing_data` = [] (empty). No need for an extra yfinance query was identified.

**News scan:** 50 headlines in total across 10 symbols. Worth noting:

- **MU:** "Is Micron Stock the Next Nvidia? The Answer May Shock Investors." — analyst pieces comparing Micron with Nvidia. "Billionaire Stanley Druckenmiller Dumped Broadcom, Intel, and Micron for This Chip Stock." — Druckenmiller reduced MU (a negative signal). "Why Micron Stock Is on Pace for a Weekly Decline" — a weekly decline.

- **AMD:** "AMD's CFO, Jean Hu, Just Announced Fantastic News for Investors" — **positive news from the CFO; this matters a great deal!** "TSM's Record Month Confirms AMD's AI Ramp, but Its Pricing Power Could Take Some of the Upside Back" — TSM's record month confirms AMD's AI ramp.

- **SNDK:** "Storage Stocks Slide as Profit Taking Follows Big Run: Seagate Falls 4%, SanDisk Drops 3%, Micron Holds Flat" — profit-taking continues; SNDK fell 3%.

- **NVDA:** "SpaceX signs $1.1 billion-per month computing deal" — a large deal. "Nvidia CEO Jensen Huang just doubled down on his big 2030 prediction" — a message of confidence from the CEO.

- **TSM:** "David Tepper makes surprising double bet on AI's biggest bottleneck" — Tepper making a large bet on TSM. "TSM Just Posted Record Sales. Nvidia May Be Both the Winner and the One Paying for It" — record sales.

- **MRVL:** "Marvell CEO reveals decade-long gem behind its explosive 239% surge" — the CEO setting out the long-term strategy.

### B. The cause of the move

No position moved more than ±10% on the week (MU -4.1%, AMD +8.1%, ANET +3.0%, NVDA -5.2%). No move requires special investigation.

### C. Thesis health check

**MU (975.26 $, Friday 11 September) — memory super-cycle / HBM leadership → VALID**
Price > 50d (928.61, +5.0% above it) >> 200d (621.93, +56.8% above it). RSI 53.0 (healthy). 1 week +1.8%, 1 month +2.7%, 3 months -0.6%. Stop 730 $ (+33.6% away, very comfortable). Earnings 30 September (weekly_data.json, a Wednesday, 18 days out). Headlines: Druckenmiller reduced MU (a negative signal) but analyst interest continues ("Is Micron Stock the Next Nvidia?"). A -4.1% week is within normal volatility. It is holding the 50d support and momentum is stable. **The thesis holds and the stop is comfortable.**

**AMD (516.13 $) — AI accelerator / the NVDA alternative → VALID (upgraded from WEAKENING!)**
Price > 50d (496.55, +3.9% above it) >> 200d (346.91, +48.8% above it). **A CRITICAL DEVELOPMENT: it regained the 50d!** Last round (#7, 5 September) it was 477.57 $ < 499.27 (below the 50d) and a "last chance" warning was issued. This round it is 516.13 $ > 496.55 $ (+3.9% above it) — it regained the 50d. RSI 58.0 (strong momentum, up from 49.7 last round). 1 week +13.1% (**a very strong week!**), 1 month +6.9%, 3 months +0.9%. Stop 440 $ (+17.3% away, back in comfortable territory from the tight +8.5% of last round). Earnings 3 November (a Tuesday). Headline: **"AMD's CFO, Jean Hu, Just Announced Fantastic News for Investors"** — positive news from the CFO, which strengthens the thesis. "TSM's Record Month Confirms AMD's AI Ramp" — the AI ramp is confirmed. **Last round (#7) I said "last chance": "next round it either regains the 50d or I act." It regained the 50d — the thesis survived!** Rounds #5, #6 and #7 carried the WEAKENING label three times in a row — this round the action came (the 50d was regained) and the label changed. **The thesis is upgraded to VALID.**

**ANET (199.59 $) — leader in AI data-center network hardware → VALID**
Price > 50d (185.3, +7.7% above it) >> 200d (153.4, +30.1% above it). RSI 57.1 (healthy). 1 week +4.3%, 1 month -2.0%, 3 months +22.3%. Stop 160 $ (+24.7% away, comfortable). Earnings 3 November (a Tuesday). **The portfolio's steadiest position.** A +4.3% week is a show of strength. It is holding the 50d support and momentum is strong. **The thesis holds.**

**NVDA (218.29 $) — AI accelerator leadership → VALID but down in its first week**
Price > 50d (212.36, +2.8% above it) >> 200d (197.11, +10.7% above it). RSI 49.9 (neutral, down from 60.4 last round). 1 week -4.3%, 1 month -3.0%, 3 months +6.5%. Stop 190 $ (+14.9% away, comfortable but narrower than last round's +21.3%). Earnings 17 November (a Tuesday, 66 days out). It was opened last round (#7) at 230.36 $ and is now 218.29 $ (a -5.2% fall, a first-week loss). Headlines: "SpaceX signs $1.1 billion-per month computing deal" — a large deal, positive. "Nvidia CEO Jensen Huang just doubled down on his big 2030 prediction" — a message of confidence from the CEO. **It is holding the 50d support but momentum has weakened (RSI 60.4 → 49.9). The first-week fall is a disappointment but the technicals are not broken yet.** The stop distance narrowed (+21.3% → +14.9%) but is not yet at a critical level. **The thesis holds but must be watched next round: a warning if it loses the 50d or approaches the stop (below 200 $).**

### D. Decisions

#### DECISION 1: HOLD — MU, AMD, ANET, NVDA

**MU:** holding the 50d support, the stop distance very comfortable (+33.6%), earnings 18 days out (30 September). A -4.1% week is normal. Druckenmiller's reduction is negative, but analyst interest ("Is Micron Stock the Next Nvidia?") supports the thesis. Stop 730 $ retained.

**AMD:** **it regained the 50d!** I had issued a "last chance" warning last round — this round it met the condition. A +13.1% week is very strong, the CFO's news is positive, and TSM's record month confirms the AI ramp. RSI 58.0 (strong momentum) and the stop distance is back in comfortable territory (+17.3%, from last round's tight +8.5%). **The thesis is upgraded from WEAKENING to VALID.** Stop 440 $ retained.

**ANET:** the portfolio's steadiest position. +4.3% on the week, holding the 50d support, momentum strong. Stop 160 $ retained (+24.7% away).

**NVDA:** the -5.2% first week is a disappointment but it is holding the 50d support (+2.8% above it). The SpaceX 1.1 bn $ deal and the CEO's message of confidence support the thesis. The stop distance narrowed (+21.3% → +14.9%) but is not yet critical. **Must be watched next round: a warning if it loses the 50d or approaches the stop (below 200 $).** Stop 190 $ retained.

**Exit plan:** stop levels unchanged (MU 730 $, AMD 440 $, ANET 160 $, NVDA 190 $). A mechanical sale on a weekly close below them.

**The signal that would show the thesis is wrong:**
- MU: if it loses the 50d before earnings (30 September) and approaches the stop (below 800 $).
- AMD: if it loses the 50d (496.55 $) again and stays below it for three consecutive days — a momentum break signal.
- ANET: if it loses the 50d (185.3 $) — a momentum break signal.
- NVDA: if it loses the 50d (212.36 $) and stays below it for three consecutive days, or approaches the stop (below 200 $) — that would mean the first month's momentum failed.

#### DECISION 2: NO NEW POSITIONS (the deferral counter: every threshold-reached symbol dropped from the list)

**Cash:** 16,421 $ (16.4% of the portfolio, per REPORT.md).

**Deferral counter status (from the counters.py output in REPORT.md):**
- **SNDK: 4/3** (THRESHOLD REACHED)
- **TSM: 7/3** (THRESHOLD REACHED)
- **MRVL: 7/3** (THRESHOLD REACHED)
- **MSFT: 7/3** (THRESHOLD REACHED)
- **GOOGL: 7/3** (THRESHOLD REACHED)

Instruction section D is explicit: "for every symbol the table marks 'THRESHOLD REACHED', there are two options this round: open a position, or drop the symbol from the list." There is no third option; waiting indefinitely is forbidden.

**Assessment and decisions (for each symbol separately):**

**1. SNDK (1633.35 $, 4/3 THRESHOLD REACHED) — DROP FROM LIST**
Price > 50d (1517.87, +7.6% above it), RSI 53.6, 1 week +5.0%, 1 month +6.9%. The technicals are solid. But the headline: "Storage Stocks Slide as Profit Taking Follows Big Run: SanDisk Drops 3%" — profit-taking continues. Last round (#7) I said "deferred 1/3" but counters.py shows 4/3 — it has been deferred far longer (I started the counter wrongly in round #7, as noted in the version 7 rationale). **Why I am not entering this round:** (1) I sold at 1212.21 $ on 8 August (round #3, an early sale, a +43.5% opportunity missed). It is now 1633.35 $ (down 6.1% from last round's 1740 $). The psychological-load reasoning was stale, but the 4/3 threshold has been badly overshot — deferring this long scatters the portfolio's focus. (2) Cash is 16.4% — I can open one position (~10% weight). TSM would be more strategic than SNDK (the fabrication leader, manufacturing every AI chip). **Decision: DROP FROM LIST.**

**2. TSM (433.24 $, 7/3 THRESHOLD REACHED) — DROP FROM LIST**
Price > 50d (418.93, +3.4% above it) >> 200d (374.99, +15.5% above it). RSI 56.9, 1 week +3.9%, 1 month +0.6%, 3 months +2.2%. The technicals are solid and momentum is steady. Headlines: "David Tepper makes surprising double bet on AI's biggest bottleneck" — Tepper making a large bet on TSM. "TSM Just Posted Record Sales." — record sales. Earnings 15 October (a Thursday, 33 days out). **The 7/3 threshold has been badly overshot and opening a position looks reasonable. BUT:** (1) Cash is 16.4% — I can open one position (~10% weight). Opening TSM takes on the risk of AMD's escape from "last chance" (if AMD weakens again there is no cash). (2) **Portfolio balance:** MU 34.4% (memory), AMD 18.6% + NVDA 15.1% = 33.7% (AI accelerators), ANET 15.4% (networking). Adding TSM adds the "fabrication" front, but the portfolio already has indirect TSM exposure within the AI infrastructure theme (NVDA and AMD all buy from TSM). (3) **The 3-5x target:** TSM is steady but a large company with low beta. 3 months +2.2% — slow growth. AMD did +13.1% on the week (far more dynamic). TSM's contribution to the portfolio's aggressive target may be limited. **Decision: DROP FROM LIST.** The reason: the 7/3 threshold has been badly overshot, but in the context of portfolio balance and the aggressive target, preserving cash is more strategic than adding TSM. AMD regaining the 50d strengthened the portfolio's accelerator front — waiting for an opportunity to add to the existing positions (AMD, NVDA, MU) is more disciplined than an extra position.

**3. MRVL (236.10 $, 7/3 THRESHOLD REACHED) — DROP FROM LIST**
Price > 50d (216.84, +8.9% above it) >> 200d (154.76, +52.6% above it). RSI 55.5, 1 week +13.1% (**very strong!**), 1 month +6.3%, 3 months -15.6%. The technicals are very strong. Headline: "Marvell CEO reveals decade-long gem behind its explosive 239% surge" — the CEO setting out the long-term strategy. Earnings 1 December (a Tuesday, 80 days out). **The 7/3 threshold has been badly overshot and the technicals are very strong (+13.1% on the week) — why am I not entering?** (1) Earlier rounds carried the worry that "the Google deal may slip" (the earnings result in round #6 was soft). This round there is a +13.1% weekly recovery — the Google worry may have eased. BUT (2) cash is 16.4% — I can open one position. MRVL vs TSM: both are strong. But (3) **the risk of a portfolio-balance error:** MRVL is custom AI chips — that is precisely why I closed AVGO (the Google-MRVL competition, rounds #5-#7). Entering MRVL means returning to the front I exited. TSM is fabrication (a different front) but I dropped that too (for the reasons above). **Decision: DROP FROM LIST.** The reason: the technicals are very strong but the 7/3 threshold has been badly overshot, the Google deal remains uncertain (a soft report last round), and custom AI chips are a competitive field (the reason I closed AVGO). The current portfolio (AMD regained the 50d, NVDA is new) covers the AI accelerator front — adding MRVL brings no theme diversity and consumes cash.

**4. MSFT (495.63 $, 7/3 THRESHOLD REACHED) — DROP FROM LIST**
Price > 50d (453.12, +9.4% above it) >> 200d (429.65, +15.4% above it). RSI 56.9, 1 week -2.8%, 1 month -0.1%, 3 months +27.1%. The technicals are strong (well above the 50d, 3 months +27.1%). **Why I am not entering:** (1) The charter: "US large-cap technology plus semiconductor / AI infrastructure." MSFT is a mega-cap in cloud/platform — not AI infrastructure. (2) **Low beta, limited contribution to a 3-5x target.** 3 months +27.1% is strong but normal for a company this size. Its contribution to the portfolio's aggressive target (3-5x) is far lower than the semiconductors (MU, AMD, NVDA). (3) The 7/3 threshold has been badly overshot — why was it deferred so long? Because MSFT did not fit the portfolio's theme. **Decision: DROP FROM LIST.** The reason: a mega-cap, low beta, outside the AI infrastructure theme. Limited contribution to a 3-5x target.

**5. GOOGL (338.50 $, 7/3 THRESHOLD REACHED) — DROP FROM LIST**
Price < 50d (346.98, 2.4% below it), 200d (336.38, +0.6% above it). RSI 46.9 (weak). 1 week -1.1%, 1 month -2.2%, 3 months -5.8%. **The technicals are weak: below the 50d, RSI weak, momentum negative.** Earnings 28 October (a Wednesday). **Why I am not entering:** (1) Below the 50d — momentum broken. (2) The charter: "US large-cap technology plus semiconductor / AI infrastructure." GOOGL is a mega-cap in cloud/AI platforms but not AI infrastructure. (3) Limited contribution to a 3-5x target (the same reasoning as MSFT). **Decision: DROP FROM LIST.** The reason: below the 50d (weak technicals), a mega-cap (low beta), outside the AI infrastructure theme.

**Why I opened no position in any of them — the overall reasoning:**
Cash is 16.4% — I can open one position (~10% weight, 10,000 $). None of the five threshold-reached symbols offered a strong enough case in the context of the portfolio's current state and its target:
- SNDK: the technicals are solid but 4/3 is badly overshot, there is the psychological load (the early sale), and profit-taking headlines.
- TSM: the technicals are solid but 7/3 is badly overshot, beta is low, and the portfolio already has indirect TSM exposure (NVDA/AMD).
- MRVL: the technicals are very strong but 7/3 is badly overshot, the Google deal is uncertain, and custom AI chips are competitive (the reason I closed AVGO).
- MSFT and GOOGL: mega-caps, outside the AI infrastructure theme, low beta, limited contribution to a 3-5x target.

**An alternative approach considered:** one could argue "if you are not opening a position in any of them, keep watching the strongest one or two and drop the rest". But instruction section D is explicit: "threshold reached? Open a position or drop it from the list; there is no third option." Telling a threshold-reached symbol "watch one more round" is indefinite deferral and is forbidden. **I dropped all five from the list because I could not find sufficient reason to open a position in any of them.**

**Cash strategy:** the 16.4% cash (16,421 $) will not be held passively (instruction section E). **What I am waiting for:** (1) an opportunity to add to the existing positions (MU, AMD, ANET, NVDA) if they correct sharply — especially AMD (it regained the 50d, momentum strong) and MU (earnings 18 days out, a correction may present an opportunity). (2) If NVDA loses the 50d next round or approaches the stop (below 200 $), the cash is there and an alternative position (strengthening AMD) can be assessed. (3) An unexpected opportunity (a fresh screen surfacing a new strong symbol). The cash is powder, ready for an opportunity in a decline.

### E. Theme risk

**Portfolio:** 4 positions (MU 33.1%, AMD 20.1%, ANET 15.9%, NVDA 14.4%, weights per REPORT.md) — all in the AI infrastructure theme. 83.6% invested, 16.4% cash.

**The risk of falling together:** if the AI spending cycle breaks (mega-caps cutting capex, the AI investment bubble bursting) every position falls together. That risk was accepted deliberately at the outset — the price of an aggressive target (3-5x). **This round TSM / MRVL / MSFT / GOOGL were dropped from the list — an opportunity to broaden the theme was passed up, but the theme concentration was preserved.** The reasons: (1) The TSM / MRVL thresholds were badly overshot (7/3), and deferring that long is itself a signal that they were off-theme. (2) MSFT / GOOGL are mega-caps with low beta and limited contribution to a 3-5x target. (3) The current portfolio (AMD regained the 50d plus a new NVDA) strengthened the AI accelerator front — preserving cash for a correction opportunity is more strategic than an extra position.

**Portfolio composition detail:**
- Memory: MU (33.1%) — the HBM/DRAM super-cycle, the portfolio's largest weight
- AI accelerators: AMD (20.1%, regained the 50d) + NVDA (14.4%, new, the leader) = 34.5% — the portfolio's second-largest group
- Network hardware: ANET (15.9%) — the data-center network leader, the steadiest position
**Total invested:** 83.6% (cash 16.4%).

**Diversification:** the three main fronts of AI infrastructure (memory, processors, networking) are covered. But ALL THREE depend on the AI spending cycle — a break in the theme hits them together. **I accept the risk: an aggressive target (3-5x) requires aggressive concentration.** TSM/MRVL/MSFT/GOOGL were dropped because a strategy of theme depth (an opportunity to add to the existing positions) was chosen over theme breadth.

**Cash: NOT a protective cushion but buying power.** The 16.4% cash (16,421 $) does not protect the portfolio (an unleveraged virtual portfolio); it is powder for a decline. It is waiting for a correction opportunity in the existing positions (especially strengthening AMD, or a pre-earnings correction in MU). If NVDA weakens next round (losing the 50d, approaching the stop), the cash is ready for an alternative action.

### F. Accounting for myself

**1. What did I say last round, and what did I do this round?**

**Last round (#7, 5 September):**

- **HOLD MU, ANET:** I held. **No departure.**

- **WATCH AMD (the last chance):** "it either regains the 50d, or the stop triggers, or I decide to trim." → AMD regained the 50d (516.13 $ > 496.55 $), +13.1% on the week, positive news from the CFO. I held and **upgraded the thesis label from WEAKENING to VALID.** **No departure — last round's "last chance" condition was met this round and I acted as I said.**

- **HOLD NVDA:** I held. It fell 5.2% in its first week but is holding the 50d support. **No departure.**

- **CLOSE AVGO (fully):** closed last round. It is not in the portfolio this round. **No departure.**

- **Watchlist (TSM, MRVL, SNDK):** last round I said "deferred 1/3". This round I learned from counters.py that SNDK is 4/3, TSM 7/3 and MRVL 7/3 — **I started the counter wrongly last round (noted in the version 7 rationale).** This round I used the correct counters and **dropped all five threshold-reached symbols (SNDK, TSM, MRVL, MSFT, GOOGL) from the list.** **THERE IS A DEPARTURE (explained below).**

**THERE IS A DEPARTURE — the watchlist:**
Last round (#7) I said "deferred 1/3 (the first deferral)" for TSM, MRVL and SNDK. This round the counters.py output reads SNDK 4/3, TSM 7/3, MRVL 7/3 — all THRESHOLD REACHED. **I am writing the departure down explicitly:** I started the counter wrongly last round (I said 1/3 when it was 4/3 and 7/3). The version 7 rationale names exactly this error: "round #7 wrote the counter in the right format but started it at 1/3 — when TSM, MRVL and SNDK had been deferred for rounds." This round I took the correct counters from counters.py and **dropped every threshold-reached symbol (five of them) from the list.** Last round I said "deferral status for the next round (12 September): TSM 2/3 or open a position, MRVL 2/3 or open a position, SNDK 2/3 or open a position" — but because the real counters were 4/3 and 7/3, the "open a position or drop it" rule applied this round. **I opened a position in none of them and dropped them all.** The reasons are above (section D2).

**2. Where last round's thesis turned out wrong:**

**The AMD thesis:** last round (#7) "WEAKENING — the last chance; next round it either regains the 50d or I act." → **IT TURNED OUT RIGHT.** AMD regained the 50d (477.57 $ < 499.27 → 516.13 $ > 496.55 $), +13.1% on the week, positive news from the CFO. **I was not wrong — I set the "last chance" condition correctly last round and it was met this round.** The thesis was upgraded from WEAKENING to VALID. **The lesson: the "last chance" warning worked — giving AMD one more round was right (to avoid closing two positions in the same round as AVGO). AMD's fundamentals were strong (2027 EPS growth) and only the technical momentum was weak — this round the technicals recovered too.**

**NVDA's first-week performance:** last round (#7) I opened it at 230.36 $ saying "above the 50d, momentum strong, 73 days to earnings". This round it is 218.29 $ (a -5.2% fall, a first-week loss). **Where I was wrong:** the assumption that "the first week's performance will be strong". NVDA is still above the 50d (+2.8%) but momentum has weakened (RSI 60.4 → 49.9) and the stop distance narrowed (+21.3% → +14.9%). The first-week fall is a disappointment. **Cause investigation (not required under section B since -5.2% < 10%, but noted anyway):** NVDA's -4.3% week (weekly_data.json) may be part of a general AI accelerator correction — AMD did +13.1% (strong) while NVDA did -4.3% (weak). Most likely short-term profit-taking, or a market reaction sensitive to NVDA's high valuation (its multiples). **What I learned: the first-week performance of a new position is not predictable — even with solid technicals (above the 50d) a short-term correction can arrive. NVDA's thesis (AI accelerator leadership) still holds, but the first month must be watched.**

**The TSM / MRVL / SNDK deferral counter:** last round I said "deferred 1/3"; this round counters.py reads SNDK 4/3, TSM 7/3, MRVL 7/3 — **they had been deferred far longer and I started the counter wrongly.** This is named in the version 7 rationale. **Where I was wrong:** I violated the ban on producing the deferral counter myself (last round I counted "the first deferral" myself instead of reading REPORT.md). This round I did it right: I took it from counters.py. **The lesson: apply instruction section D to the letter — "you do not produce the number, you read it from REPORT.md." Last round I violated that clause.**

**3. Where this round's decision could mislead me:**

**The decision to drop all five threshold-reached symbols:** SNDK (4/3), TSM (7/3), MRVL (7/3), MSFT (7/3), GOOGL (7/3) — I dropped them all. If one of them (especially TSM or MRVL, whose technicals are strong) gains 30% in later rounds, I could regret it: "instead of dropping the threshold-reached symbols I should at least have opened a position in TSM." **My reasoning:** (1) Cash is 16.4% — I can open one position. None of the five offered a strong enough case in the context of the portfolio's state and target (the detailed reasons are in section D2). (2) Telling a threshold-reached symbol "watch one more round" is indefinite deferral and instruction section D forbids it. **I accept the risk: dropping the threshold-reached symbols may mean missing technically strong names like TSM/MRVL. But preserving the portfolio's focus (AMD regained the 50d, the cash is ready for a correction opportunity) is more strategic.**

**The decision to hold NVDA (a -5.2% first week):** I said "it is holding the 50d support but momentum has weakened; it must be watched next round". If NVDA falls another 10% next round (losing the 50d, down to around 200 $), I could regret it: "the first-week fall was the warning; I should have trimmed this round." My reasoning: (1) NVDA is still above the 50d (+2.8%) and the stop distance is comfortable (+14.9%, not yet critical). (2) The SpaceX 1.1 bn $ deal and the CEO's message of confidence support the thesis. (3) A first-week fall can be a normal correction (profit-taking). **I accept the risk: NVDA's momentum has weakened, and a warning follows next round if it loses the 50d or approaches the stop. But trimming now would be a panic sale on one week of correction.**

**The decision to upgrade AMD's thesis label to VALID:** WEAKENING last round, VALID this round (it regained the 50d). If AMD loses the 50d again next round, I could regret it: "I upgraded to VALID far too early; I should have held WEAKENING for another round or two." My reasoning: (1) Last round I said "the last chance — next round it either regains the 50d or I act." AMD met the condition (it regained the 50d, +13.1% on the week, positive CFO news). (2) Instruction section C: "if you are writing the same label for the third round in a row on the same position, something must change in that round: either the action or the label." Rounds #5, #6 and #7 were WEAKENING three times — this round (#8) the action came (the 50d was regained) and the label changed. **I accept the risk: AMD may weaken again. But last round's "last chance" condition was met this round, and upgrading the label is disciplined.**

**The decision to preserve 16.4% cash (opening no new position):** if the market gains 15% in later rounds while I sat on 16.4% cash, I could regret it: "I should have opened a position in TSM or MRVL; holding cash passively is an opportunity cost." My reasoning: (1) Instruction section E: "the cash will not be held passively; it is buying power in a decline." But the cash is HELD, waiting for a correction opportunity (adding to the existing positions — especially strengthening AMD, or a pre-earnings correction in MU). (2) None of the threshold-reached symbols offered a strong enough case (the detailed reasons are in section D2). **I accept the risk: preserving cash may mean missing an upside opportunity. But the current portfolio (AMD regained the 50d plus a new NVDA) is dynamic enough — the cash is more strategic held for a decline.**

**Lesson calibration:**
- **A behaviour change (two independent observations, the same direction):** (1) The AMD "last chance" warning (round #7), with the condition met (round #8). (2) AVGO trim-wait-close (rounds #5, #6, #7), with the post-earnings decline. **In both positions the "conditional action" plan worked.** Giving AMD one more round was right (the fundamentals were strong); waiting for AVGO's report and then closing was right (the thesis was broken). **The lesson: if a position is weakening but the fundamentals are strong (like AMD), issue a "last chance" warning and watch one more round. If the thesis is broken (like AVGO), make a conditional plan (wait for the report) and cut as soon as the condition occurs. Do not conflate the two cases.**

- **Hypothesis (not yet a behaviour change):** the first-week performance of a new position is not predictable (NVDA -5.2%). But this is a single event — NVDA's first month will be watched in coming rounds. If NVDA is still holding the 50d and recovering a month from now, the first-week fall was only a short-term correction. **The lesson (not yet clear): after opening a new position, watch the first 2-3 weeks; a warning if it loses the 50d or approaches the stop. A first-week fall can be normal, but losing the 50d two weeks in a row may be a trim signal.**

**Next review:** 19 September 2026 (Saturday — the next weekly round). **CRITICAL:** NVDA's 50d status (regained or lost?) and its stop distance (how close to 200 $?). Whether AMD is holding the 50d (if it loses it again, the thesis drops from VALID to WEAKENING). MU's earnings are approaching (30 September, 11 days out — a check the week before). Whether ANET's momentum continues. The cash is waiting for a correction opportunity.

---

## #9 — 2026-09-19 · WEEKLY ROUND

**Market context:** the AI infrastructure theme is in a steady recovery trend. The portfolio was +2.32% (3.57% ahead of SPY, 2.79% ahead of SMH). Semiconductors and AI accelerators posted a strong week.

### A. Data status

Data was fetched in full for 10/10 symbols (based on the Friday 18 September 2026 close). Price, 50/200d SMA, RSI, return data and earnings dates are present for every position. **No missing fields.**

**Data-integrity gate check:** the `last_price` and `sma50` fields were checked one by one for every position (instruction step 3). Every field is populated:
- MU: last_price=1015.8 OK, sma50=927.26 OK
- AMD: last_price=559.82 OK, sma50=495.85 OK
- ANET: last_price=199.39 OK, sma50=187.53 OK
- NVDA: last_price=222.27 OK, sma50=214.07 OK

`_meta.missing_data` = [] (empty). No need for an extra yfinance query was identified.

**News scan:** 50 headlines in total across 10 symbols. Worth noting:

- **MU:** "What Does Micron Technology (MU) Warning Of Shortages Through 2027 Mean?" — a warning of supply shortages through 2027. "Nvidia, SK Hynix send strong signal to Micron investors" — positive signals from NVDA and SK Hynix. "UBS now expects AI capex to reach nearly $1tn this year and around $1.4tn by 2027" — AI investment is growing.

- **AMD:** "Dow Jones Futures: Nasdaq, S&P 500 Hold; Robinhood, Sandisk, AMD, Moderna Surge Into Buy Areas" — AMD is in a buy area. "AMD (AMD) Stock Looks Cheap After Its Huge 3 Year Run" — the valuation looks cheap after a three-year run. "Chip Stocks Break Through Ceiling As Sector Rebounds. Macom Is A Standout." — the semiconductor sector is breaking through.

- **ANET:** "Arista Networks (ANET) Raises Full Year Outlook As AI Data Center Demand Stays Strong" — **ANET raised its full-year outlook; AI data-center demand is strong!**

- **NVDA:** general market news, nothing company-specific. Momentum is steady.

- **SNDK:** "Sandisk Joins the S&P 100 on Monday -- the Same Day Nike Leaves It" — added to the S&P 100. "Dow Jones Futures: Nasdaq, S&P 500 Hold; Robinhood, Sandisk, AMD, Moderna Surge Into Buy Areas" — in a buy area.

### B. The cause of the move

No position moved more than ±10% on the week (MU +4.2%, AMD +8.5%, ANET -0.1%, NVDA +1.8%). No move requires special investigation.

### C. Thesis health check

**MU (1015.80 $, Friday 18 September) — memory super-cycle / HBM leadership → VALID and STRONG**
Price > 50d (927.26, +9.6% above it) >> 200d (640.02, +58.7% above it). RSI 58.3 (healthy momentum). 1 week +4.2%, 1 month +4.3%, 3 months -16.1%. Stop 730 $ (+39.2% away, very comfortable). Earnings 30 September (weekly_data.json, a Wednesday, 11 days out). Headlines: "a warning of supply shortages through 2027" — a shortage means price support. "Positive signals from NVDA and SK Hynix" — the main customers are strong. "UBS: AI capex $1tn this year, $1.4tn by 2027" — the AI investment cycle is growing and memory demand is strong. A +4.2% week is a healthy recovery (last round was a -4.1% fall). It is holding the 50d support (+9.6% above it) and momentum is steady. **The thesis holds and is strong; earnings are 11 days out — to be watched.**

**AMD (559.82 $) — AI accelerator / the NVDA alternative → VALID and STRONG**
Price > 50d (495.85, +12.9% above it) >> 200d (354.62, +57.9% above it). **It is holding the 50d and widening the gap!** Last round (#8) it had regained the 50d (516.13 $ > 496.55 $, +3.9% above it); this round it strengthened further (559.82 $ > 495.85 $, +12.9% above it). RSI 65.4 (strong momentum, up from 58.0 last round). 1 week +8.5% (**a very strong week!**), 1 month +19.2% (**the portfolio's strongest monthly performance!**), 3 months +1.5%. Stop 440 $ (+27.2% away, comfortable territory, widened from last round's +17.3%). Earnings 3 November (weekly_data.json, a Tuesday). Headlines: "AMD in a buy area" — analyst interest continues. "The valuation looks cheap after a three-year run" — the fundamentals are strong. "Chip Stocks Break Through Ceiling" — a sector rally. **Last round (#8) I upgraded the thesis label from WEAKENING to VALID (it regained the 50d). This round confirms it: holding the 50d and widening the gap (+12.9% above it), +8.5% on the week, +19.2% on the month. The thesis is VALID and STRONG — the portfolio's most dynamic position.**

**ANET (199.39 $) — leader in AI data-center network hardware → VALID and STRONG**
Price > 50d (187.53, +6.3% above it) >> 200d (155.11, +28.5% above it). RSI 55.8 (healthy). 1 week -0.1% (a minimal correction), 1 month +8.5%, 3 months +14.2%. Stop 160 $ (+24.6% away, comfortable). Earnings 3 November (a Tuesday). Headline: **"ANET raised its full-year outlook; AI data-center demand is strong!"** — this matters a great deal and strengthens the thesis. The -0.1% week is a minimal correction within normal volatility (+4.3% last round, -0.1% this round — consolidation). It is holding the 50d support (+6.3% above it) and momentum is healthy. **The portfolio's steadiest position. The guidance raise strengthened the thesis — VALID and STRONG.**

**NVDA (222.27 $) — AI accelerator leadership → VALID and RECOVERING**
Price > 50d (214.07, +3.8% above it) >> 200d (198.02, +12.2% above it). RSI 54.4 (healthy, improved from 49.9 last round). 1 week +1.8% (a recovery), 1 month +2.6%, 3 months +6.6%. Stop 190 $ (+17.0% away, comfortable and slightly wider than last round's +14.9%). Earnings 17 November (a Tuesday). Last round (#8) it had fallen 5.2% in its first week (218.29 $, -4.3% on the week); this round it recovered (222.27 $, +1.8% on the week). **It is holding the 50d (+3.8% above it, slightly wider than last round's +2.8%), momentum improved (RSI 49.9 → 54.4), and the stop distance widened slightly (+14.9% → +17.0%).** Last round the watch item was "NVDA's 50d status (regained or lost?)" — this round it is holding the 50d and widened the gap slightly. **The thesis holds; a recovery after the first-week fall — two consecutive weeks of decline would have been a warning, but it recovered this round. The watch continues.**

### D. Decisions

#### DECISION 1: HOLD — MU, AMD, ANET, NVDA

**MU:** holding the 50d support (+9.6% above it), the stop distance very comfortable (+39.2%), earnings 11 days out (Wednesday 30 September). The shortage news means price support, and the growth in AI capex supports memory demand. A +4.2% week is a healthy recovery. **The last week before earnings will be critical — the next round (26 September) is the check four days before the report.** Stop 730 $ retained.

**AMD:** holding the 50d and widening the gap (+12.9% above it), +8.5% on the week, +19.2% on the month — **the portfolio's most dynamic position.** It regained the 50d last round and confirmed it this round. RSI 65.4 (strong momentum but not yet overbought — that would be above 70), the stop distance comfortable (+27.2%). The thesis is VALID and STRONG. Stop 440 $ retained.

**ANET:** the guidance raise strengthened the thesis. Holding the 50d support (+6.3% above it); the -0.1% week is a minimal correction (consolidation, normal after last round's +4.3%). The stop distance is comfortable (+24.6%). The portfolio's steadiest position. Stop 160 $ retained.

**NVDA:** it recovered after the -5.2% first week (+1.8% on the week). Holding the 50d (+3.8% above it), RSI improved (49.9 → 54.4), the stop distance widened slightly (+14.9% → +17.0%). Two consecutive weeks of decline would have been a warning, but it recovered this round — the first month's performance is at an acceptable level (entry 230.36 $ → now 222.27 $, a -3.5% loss but above the 50d). The thesis holds; the watch continues. Stop 190 $ retained.

**Exit plan:** stop levels unchanged (MU 730 $, AMD 440 $, ANET 160 $, NVDA 190 $). A mechanical sale on a weekly close below them.

**The signal that would show the thesis is wrong:**
- MU: if the earnings report (30 September) misses expectations, or if the shortage narrative does not reach the margins. If it approaches the stop before the report (below 800 $).
- AMD: if it loses the 50d (495.85 $) and stays below it for three consecutive days — a momentum break signal; the thesis drops from VALID to WEAKENING.
- ANET: if it loses the 50d (187.53 $) — a decline after a guidance raise would put the thesis in question.
- NVDA: if it loses the 50d (214.07 $) and stays below it for three consecutive days, or approaches the stop (below 200 $) — that would mean the first month's momentum failed.

#### DECISION 2: NO NEW POSITIONS (the watchlist is empty)

**Cash:** 16,421 $ (16.4% of the portfolio, per REPORT.md).

**Watchlist status:** last round (#8, 12 September) five threshold-reached symbols (SNDK, TSM, MRVL, MSFT, GOOGL) were dropped from the list. **The watchlist is empty this round — no new symbol was assessed.**

**Why no new positions:**
(1) **The watchlist is empty:** last round every threshold-reached symbol was dropped (telling a threshold-reached symbol "watch one more round" is indefinite deferral and instruction section D forbids it). No new symbol screen was run.
(2) **The existing portfolio is strong:** AMD regained the 50d and strengthened this round (+8.5% on the week, +19.2% on the month), ANET raised guidance, MU recovered healthily ahead of earnings, and NVDA recovered after its first-week fall. All four positions are above the 50d with comfortable stop distances. **The portfolio has gained momentum — watching the existing positions is more disciplined than adding a new one.**
(3) **Cash strategy:** the 16.4% cash (16,421 $) will not be held passively (instruction section E). **What I am waiting for:** (a) a correction opportunity before or after MU's earnings (30 September) — an addition. (b) An opportunity to add to AMD if its momentum continues (say a correction toward 500 $). (c) If NVDA loses the 50d next round or approaches the stop, an alternative action (strengthening AMD). The cash is powder, ready for a correction opportunity.

**On running a new symbol screen:** one could ask "why not reassess the symbols dropped last round (TSM, MRVL, SNDK)?" The reasoning: (1) Last round's decision to drop them was made on overall grounds (the TSM/MRVL thresholds were badly overshot at 7/3 with limited contribution to the portfolio's theme; SNDK carried the psychological load plus profit-taking). (2) This round the existing portfolio gained strong momentum — adding a new position spreads the portfolio thin (each position shrinks and contributes less to a 3-5x target). (3) **Once a symbol has been dropped from the list, re-entering requires a very strong reason (a structural change like S&P 100 inclusion, or a technical opportunity like a 50d break after a 20% fall).** SNDK gained another 9.7% this round (1791.82 $, from last round's 1633.35 $ — the recovery after the S&P 100 inclusion continues), but the "dropped from the list" status still stands (a deferral that long, 4/3, had scattered the portfolio's focus). A new symbol screen can be run in later rounds, but this round the focus is on the existing positions.

### E. Theme risk

**Portfolio:** 4 positions (MU 33.4%, AMD 21.1%, ANET 15.3%, NVDA 14.1%, weights per REPORT.md) — all in the AI infrastructure theme. 83.9% invested, 16.1% cash (REPORT.md shows 16,421 $; the weight reads 16.1% rather than 16.4%, but REPORT.md's weights are the current ones).

**The risk of falling together:** if the AI spending cycle breaks (mega-caps cutting capex, the AI investment bubble bursting) every position falls together. That risk was accepted deliberately at the outset — the price of an aggressive target (3-5x). **This round the portfolio gained momentum** (AMD +8.5% on the week, ANET raised guidance, MU's shortage news, NVDA recovered) — the theme risk persists but the momentum within the portfolio has strengthened.

**Portfolio composition detail:**
- Memory: MU (33.4%) — the HBM/DRAM super-cycle, the portfolio's largest weight, earnings 11 days out
- AI accelerators: AMD (21.1%, widening above the 50d) + NVDA (14.1%, recovered) = 35.2% — the portfolio's second-largest group and its most dynamic front
- Network hardware: ANET (15.3%, raised guidance) — the data-center network leader, the steadiest position
**Total invested:** 83.9% (cash 16.1%).

**Diversification:** the three main fronts of AI infrastructure (memory, processors, networking) are covered. But ALL THREE depend on the AI spending cycle — a break in the theme hits them together. **I accept the risk: an aggressive target (3-5x) requires aggressive concentration.** Last round TSM/MRVL/MSFT/GOOGL were dropped — a strategy of theme depth (adding to the existing positions) was chosen over theme breadth. This round the existing portfolio gained momentum and the strategy was vindicated.

**Cash: NOT a protective cushion but buying power.** The 16.1% cash (16,421 $) does not protect the portfolio (an unleveraged virtual portfolio); it is powder for a decline. **What I am waiting for:** (1) a correction opportunity before or after MU's earnings (30 September) — an addition. (2) A correction opportunity in AMD if its momentum continues (around 500 $, say) — strengthening. (3) If NVDA weakens (losing the 50d, approaching the stop) — an alternative action (strengthening AMD or trimming NVDA). The cash is not passive; it is waiting for a correction opportunity.

### F. Accounting for myself

**1. What did I say last round, and what did I do this round?**

**Last round (#8, 12 September):**

- **HOLD MU, AMD, ANET, NVDA:** I held them all. **No departure.** I had upgraded AMD's thesis label from WEAKENING to VALID last round (it regained the 50d), and this round confirmed it (holding the 50d and widening the gap, +12.9% above it).

- **The watchlist — five threshold-reached symbols (SNDK, TSM, MRVL, MSFT, GOOGL) dropped from the list:** last round I dropped them all (instruction section D: threshold reached, open a position or drop it, there is no third option). This round I assessed no new symbol. **No departure.**

- **Preserving 16.4% cash "to wait for a correction opportunity":** last round I said "waiting for a correction opportunity in the existing positions (strengthening AMD, or a pre-earnings correction in MU)". There was no correction this round (AMD +8.5%, MU recovered +4.2%), so I held the cash. **No departure — waiting for a correction means holding cash when no correction comes.**

**NO DEPARTURES.** I did everything I said I would last round.

**2. Where last round's thesis turned out wrong — it did not; it was confirmed:**

**The AMD thesis (last round's upgrade to VALID):** last round (#8) it regained the 50d (516.13 $ > 496.55 $, +3.9% above it) and I upgraded the label from WEAKENING to VALID. This round confirms it: holding the 50d and widening the gap (559.82 $ > 495.85 $, +12.9% above it), +8.5% on the week, +19.2% on the month — **the portfolio's most dynamic position.** Last round I said "if AMD loses the 50d again next round, I could regret upgrading to VALID too early". **I do not regret it — AMD held the 50d and strengthened. The decision to upgrade the thesis was right.**

**NVDA's recovery after the first-week fall:** last round (#8) NVDA had fallen 5.2% in its first week (218.29 $, -4.3% on the week) and I said "it is holding the 50d support but momentum has weakened; it must be watched next round". This round it recovered (222.27 $, +1.8% on the week), is holding the 50d (+3.8% above it, slightly wider than last round's +2.8%), RSI improved (49.9 → 54.4), and the stop distance widened slightly (+14.9% → +17.0%). Last round I said "if NVDA falls another 10% next round, I could regret not trimming this round". **I do not regret it — NVDA recovered and the first-week fall was a short-term correction. The first month's performance is at an acceptable level (entry 230.36 $ → now 222.27 $, a -3.5% loss but above the 50d, and a recovery trend has begun).**

**The decision to drop the five threshold-reached symbols:** last round SNDK (4/3), TSM (7/3), MRVL (7/3), MSFT (7/3) and GOOGL (7/3) were all dropped. Last round I said "if one of them (especially TSM or MRVL) gains 30% in later rounds, I could regret it: instead of dropping the threshold-reached symbols I should at least have opened a position in TSM". Checking this round: TSM 433.24 $ → 434.67 $ (+0.3%), MRVL 236.10 $ → 244.25 $ (+3.5%), SNDK 1633.35 $ → 1791.82 $ (+9.7%). **None of them gained 30%. SNDK's +9.7% is the strongest, but it is the recovery after the S&P 100 inclusion — a short-term buying wave, not a structural change.** Last round's decision read: "dropping the threshold-reached symbols may mean missing technically strong names like TSM/MRVL. But preserving the portfolio's focus (AMD regained the 50d, the cash is ready for a correction opportunity) is more strategic." This round confirms it: AMD did +8.5% on the week (the portfolio's most dynamic position) and the existing portfolio gained momentum — focusing on the existing positions rather than adding a new one was the right call. **I do not regret it.**

**3. Where this round's decision could mislead me:**

**The decision to keep AMD's thesis label at VALID (and not to add):** AMD is holding the 50d and widening the gap (+12.9% above it), +8.5% on the week, +19.2% on the month — **the portfolio's most dynamic position.** The thesis is VALID and STRONG. If AMD gains another 20% next round (around 670 $) while I sat on cash "waiting for an opportunity to add", I could regret it: "I should have added around 560 $; the momentum was plain." My reasoning: (1) RSI 65.4 (strong momentum but close to 70 — overbought risk). (2) +8.5% on the week and +19.2% on the month — a climb at that pace is not sustainable and there is short-term pullback risk. (3) MU's earnings are 11 days out (30 September) — a correction opportunity before or after the report is more strategic (MU is the portfolio's largest weight at 33.4%, so the impact of an addition there is greater). **I accept the risk: if AMD's momentum continues I miss the chance to add. But with RSI at 65.4 (near overbought) there is short-term pullback risk — waiting for a correction is more disciplined.**

**The decision to hold NVDA (not to add):** NVDA recovered (+1.8% on the week), is holding the 50d (+3.8% above it), and RSI improved (54.4). But it is still down 3.5% (entry 230.36 $ → now 222.27 $). If NVDA gains 15% next round (around 255 $) I could regret it: "the recovery had begun and I did not add." My reasoning: (1) NVDA is still proving its first month — it fell 5.2% two weeks ago and recovered +1.8% this round, but the recovery trend is not confirmed (one week of recovery is not enough; two or three more weeks should be watched). (2) The stop distance is +17.0% (comfortable but the tightest of MU/AMD/ANET) — watching is more disciplined than adding. (3) The cash is being held for the MU earnings opportunity. **I accept the risk: if NVDA's recovery continues I miss the chance to add. But the first month is not yet proven — I will watch two or three more weeks and consider adding if the recovery is confirmed.**

**The decision not to add to MU before earnings:** MU's earnings are 11 days out (Wednesday 30 September). The price is 1015.80 $, +9.6% above the 50d, with a healthy +4.2% weekly recovery. The "warning of supply shortages through 2027" means price support. If MU's earnings come in strong and it gains 20% (around 1220 $) I could regret it: "I should have added around 1015 $ before the report." My reasoning: (1) **Earnings risk runs both ways:** a strong report could add 20% BUT a weak report or a guidance disappointment could take 10-15% off. Adding before the report increases the earnings risk. (2) The instruction's earnings rule: "no new full position with less than a week to earnings" — earnings are 11 days out, so not at that limit, BUT adding just because it is "more than a week" ignores the earnings risk. (3) **Cash strategy: waiting for a correction opportunity AFTER the report is more disciplined.** If the report is strong and the stock gains 10-15% I will not add (it is already at its target weight of 33.4%, the largest position). If the report is weak and the stock falls 10-15% there is an opportunity to add (around 900 $ — near the 50d at 927, a support test). **I accept the risk: if MU's earnings come in strong I miss the chance to add. But earnings risk runs both ways — waiting for a post-earnings correction is more disciplined. And if the report is strong and it gains 20%, the portfolio's largest weight at 33.4% already contributes heavily — the missed addition costs little.**

**The decision not to run a new symbol screen:** five threshold-reached symbols were dropped last round and I ran no new screen this round. If a new strong symbol were screened in later rounds (an AI-theme name like PLTR, SMCI or ORCL) and it gained 30%, I could regret it: "I should have run a new symbol screen this round." My reasoning: (1) Last round every threshold-reached symbol was dropped (instruction section D: threshold reached, open a position or drop it). Running a new screen would mean "starting from scratch" — but this round the existing portfolio gained momentum (AMD +8.5%, ANET raised guidance, MU recovered healthily), so the focus is on the existing positions. (2) Adding a new symbol spreads the portfolio thin (cash is 16.4% — one position at ~10% weight can be opened; each position shrinks and contributes less to a 3-5x target). (3) **Cash strategy: waiting for an opportunity to add to the existing positions (a post-earnings correction in MU, a correction in AMD) is more strategic.** **I accept the risk: missing a new strong symbol screen could be a lost opportunity. But the existing portfolio gained momentum — a theme-depth strategy (adding to the existing positions) fits better than theme breadth (a new symbol).**

**Lesson calibration:**
- **A behaviour change (two independent observations, the same direction, confirmed):** (1) The AMD "last chance" warning (round #7), the condition met (round #8), the thesis upgraded to VALID, and confirmed this round (#9) (holding the 50d and widening the gap, +8.5% on the week). (2) NVDA's -5.2% first week (round #8): I said "it is holding the 50d support; it must be watched next round", and this round it recovered (+1.8% on the week, holding the 50d). **In both positions the "conditional action plus watch" plan worked.** The "last chance" warning for AMD was right (the fundamentals were strong and the technicals recovered). Treating NVDA's first-week fall as "not a warning, watch it" was right (a short-term correction, then a recovery). **The lesson is confirmed: if a position is weakening but the fundamentals are strong (like AMD), issue a "last chance" warning and upgrade the thesis if the condition is met. If a new position falls in its first week (like NVDA), do not panic-sell — check whether it is holding the 50d, and if it is and it is recovering, watch it.**

- **Hypothesis (from round #8, confirmed this round):** the first-week performance of a new position is not predictable (NVDA -5.2%). This round NVDA recovered (+1.8%). **The lesson (confirmed): after opening a new position, watch the first 2-3 weeks. A first-week fall can be normal (a short-term correction), but losing the 50d or two consecutive weeks of decline is a warning. NVDA fell in its first week but held the 50d and recovered this round — a recovery trend has begun; the watch continues.**

- **A new hypothesis (from this round):** AMD's momentum is very strong (+8.5% on the week, +19.2% on the month, RSI 65.4 — close to overbought). If a correction appears next round (a 5-10% fall, around 500 $ — near the 50d at 495), that could be an opportunity to add (a healthy correction after strong momentum plus a test of the 50d support). **The lesson (still a hypothesis, to be tested next round): in a position with RSI above 65, waiting for a correction is more disciplined than adding. If AMD corrects next round and tests the 50d (around 495 $ — a 10-15% fall), I will assess an addition.**

**Next review:** 26 September 2026 (Saturday — the next weekly round). **CRITICAL:** (1) MU's earnings on Wednesday 30 September — **the next round is four days before the report, the final check.** Is it holding the 50d, is the stop distance comfortable? (2) Is AMD's momentum continuing? RSI 65.4 (close to overbought) — pullback risk. Is it holding the 50d and widening the gap? (3) Is NVDA's recovery trend continuing? Is it holding the 50d, is RSI improving? (4) Is ANET's momentum continuing after the guidance raise? (5) The cash is waiting for a correction opportunity (a post-earnings correction in MU, or a correction in AMD).

---

## #10 — 2026-09-26 · WEEKLY ROUND

**Market context:** strong momentum continues in the AI infrastructure theme. The portfolio is +7.11% (9.23% ahead of SPY, 7.98% ahead of SMH). Semiconductors and AI accelerators posted a very strong week — AMD and MU stood out.

### A. Data status

Data was fetched in full for 10/10 symbols (based on the Friday 25 September 2026 close). Price, 50/200d SMA, RSI, return data and earnings dates are present for every position. **No missing fields.**

**Data-integrity gate check (instruction step 3 — every field checked one by one):**
- MU: last_price = 1082.28 OK, sma50 = 941.62 OK
- AMD: last_price = 630.63 OK, sma50 = 504.71 OK
- ANET: last_price = 206.55 OK, sma50 = 190.23 OK
- NVDA: last_price = 225.07 OK, sma50 = 215.79 OK

`_meta.missing_data` = [] (empty). **Every critical field is populated — the data-integrity gate is passed.** No need for an extra yfinance query was identified.

**News scan:** 50 headlines in total across 10 symbols. Worth noting:

- **MU:** "Q4 Earnings Are Likely to Boost the 'Strong Buy' Case for Micron Stock" — earnings on 30 September (5 days out). "Micron Technology Stock Wavers Ahead Of Fiscal Q4 Earnings Report" — pre-earnings volatility. "Stock Market Today: Dow Surges 450 Points On U.S.-Iran Peace Hopes; Micron Rises" — reduced geopolitical risk supports MU. "Dow Jones Futures: Growth Stocks Shrug Off Surging Yields; Micron, SpaceX, Tesla, Key Economic Data Due" — growth stocks are strong.

- **AMD:** "Trump says China's Xi 'seemed to like' renaming AI as super intelligence" — the Trump-Xi meeting, a positive signal for AI investment. "These are stocks getting lifted up by Meta's Muse" — Meta's Muse AI platform is supporting AMD. "Tech stocks gain after tech titan dinner with Trump and China's Xi Jinping" — the technology summit is positive. "Taiwan says U.S. arms support serves American interests after Trump-Xi summit" — reduced geopolitical uncertainty.

- **ANET:** "Arista Networks (ANET) Draws Fresh AI Attention, Is The Stock Still Cheap?" — AI interest continues, the valuation is being questioned. "Technology Stocks Are Back, Because Nothing Else Is" — the technology leaders are back. "Arista Networks, Inc. (ANET) Is a Trending Stock: Facts to Know Before Betting on It" — the trend continues.

- **NVDA:** "2 Data Center Stocks That Could Help Make You a Fortune" — data-center demand is strong. No NVDA-specific news, only general AI momentum headlines.

- **SNDK:** "Are AI Memory Stocks Ready For Another Run? Micron, Sandisk Attempt To Clear New Buy Points" — SNDK is looking for a new buy point. "SK Hynix's Solidigm Weighs IPO That Could Raise $15 Billion, Report Says" — SK Hynix's IPO plan, interest in the NAND sector.

### B. The cause of the move

**AMD (559.82 $ → 630.63 $, +12.6% on the week) — it exceeded ±10%, so a cause investigation:**

The reasons for AMD's strong performance:
1. **The Trump-Xi technology summit (the week of 25 Sep):** "Trump says China's Xi 'seemed to like' renaming AI as super intelligence" — a signal of US-China AI cooperation and reduced geopolitical risk. AMD is an important player in the Chinese market (data-center GPUs), so a softening trade war is positive.
2. **Meta's Muse AI platform:** "These are stocks getting lifted up by Meta's Muse" — Meta's new AI platform may be using AMD's accelerators (diversification away from NVDA). Mega-caps turning toward AMD strengthens the "NVDA alternative" thesis.
3. **The semiconductor sector rally:** "Chip Stocks Break Through Ceiling As Sector Rebounds" (last round's headline) — the broad buying wave across the sector continues. AMD had regained the 50d last round, and this round a technical breakout (strengthening above the 50d) gave a buy signal.
4. **Technical momentum:** last round (#9) it was holding and widening above the 50d (+12.9% above it, RSI 65.4). This round momentum strengthened further — RSI 73.0 (it entered overbought territory, though not extremely so). Technical strength attracts algorithmic and momentum investors.

**Conclusion:** AMD's +12.6% move rests not on a single event but on a combination of four factors — reduced geopolitical risk (Trump-Xi), mega-cap diversification (Meta Muse), the sector rally and technical momentum. The "AI accelerator / NVDA alternative" thesis is strengthening.

**MU (1015.80 $ → 1082.28 $, +6.5% on the week) — it did not exceed ±10% but came close, a note:**
MU is +6.5% (below the ±10% threshold) but a strong recovery. Earnings are 5 days out (Wednesday 30 September) — the headline "Q4 Earnings Are Likely to Boost the 'Strong Buy' Case" is setting expectations. Reduced geopolitical risk (US-Iran peace hopes) supports MU. The move is within normal volatility but must be watched carefully ahead of the report.

### C. Thesis health check

**MU (1082.28 $, Friday 25 September) — memory super-cycle / HBM leadership → VALID and STRONG**
Price >> 50d (941.62, +14.9% above it) >> 200d (660.97, +63.7% above it). **Last round it was +9.6% above the 50d; this round +14.9% — the gap is widening!** RSI 63.2 (healthy momentum, up from 58.3 last round but not overbought). 1 week +6.5%, 1 month +15.7%, 3 months -5.5%. Stop 730 $ (+48.3% away, very comfortable, widened further from last round's +39.2%). **Earnings 30 September (weekly_data.json, a Wednesday, 5 days out — CRITICAL!)** Headlines: "Q4 Earnings Are Likely to Boost the 'Strong Buy' Case" — analyst expectations are high. "Dow Surges 450 Points On U.S.-Iran Peace Hopes; Micron Rises" — reduced geopolitical risk supports it. "Growth Stocks Shrug Off Surging Yields" — growth stocks are strong despite rising rates. A +6.5% week is a strong recovery (last round +4.2%, so the pace is holding). It is holding the 50d support and widening the gap (+14.9% above it) with strong momentum. **The thesis holds and is strong; earnings are 5 days out — the report is THIS ROUND's critical event.**

**AMD (630.63 $) — AI accelerator / the NVDA alternative → VALID and VERY STRONG**
Price >> 50d (504.71, +24.9% above it) >> 200d (364.75, +72.9% above it). **FAR above the 50d!** Last round (#9) it was +12.9% above; this round +24.9% — a momentum burst. RSI **73.0 (IT ENTERED OVERBOUGHT TERRITORY!)** — 65.4 last round, 73.0 this round. An RSI above 70 is technically an overbought signal, but a strong momentum trend can continue. 1 week +12.6% (**a very strong week!**), 1 month +32.3% (**the portfolio's strongest monthly performance!**), 3 months +16.9%. Stop 440 $ (+43.3% away, very comfortable, widened further from last round's +27.2%). Earnings 3 November (a Tuesday). Headlines: the Trump-Xi technology summit (a signal of AI cooperation), Meta Muse (a turn toward AMD), the semiconductor sector rally. **Last round (#9) I kept the thesis label at VALID (it had regained the 50d) and said it was confirmed. This round is a MOMENTUM BURST — +32.3% on the month, +12.6% on the week, +24.9% above the 50d. RSI 73.0 is in overbought territory — technically there is high short-term pullback risk (with RSI >70, a healthy correction back to 60-65 is possible). But the thesis is VERY STRONG — the Trump-Xi summit and Meta Muse confirm AMD's "NVDA alternative" thesis. The portfolio's most dynamic and strongest-performing position.**

**ANET (206.55 $) — leader in AI data-center network hardware → VALID and STRONG**
Price > 50d (190.23, +8.6% above it) >> 200d (157.04, +31.5% above it). RSI 60.2 (healthy momentum, up from 55.8 last round). 1 week +3.6%, 1 month +2.7%, 3 months +25.9%. Stop 160 $ (+29.1% away, very comfortable). Earnings 3 November (a Tuesday). Headlines: "ANET Draws Fresh AI Attention, Is The Stock Still Cheap?" — AI interest continues. "Technology Stocks Are Back" — a sector rally. A +3.6% week is a healthy recovery (last round -0.1%, a minimal correction; this round it recovered). It is holding the 50d support (+8.6% above it, slightly wider than last round's +6.3%) and momentum is healthy. **The portfolio's steadiest position. Momentum continues after last round's guidance raise. The thesis holds and is strong.**

**NVDA (225.07 $) — AI accelerator leadership → VALID and THE RECOVERY CONTINUES**
Price > 50d (215.79, +4.3% above it) >> 200d (199.13, +13.0% above it). RSI 55.3 (healthy, up slightly from 54.4 last round). 1 week +1.3%, 1 month -1.2%, 3 months +15.6%. Stop 190 $ (+18.5% away, comfortable and slightly wider than last round's +17.0%). Earnings 17 November (a Tuesday). Last round (#9) the recovery had begun (+1.8% on the week, +3.8% above the 50d); this round the recovery continues (+1.3% on the week, +4.3% above the 50d). **It is holding the 50d and widening the gap (+3.8% → +4.3%), RSI is stable (54.4 → 55.3), and the stop distance widened slightly (+17.0% → +18.5%). A two-week recovery trend is confirmed.** In round #8 it fell 5.2% in its first week, in #9 it recovered +1.8%, and this round the recovery continues at +1.3% — **a two-week recovery trend; the worry about the first month's decline is fading.** But it is still below its entry price (entry 230.36 $ → now 225.07 $, a -2.3% loss — improved from last round's -3.5%). **The thesis HOLDS, the recovery trend has continued for two weeks, and the first month's performance is approaching an acceptable level. One or two more weeks of recovery would take it to the entry price.**

### D. Decisions

#### DECISION 1: HOLD — MU, AMD, ANET, NVDA

**MU:** **earnings are 5 days out (Wednesday 30 September) — THIS ROUND's critical event.** It is holding the 50d and widening the gap (+14.9% above it, up from last round's +9.6%), the stop distance is very comfortable (+48.3%, the widest in the portfolio), and the week was a strong +6.5% recovery. The headline "Q4 Earnings Are Likely to Boost the 'Strong Buy' Case" is raising analyst expectations. Reduced geopolitical risk (US-Iran peace hopes) supports it. **The earnings risk:** a strong report could add 10-15% BUT a weak report or a guidance disappointment could take 10-15% off. **Decision: hold and wait for the report.** The position is 33.7% (the portfolio's largest weight) — adding before the report would increase the earnings risk (if the report is weak, the loss grows). **The post-earnings assessment (next round, Saturday 3 October):** if the report is strong and it gains 10-15%, I will not add (it is already the largest weight). If the report is weak and it falls 10-15%, that is an opportunity to add (a test of the 50d around 941 $ — support). Stop 730 $ retained.

**AMD:** **RSI 73.0 — OVERBOUGHT TERRITORY!** Technically the short-term pullback risk is very high (an RSI above 70 is overbought; a healthy correction back to 60-65 is possible). But it is far above the 50d (+24.9%), the stop distance is very comfortable (+43.3%), and momentum is VERY STRONG (+32.3% on the month, +12.6% on the week). The Trump-Xi summit and the Meta Muse headlines strengthen the thesis. **Decision: hold and watch RSI.** The momentum burst may continue (strong trends can run for weeks even in overbought territory) BUT the pullback risk is high. **A warning next round if RSI climbs to 75-80 (deeper overbought) OR if it loses the 50d (below 504 $ — a momentum break).** For now it is far above the 50d, the thesis is very strong and the stop is very comfortable — hold. I will not add (RSI 73.0 is overbought; waiting for a correction is disciplined). Stop 440 $ retained.

**ANET:** momentum continues after the guidance raise (last round). It is holding the 50d support (+8.6% above it), the week was a healthy +3.6% recovery, RSI 60.2 (healthy), and the stop distance is very comfortable (+29.1%). The portfolio's steadiest position. Stop 160 $ retained.

**NVDA:** a two-week recovery trend is confirmed (round #9: +1.8%, this round: +1.3%). It is holding the 50d and widening the gap (+3.8% → +4.3%), RSI is stable (54.4 → 55.3), and the stop distance widened slightly (+17.0% → +18.5%). It is approaching its entry price (entry 230.36 $ → now 225.07 $, a -2.3% loss — improved from last round's -3.5%). The first month's performance is approaching an acceptable level. Stop 190 $ retained.

**Exit plan:** stop levels unchanged (MU 730 $, AMD 440 $, ANET 160 $, NVDA 190 $). A mechanical sale on a weekly close below them.

**The signal that would show the thesis is wrong:**
- MU: if the report (30 September) misses expectations, or the guidance is weak. If it approaches the stop after the report (below 800 $).
- AMD: if RSI climbs to 75-80 (very overbought — a correction is near) OR if it loses the 50d (504.71 $) and stays below it for three consecutive days — a break signal after a momentum burst.
- ANET: if it loses the 50d (190.23 $) — a decline after the guidance raise would put the thesis in question.
- NVDA: if it loses the 50d (215.79 $) and stays below it for three consecutive days — that would mean the three-week recovery trend failed.

#### DECISION 2: NO NEW POSITIONS (preserving cash — waiting for earnings and a correction)

**Cash:** 16,421 $ (16.4% of the portfolio, per REPORT.md).

**Watchlist status:** in round #8 (12 September) five threshold-reached symbols (SNDK, TSM, MRVL, MSFT, GOOGL) were dropped from the list. No new symbol screen has been run for the last two rounds (#9, #10). **The watchlist is empty this round too — no new symbol assessment.**

**Why no new positions:**
1. **MU's earnings are 5 days out (Wednesday 30 September) — the cash is being held for a post-earnings opportunity.** The earnings risk runs both ways. If the report is weak and MU falls 10-15% (around 900 $ — near the 50d at 941, a support test), that is an opportunity to add. Opening a new position before the report increases the portfolio's risk.
2. **AMD's RSI is 73.0, in overbought territory — the pullback risk is high.** If AMD corrects 10-15% in the coming rounds (around 550 $ — near the 50d at 504, a support test), that is an opportunity to add. Adding now (with RSI at 73.0) would be chasing in overbought territory — undisciplined.
3. **The existing portfolio gained very strong momentum:** AMD +32.3% on the month (the portfolio's most dynamic position), MU strong ahead of earnings (+6.5% on the week), ANET steady (+3.6% on the week), NVDA in a two-week recovery trend. All four positions are above the 50d with comfortable stop distances. **Adding a new position spreads the portfolio (cash is 16.4% — one position at ~10% weight can be opened; each position shrinks and contributes less to the 3-5x target). Waiting for an opportunity to add to the existing positions (a post-earnings MU move or an AMD correction) is more strategic.**
4. **No new symbol screen was run:** TSM/MRVL/SNDK/MSFT/GOOGL were dropped last round (threshold reached; instruction section D: open a position or drop it). Running a new screen would mean "starting from scratch", but this round's focus is the earnings report and the existing positions.

**Cash strategy (instruction section E: "the cash will not be held passively"):** the 16.4% cash does not protect the portfolio (an unleveraged virtual portfolio); it is powder for a decline. **What I am waiting for:**
- **(a) After MU's earnings (the next round, 3 October):** if the report is weak and it falls 10-15% (around 900 $ — a test of the 50d), an opportunity to add. If the report is strong and it gains 10-15%, I will not add (it is already the largest weight at 33.7%).
- **(b) An AMD correction (within one or two rounds):** RSI 73.0 is overbought and the pullback risk is high. If it corrects 10-15% (around 550 $ — near the 50d at 504, a support test), an opportunity to add.
- **(c) If NVDA weakens (unlikely but being watched):** losing the 50d or approaching the stop (below 200 $) would call for an alternative action (trimming NVDA and strengthening AMD, say).

The cash is powder, ready for **MU's earnings and an AMD correction.** Both could happen within one or two rounds — MU's report is 5 days out and an AMD correction is plausible after RSI 73.0.

### E. Theme risk

**Portfolio:** 4 positions (MU 33.7%, AMD 22.5%, ANET 15.1%, NVDA 13.6%, weights per REPORT.md) — all in the AI infrastructure theme. 84.9% invested, 15.1% cash (REPORT.md shows 16,421 $; the 15.1% weight is presumably because the portfolio's value has risen).

**The risk of falling together:** if the AI spending cycle breaks (mega-caps cutting capex, the AI investment bubble bursting) every position falls together. That risk was accepted deliberately at the outset — the price of an aggressive target (3-5x). **This round the portfolio's momentum is VERY strong** (AMD's +32.3% monthly burst, MU strong ahead of earnings, ANET steady, NVDA recovering) — the theme risk persists but the momentum in the portfolio is at historic levels.

**Portfolio composition detail:**
- Memory: MU (33.7%) — the HBM/DRAM super-cycle, the portfolio's largest weight, **earnings 5 days out**
- AI accelerators: AMD (22.5%, RSI 73.0 overbought, a momentum burst) + NVDA (13.6%, in a recovery trend) = 36.1% — the portfolio's second-largest group and **its most dynamic front (AMD's burst)**
- Network hardware: ANET (15.1%, raised guidance) — the data-center network leader, the steadiest position
**Total invested:** 84.9% (cash 15.1%).

**Diversification:** the three main fronts of AI infrastructure (memory, processors, networking) are covered. But ALL THREE depend on the AI spending cycle — a break in the theme hits them together. **I accept the risk: an aggressive target (3-5x) requires aggressive concentration.** Over the last three rounds (#8, #9, #10) TSM/MRVL/MSFT/GOOGL were dropped and no new symbol screen was run — a strategy of theme depth (an opportunity to add to the existing positions) was chosen over theme breadth. This round the existing portfolio produced a momentum burst (+7.11% on the week) and the strategy was vindicated.

**A specific risk — AMD overbought (RSI 73.0):** AMD is 22.5% of the portfolio (the second-largest position). RSI 73.0 means the short-term pullback risk is technically very high. If AMD corrects 15-20% (to around 530 $, say), the portfolio takes a 3-4% hit. **But AMD's stop distance is very comfortable (+43.3%, a 440 $ stop) and it is far above the 50d (+24.9%) — even a technical correction would not trigger the stop; it would be a healthy consolidation.** The risk is a momentum break rather than a correction (losing the 50d) — that would put the thesis in question. For now momentum is very strong and the thesis is strong (Trump-Xi plus Meta Muse) — the watch continues.

**Cash: NOT a protective cushion but buying power.** The 15.1% cash does not protect the portfolio; it is powder for a decline. It is ready for the opportunity after MU's earnings (5 days out) or an AMD correction (plausible after RSI 73.0). **If neither materialises (a strong MU report and no AMD correction), the cash waits one or two more rounds.** Waiting for an opportunity rather than rushing an addition is disciplined.

### F. Accounting for myself

**1. What did I say last round, and what did I do this round?**

**Last round (#9, 19 September):**

- **HOLD MU, AMD, ANET, NVDA:** I held them all. **No departure.**

- **Keeping AMD's thesis label at VALID:** last round it was holding and widening above the 50d (+12.9%); this round it strengthened further (+24.9% above it, RSI 73.0 overbought). **No departure — the thesis became VALID and VERY STRONG.**

- **No new positions, preserving cash "for a post-earnings MU opportunity or an AMD correction":** I held to it. MU's earnings are 5 days out (critical this round) and AMD's RSI is 73.0 (high pullback risk). **No departure.**

**NO DEPARTURES.** I did everything I said I would last round.

**2. Where last round's thesis turned out wrong — it did not; it turned out MUCH stronger:**

**The AMD momentum expectation:** last round (#9) I said "is AMD's momentum continuing? RSI 65.4 (close to overbought) — pullback risk". This round AMD produced a MOMENTUM BURST: +12.6% on the week, +32.3% on the month, RSI 73.0 (it ENTERED overbought territory). **I was not wrong — the momentum continued, but it came in MUCH stronger than I expected.** Last round I said "RSI 65.4, close to overbought, pullback risk", but instead of correcting AMD produced a momentum burst. **The cause:** the Trump-Xi technology summit (reduced geopolitical risk), Meta Muse (a turn toward AMD) and the semiconductor sector rally — three strong catalysts arrived at once. **What I learned: saying "pullback risk" about a position with RSI above 65 is not the same as saying "it will definitely correct" — if strong catalysts arrive (a macro event like Trump-Xi) momentum can push RSI past 70. But RSI 73.0 is now genuinely in overbought territory — the pullback risk next round is VERY high.**

**The NVDA recovery prediction:** last round I asked "is NVDA's recovery trend continuing?" This round the recovery continued (+1.3% on the week, +4.3% above the 50d). **It turned out right — a two-week recovery trend is confirmed.** The worry about the -5.2% first week (round #8) has gone. A two-week recovery trend means the first month's performance is approaching an acceptable level (entry 230.36 $ → now 225.07 $, a -2.3% loss — improved from last round's -3.5%).

**The approach to MU's earnings:** last round I said "MU's earnings are 11 days out"; this round they are 5 days out. MU staged a strong recovery (+6.5% on the week) and analyst expectations rose ("Q4 Earnings Are Likely to Boost the 'Strong Buy' Case"). **The earnings risk runs both ways — the result will be known by the next round (3 October) and I will assess it then.**

**3. Where this round's decision could mislead me:**

**The decision to hold AMD (RSI 73.0 overbought, not adding):** AMD's RSI is 73.0, in overbought territory — technically the short-term pullback risk is VERY high. If AMD's momentum burst continues next round (RSI climbing to 75-80, another +15% to around 725 $), I could regret it: "I should have added at RSI 73.0; the momentum was continuing." My reasoning: (1) An RSI above 70 is technically overbought — a healthy correction back to 60-65 is expected. Adding at RSI 73.0 is chasing in overbought territory, undisciplined. (2) Last round I said "RSI 65.4, pullback risk" and instead of correcting AMD went to RSI 73.0 — but there is no rule that this repeats. Strong catalysts (Trump-Xi) triggered the overbought condition, and now the catalysts are spent (the next big event is MU's earnings). (3) AMD's weight is 22.5% (the second-largest position) — adding at that weight raises the portfolio's risk considerably (if AMD corrects, the portfolio takes a 3-4% hit). **I accept the risk: if AMD's momentum continues I miss the chance to add. But adding at RSI 73.0 in overbought territory is undisciplined — waiting for a correction is better (an opportunity to add around 550 $ if it corrects 10-15%).**

**The decision not to add to MU (earnings 5 days out):** MU is +14.9% above the 50d, with a strong +6.5% weekly recovery and high analyst expectations. If MU's report is very strong and it gains 20% (around 1300 $), I could regret it: "I should have added while it was around 1082 $ before the report." My reasoning: (1) **The earnings risk runs both ways:** a strong report could add 20% BUT a weak report could take 10-15% off. The report is 5 days out — very close. Adding before it increases the earnings risk. (2) The instruction's earnings rule: "no new full position with less than a week to earnings" — 5 days is very close to that limit (7 days = a week). The rule says "new full position", not "addition", BUT adding before a report carries the same risk (if the report is weak the loss grows). (3) MU's weight is 33.7% (the largest position) — adding at that weight raises the portfolio's risk considerably and pushes the concentration to an extreme (to 40%+, say). **I accept the risk: if MU's report is strong I miss the chance to add. But the earnings risk runs both ways, 5 days is very close, and the weight is already the highest — waiting for a post-earnings correction is more disciplined (an opportunity to add around 900 $ if the report is weak and it falls 10-15%).**

**The decision not to add to NVDA (the recovery trend is continuing):** NVDA's two-week recovery trend is continuing (+1.8% last round, +1.3% this round) and it is holding and widening above the 50d (+4.3%). If NVDA gains another 15% in the coming rounds (around 260 $, above its entry price), I could regret it: "the recovery trend was clear; I should have added around 225 $." My reasoning: (1) NVDA is still below its entry price (entry 230.36 $ → now 225.07 $, a -2.3% loss). The first month's performance is not complete — a three-week recovery trend is positive, but calling the recovery "confirmed" before it reaches the entry price is premature. (2) The stop distance is +18.5% (comfortable but the tightest of MU/AMD/ANET) — watching is more disciplined than adding. (3) The cash is being held for MU's earnings and an AMD correction — both are more strategic opportunities. **I accept the risk: if NVDA's recovery continues I miss the chance to add. But it has not reached its entry price yet and the first month is not complete — one or two more weeks of recovery would take it to the entry price, and I will assess adding then.**

**The decision not to run a new symbol screen (a third round without one):** no new symbol screen has been run for the last three rounds (#8, #9, #10). TSM/MRVL/SNDK/MSFT/GOOGL were dropped last round and the watchlist is empty. If a new strong symbol appeared in later rounds (PLTR, SMCI, TSM again) and gained 30%, I could regret it: "I should have run a new symbol screen this round." My reasoning: (1) **The existing portfolio gained VERY strong momentum** (AMD's +32.3% monthly burst, MU strong ahead of earnings, ANET steady, NVDA recovering) — adding a new symbol spreads the portfolio and weakens the existing momentum. (2) **The focus is on earnings and correction opportunities:** MU's report is 5 days out (the result will be known next round) and AMD's RSI is 73.0 (high pullback risk — plausible within one or two rounds). Both opportunities could arrive within one or two rounds, and the cash is ready for them. (3) **A theme-depth strategy:** adding to the existing positions (theme depth) is more strategic than adding a new symbol (theme breadth) — the existing positions' theses are strong and their momentum is high. **I accept the risk: missing a new strong symbol screen could be a lost opportunity. But the portfolio's momentum is at a historic level (+7.11% on the week) — the focus is on earnings and correction opportunities, and the theme-depth strategy is preserved.**

**Lesson calibration:**
- **A behaviour change (three independent observations, the same direction):** (1) The AMD "last chance" warning (round #7), the condition met (round #8), the thesis upgraded to VALID. (2) Round #9 confirmed AMD (holding and widening above the 50d, +12.9%). (3) This round AMD produced a MOMENTUM BURST (+24.9% above the 50d, +32.3% on the month, RSI 73.0 overbought). **Confirmed across three rounds: the "last chance" warning plus a conditional action plan works. If a position is weakening but the fundamentals are strong (like AMD), issue a "last chance" warning, upgrade the thesis if the condition is met, and watch if the momentum continues.** **The lesson is CONFIRMED, with a STRONG catalyst addendum:** AMD's momentum burst rested on **macro / mega-cap catalysts** like the Trump-Xi technology summit and Meta Muse. The lesson: if the fundamentals are strong (AMD's AI ramp), issue a "last chance" warning, BUT if a macro catalyst arrives (Trump-Xi) momentum can push RSI past 70 — in that case do not panic-sell, watch; but do not add once RSI is 73+ (chasing in overbought territory is undisciplined). Wait for a correction.

- **Confirmed (from round #8):** the first-week performance of a new position is not predictable (NVDA's -5.2% fall in round #8). Round #9 recovered (+1.8%) and this round the recovery continued (+1.3%). **The lesson is confirmed: if a new position falls in its first week, do not panic-sell — check whether it is holding the 50d. If a two-week recovery trend is confirmed, keep watching (until it reaches the entry price).** NVDA's three-week recovery trend has begun — the first month's performance is approaching an acceptable level.

- **A new hypothesis (from this round):** AMD's RSI is 73.0, in overbought territory. Last round I said "RSI 65.4, pullback risk" and AMD went to RSI 73.0 — strong catalysts (Trump-Xi, Meta Muse) triggered the overbought condition. **The lesson (a hypothesis): saying "pullback risk" in the RSI 65-70 band is not a certainty — if a strong macro catalyst arrives, RSI can push past 70. But RSI above 70 is genuine overbought territory and the pullback risk is VERY high. Do not add at RSI 73.0 (chasing in overbought territory); wait for a correction (a 10-15% correction is plausible, an opportunity at a test of the 50d).** To be tested next round: does AMD correct (does RSI fall back to 60-65) or does the momentum continue (does RSI climb to 75-80)?

**Next review:** 3 October 2026 (Saturday — the next weekly round). **THE MOST CRITICAL ROUND:** (1) **MU's earnings result (Wednesday 30 September, three days before that round) — the round's main event.** Was the report strong or weak? How was the guidance? What was the price reaction? Is there an opportunity to add after the report (around 900 $ if it fell — a test of the 50d)? (2) **Has AMD's correction begun? Has RSI fallen from 73.0?** Is it holding the 50d or has it lost it? If a correction has begun (10-15%, around 550 $ — a test of the 50d), an opportunity to add. (3) Is NVDA's recovery trend continuing? Has it reached its entry price (above 230 $)? (4) Is ANET's momentum continuing? (5) **The cash strategy will become clear:** the decision to add after MU's earnings and/or after an AMD correction.
