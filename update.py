#!/usr/bin/env python3
"""AI Portfolio Experiment — automated update.

What it does (measurement and reporting only; it makes NO decisions — since charter
version 2 every buy and sell decision belongs to the AI):
  1. Fetches the latest closing prices (yfinance, no key required).
  2. Values the portfolio and computes the SPY/SMH comparison.
  3. FLAGS positions that closed below their exit level — it never closes them. That
     decision belongs to the AI in the weekly round.
  4. Writes REPORT.md and history.csv; emits outputs for GitHub Actions.
  5. Computes the deferral counters from the log and prints them into the report
     (counters.py) — so the counter is data placed in front of the AI rather than a
     number the AI declares.
"""

import csv
import json
import os
from datetime import date

import yfinance as yf

import counters

BASE = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_PATH = os.path.join(BASE, "portfolio.json")
REPORT_PATH = os.path.join(BASE, "REPORT.md")
HISTORY_PATH = os.path.join(BASE, "history.csv")
BREACH_PATH = os.path.join(BASE, "STOP_BREACH.md")
TELEGRAM_PATH = os.path.join(BASE, "telegram.txt")


def fetch_closes(symbols):
    frame = yf.download(" ".join(symbols), period="10d", interval="1d",
                        auto_adjust=False, progress=False)["Close"]
    # yfinance can return a fully empty trailing day. ffill rescued the price, but the
    # date label then pointed at that empty day — the report said "the 28 Aug close"
    # while the price actually belonged to 27 Aug. The date must come from the last day
    # that genuinely has data.
    filled = frame.dropna(how="all")
    if filled.empty:
        raise RuntimeError("No closing data available: every day is empty")
    as_of = filled.index[-1].date()
    if hasattr(frame, "columns"):
        last = frame.ffill().iloc[-1]
        return {symbol: float(last[symbol]) for symbol in symbols}, as_of
    # single-symbol case
    return {symbols[0]: float(frame.ffill().iloc[-1])}, as_of


def main():
    with open(PORTFOLIO_PATH, encoding="utf-8") as handle:
        portfolio = json.load(handle)

    symbols = [p["symbol"] for p in portfolio["positions"]] + ["SPY", "SMH"]
    prices, as_of = fetch_closes(symbols)
    today = date.today().isoformat()

    # --- Exit-level check: WARNING ONLY, never execution ---
    # Charter version 2: closing a position is the AI's decision. Nothing is touched here.
    breaches = []
    for position in portfolio["positions"]:
        close = prices[position["symbol"]]
        if close < position["stop_weekly_close"]:
            performance = (close / position["entry_price"] - 1) * 100
            breaches.append(
                f"- **{position['symbol']}**: close {close:.2f} $ < exit level "
                f"{position['stop_weekly_close']} $ ({performance:+.1f}%) "
                f"→ THE DECISION IS THE AI'S: close it, move the level, or carry it "
                f"with a stated reason"
            )

    if breaches:
        with open(BREACH_PATH, "w", encoding="utf-8") as handle:
            handle.write(f"# Exit-level warning — {today}\n\n"
                         f"Data as of: {as_of}\n\n"
                         + "\n".join(breaches)
                         + "\n\nNothing was closed automatically. This round's decision "
                           "and its reasoning go into DECISION_LOG.md.\n")
    elif os.path.exists(BREACH_PATH):
        # Clear the flag once the warning has passed; otherwise the file hung around
        # permanently.
        os.remove(BREACH_PATH)

    # --- Valuation ---
    position_value = sum(p["shares"] * prices[p["symbol"]]
                         for p in portfolio["positions"])
    total = portfolio["cash_usd"] + position_value
    start = portfolio["starting_capital_usd"]
    spy_value = start * prices["SPY"] / portfolio["benchmark"]["SPY_reference"]
    smh_value = start * prices["SMH"] / portfolio["benchmark"]["SMH_reference"]

    # --- History (equity curve; a same-day row is overwritten) ---
    previous_rows = []
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, newline="", encoding="utf-8") as handle:
            previous_rows = [row for row in csv.reader(handle)
                             if row and row[0] not in ("date", today)]
    with open(HISTORY_PATH, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "portfolio_usd", "spy_usd", "smh_usd"])
        writer.writerows(previous_rows)
        writer.writerow([today, f"{total:.2f}", f"{spy_value:.2f}", f"{smh_value:.2f}"])

    # --- Report ---
    if breaches:
        breach_note = (chr(10).join(breaches)
                       + "\n\n*Nothing was closed automatically — the decision is the "
                         "AI's.*")
    else:
        breach_note = "No warnings — every position is above its exit level."
    rows = []
    for position in portfolio["positions"]:
        price = prices[position["symbol"]]
        value = position["shares"] * price
        performance = (price / position["entry_price"] - 1) * 100
        stop_distance = (price / position["stop_weekly_close"] - 1) * 100
        rows.append(
            f"| {position['symbol']} | {position['entry_price']:.2f} | {price:.2f} | "
            f"{performance:+.1f}% | {value:,.0f} | {value / total * 100:.1f}% | "
            f"{position['stop_weekly_close']} ({stop_distance:+.1f}%) |"
        )

    report = f"""# Portfolio Report — {today}

Data: closes as of {as_of} · Starting capital: {start:,.0f} $ (2026-08-05)

## Positions

| Ticker | Entry | Last | Return | Value $ | Weight | Stop (distance) |
|---|---|---|---|---|---|---|
{chr(10).join(rows)}

**Cash:** {portfolio['cash_usd']:,.2f} $

## Scoreboard

| | Value | Return |
|---|---|---|
| **AI Portfolio** | {total:,.0f} $ | **{(total / start - 1) * 100:+.2f}%** |
| SPY (100k on the same day) | {spy_value:,.0f} $ | {(spy_value / start - 1) * 100:+.2f}% |
| SMH (100k on the same day) | {smh_value:,.0f} $ | {(smh_value / start - 1) * 100:+.2f}% |

Gap vs SPY: **{(total - spy_value) / start * 100:+.2f}%** · vs SMH: **{(total - smh_value) / start * 100:+.2f}%**

## Stop check

{breach_note}
{counters.report_block()}
*Automated report (update.py). Decisions and theses: DECISION_LOG.md*
"""
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write(report)

    portfolio["last_updated"] = today
    with open(PORTFOLIO_PATH, "w", encoding="utf-8") as handle:
        json.dump(portfolio, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    # --- Telegram summary (the workflow sends this file) ---
    position_summary = "\n".join(
        f"• {p['symbol']}: {p['shares'] * prices[p['symbol']]:,.0f} $ "
        f"(price {prices[p['symbol']]:.2f} $, "
        f"{(prices[p['symbol']] / p['entry_price'] - 1) * 100:+.1f}%)"
        for p in portfolio["positions"]
    )
    if breaches:
        breach_telegram = "⚠️ Below the exit level (the decision is the AI's):\n" + \
            "\n".join(item.replace("**", "") for item in breaches)
    else:
        breach_telegram = "✅ No exit-level warnings."
    with open(TELEGRAM_PATH, "w", encoding="utf-8") as handle:
        handle.write(
            f"📊 AI Portfolio Experiment — {today}\n\n"
            f"Total: {total:,.0f} $ ({(total / start - 1) * 100:+.2f}%)\n"
            f"SPY: {(spy_value / start - 1) * 100:+.2f}% · "
            f"SMH: {(smh_value / start - 1) * 100:+.2f}%\n"
            f"Gap vs SPY: {(total - spy_value) / start * 100:+.2f}%\n\n"
            f"Positions:\n{position_summary}\n"
            f"Cash: {portfolio['cash_usd']:,.0f} $\n\n"
            f"{breach_telegram}\n\n"
            f"Details: https://github.com/zeynelgun-afk/ai-portfoy-deneyi"
        )

    # --- GitHub Actions output ---
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as handle:
            handle.write(f"stop_breach={'true' if breaches else 'false'}\n")
            handle.write("breach_list="
                         + ", ".join(item.split("**")[1] for item in breaches) + "\n")

    print(f"Total: {total:,.2f} $ ({(total / start - 1) * 100:+.2f}%) | "
          f"SPY: {(spy_value / start - 1) * 100:+.2f}% | "
          f"SMH: {(smh_value / start - 1) * 100:+.2f}% | "
          f"Breaches: {len(breaches)}")


if __name__ == "__main__":
    main()
