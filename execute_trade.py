#!/usr/bin/env python3
"""The layer that EXECUTES an autonomous intraday trade — deterministic, no LLM.

Why this is a separate script: the content of the decision belongs to the AI (charter
version 2), but executing it is arithmetic. Letting an LLM write to portfolio.json
directly would mean a single corrupt yfinance bar could turn into a real trade. Here the
decision is executed exactly as given — but the arithmetic and the data integrity are
checked first. None of this is a constraint on the decision: no check ever says "this
trade is wrong", only "this trade cannot be done with these numbers".

The fill price is NOT taken from the LLM. It is the intraday price measured by the
detector and stored in state/violations.json — it comes from a measurement, never from
the model's sentence.

Reasons a decision may go unexecuted (all of them are written to the log and the pending
notes; nothing fails silently):
  * the market is closed (the trade is deferred; the decision carries to Saturday)
  * the price source is not live (`data_source != intraday_5m`)
  * the arithmetic does not hold (not enough cash, more shares than held)
  * a trade in the same direction already happened today (trade_lock.json)

Before any mutation, portfolio.json is snapshotted to state/portfolio_snapshot.json, so
`--rollback` can restore the pre-trade state without reaching for git.

Usage:
    python execute_trade.py
    python execute_trade.py --dry-run     # writes nothing; prints what it would do
    python execute_trade.py --rollback    # restore the snapshot taken before the trade
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from market_time import market_open, recent

BASE = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_PATH = os.path.join(BASE, "portfolio.json")
LOG_PATH = os.path.join(BASE, "DECISION_LOG.md")

LIVE_SOURCE = "intraday_5m"
SHARE_EPSILON = 1e-6


def env(name, default=""):
    return (os.environ.get(name) or default).strip()


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%MZ")


def read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(f"Unreadable execution state: {os.path.basename(path)}") from error


def write_json(path, payload):
    """Atomic write: a crash mid-write must not leave portfolio.json half-rewritten."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory,
                                         delete=False, suffix=".tmp")
    try:
        with handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        if os.path.exists(handle.name):
            os.unlink(handle.name)
        raise


def number(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


# ------------------------------------------------------------------------ validation


def validate(decision, portfolio, data, market_is_open, locks, today, price_source=LIVE_SOURCE):
    """Returns (executable, rejection_reason, details). Never judges the decision itself."""
    symbol = decision.get("symbol")
    action = decision.get("action")
    if action == "HOLD":
        return False, "the decision is HOLD — nothing to execute", {}
    if decision.get("new_stop") is not None:
        stop = number(decision["new_stop"])
        if stop is None or stop <= 0:
            return False, "invalid new_stop — must be a positive finite price", {}

    row = data.get(symbol, {})
    price = number(row.get("price"))
    if price is None or price <= 0:
        return False, f"no measured price for {symbol} — no trade made", {}
    if row.get("data_source") != price_source:
        return False, (f"the price source is not live ({row.get('data_source')}) — "
                       "no intraday trade made"), {}
    if not market_is_open:
        return False, ("the market is closed — the trade carries to the next session or "
                       "the Saturday round"), {}

    direction = "SELL" if action in ("SELL", "TRIM") else action
    lock = f"{today.isoformat()}:{symbol}:{direction}"
    legacy_trim = f"{today.isoformat()}:{symbol}:TRIM"
    if lock in locks or (direction == "SELL" and legacy_trim in locks):
        return False, f"a trade in the same direction already happened today ({lock})", {}

    holdings = {p["symbol"]: p for p in portfolio.get("positions", [])}
    cash = number(portfolio.get("cash_usd")) or 0.0

    if action in ("SELL", "TRIM"):
        holding = holdings.get(symbol)
        if not holding:
            return False, f"{symbol} is not in the portfolio — nothing to sell", {}
        held = number(holding.get("shares")) or 0.0
        shares = held if action == "SELL" else number(decision.get("shares"))
        if shares is None or shares <= 0:
            return False, f"invalid share count ({decision.get('shares')!r})", {}
        if shares > held + SHARE_EPSILON:
            return False, f"more shares than held ({shares} > {held})", {}
        shares = min(shares, held)
        return True, None, {"shares": shares, "price": price,
                            "amount": shares * price, "lock": lock}

    if action == "BUY":
        amount = number(decision.get("amount_usd"))
        if amount is None or amount <= 0:
            return False, f"invalid amount_usd ({decision.get('amount_usd')!r})", {}
        if amount > cash:
            return False, f"not enough cash ({amount:.2f} $ > {cash:.2f} $)", {}
        return True, None, {"shares": amount / price, "price": price, "amount": amount,
                            "lock": lock}

    return False, f"unknown action ({action!r})", {}


# ------------------------------------------------------------------------- execution


def execute(decision, portfolio, details, moment, source="intraday_autonomous"):
    """Mutate portfolio.json in place and return the trade_history record."""
    symbol, action = decision["symbol"], decision["action"]
    shares, price, amount = details["shares"], details["price"], details["amount"]
    holdings = {p["symbol"]: p for p in portfolio["positions"]}

    if action in ("SELL", "TRIM"):
        holding = holdings[symbol]
        remaining = round((number(holding["shares"]) or 0.0) - shares, 6)
        portfolio["cash_usd"] = round((number(portfolio.get("cash_usd")) or 0.0)
                                      + amount, 2)
        if remaining <= SHARE_EPSILON:
            portfolio["positions"] = [p for p in portfolio["positions"]
                                      if p["symbol"] != symbol]
            recorded_action = "SELL"
        else:
            ratio = remaining / (remaining + shares)
            holding["shares"] = remaining
            # Cost falls proportionally; the entry price is unchanged (a partial sale
            # does not move the average).
            holding["cost_usd"] = round((number(holding.get("cost_usd")) or 0.0)
                                        * ratio, 2)
            recorded_action = "TRIM"
    else:  # BUY — add to an existing position or open a new one
        portfolio["cash_usd"] = round((number(portfolio.get("cash_usd")) or 0.0)
                                      - amount, 2)
        holding = holdings.get(symbol)
        if holding:
            old_shares = number(holding["shares"]) or 0.0
            old_cost = number(holding.get("cost_usd")) or 0.0
            new_shares = round(old_shares + shares, 6)
            holding["shares"] = new_shares
            holding["cost_usd"] = round(old_cost + amount, 2)
            holding["entry_price"] = round(holding["cost_usd"] / new_shares, 2)
        else:
            portfolio["positions"].append({
                "symbol": symbol, "shares": round(shares, 6),
                "entry_price": round(price, 2),
                "entry_date": moment.date().isoformat(),
                "cost_usd": round(amount, 2), "target_weight_pct": None,
                "stop_weekly_close": number(decision.get("new_stop")),
                "next_earnings": None,
            })
            holding = portfolio["positions"][-1]
        recorded_action = "BUY"

    new_stop = number(decision.get("new_stop"))
    if new_stop and holding in portfolio["positions"]:
        holding["stop_weekly_close"] = new_stop

    record = {
        "date": moment.date().isoformat(),
        "time_utc": moment.strftime("%H:%M"),
        "action": recorded_action,
        "symbol": symbol,
        "shares": round(shares, 6),
        "price": round(price, 2),
        "amount_usd": round(amount, 2),
        "source": source,
        "note": decision.get("reasoning", "")[:400],
    }
    portfolio.setdefault("trade_history", []).append(record)
    portfolio["last_updated"] = moment.date().isoformat()
    return record


def write_log(moment, executed, rejected):
    """Intraday decisions land in DECISION_LOG.md under their own record type.

    Charter rule 1: every decision is written to the log. So that an intraday decision
    can be told apart from a weekly round, the heading is numbered with an "S#" prefix.
    """
    if not executed and not rejected:
        return
    with open(LOG_PATH, encoding="utf-8") as handle:
        existing = handle.read()
    index = existing.count("· INTRADAY DECISION") + 1
    lines = [f"\n## S#{index} — {moment.date().isoformat()} "
             f"{moment.strftime('%H:%M')} UTC · INTRADAY DECISION\n",
             "This is not a weekly round but an event-driven intraday one "
             "(`detector.py` -> `reassess.py` -> `execute_trade.py`). The trigger "
             "and the resulting assessment are recorded below.\n"]
    for decision, details in executed:
        lines += [
            f"### {decision['symbol']} — {details['recorded_action']} (EXECUTED)\n",
            f"- **Trigger:** {decision.get('trigger', '-')}",
            f"- **Fill:** {details['shares']:.4f} shares × {details['price']:.2f} $ "
            f"= {details['amount']:,.2f} $ (price source: the intraday bar measured by "
            "the detector)",
            f"- **Thesis assessment:** {decision.get('thesis_assessment', '-')}",
            f"- **Reasoning:** {decision.get('reasoning', '-')}",
            f"- **What would show the thesis is wrong:** "
            f"{decision.get('falsifier', '-')}",
            f"- **Model:** {decision.get('model', '-')}\n",
        ]
    for decision, reason in rejected:
        lines += [
            f"### {decision.get('symbol')} — {decision.get('action')} (NOT EXECUTED)\n",
            f"- **Trigger:** {decision.get('trigger', '-')}",
            f"- **Why it was not executed:** {reason}",
            f"- **The model's reasoning (recorded, not acted on):** "
            f"{decision.get('reasoning', '-')}\n",
        ]
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def append_note(path, heading, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"\n## {heading}\n\n{body}\n")


def rollback(snapshot_path):
    """Restore the snapshot taken before the trade."""
    if not os.path.exists(snapshot_path):
        print("No snapshot found — nothing to roll back")
        return 1
    snapshot = read_json(snapshot_path, None)
    if snapshot is None or "positions" not in snapshot:
        print("The snapshot is unreadable — rollback refused")
        return 1
    write_json(PORTFOLIO_PATH, snapshot)
    print(f"portfolio.json restored from the snapshot "
          f"(as of {snapshot.get('last_updated')})")
    print("The DECISION_LOG.md entry was NOT removed — the record of a decision is not "
          "erased. Write a new entry explaining the rollback.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Execute the intraday decision")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback", action="store_true",
                        help="restore portfolio.json from the pre-trade snapshot")
    parser.add_argument("--state-dir", default=os.path.join(BASE, "state"))
    args = parser.parse_args()

    decision_path = os.path.join(args.state_dir, "pending_decision.json")
    lock_path = os.path.join(args.state_dir, "trade_lock.json")
    notes_path = os.path.join(args.state_dir, "pending_notes.md")
    violations_path = os.path.join(args.state_dir, "violations.json")
    snapshot_path = os.path.join(args.state_dir, "portfolio_snapshot.json")

    if args.rollback:
        return rollback(snapshot_path)

    bundle = read_json(decision_path, {})
    decisions = bundle.get("decisions", [])
    if not decisions:
        print("No decision to execute")
        return 0

    violations = read_json(violations_path, {})
    data = violations.get("data", {})
    market_is_open = bool(violations.get("market_open"))
    portfolio = read_json(PORTFOLIO_PATH, None)
    if portfolio is None:
        print("ERROR: could not read portfolio.json — no trade made")
        return 1

    moment = now_utc()
    market_is_open = market_is_open and market_open(moment)
    if (not recent(bundle.get("time"), moment, 900)
            or not recent(violations.get("checked_at"), moment, 900)
            or bundle.get("measurement_at") != violations.get("checked_at")):
        raise RuntimeError("Decision and measurement are stale or do not belong to the same check")
    today = moment.date()
    locks = read_json(lock_path, {})
    # Recover the lock if a previous process saved the portfolio and then crashed
    # before saving trade_lock.json. The ledger must prevent replay on its own.
    for trade in portfolio.get("trade_history", []):
        if trade.get("source") == "intraday_autonomous" and trade.get("date") == today.isoformat():
            direction = "SELL" if trade.get("action") in ("SELL", "TRIM") else trade.get("action")
            locks[f"{today.isoformat()}:{trade['symbol']}:{direction}"] = trade.get("time_utc", "recorded")
    executed, rejected = [], []

    for decision in decisions:
        row = data.get(decision.get("symbol"), {})
        if market_is_open and decision.get("action") != "HOLD" and not recent(row.get("price_at"), moment):
            raise RuntimeError("Trade refused: missing, stale or future price timestamp")
        ok, reason, details = validate(decision, portfolio, data, market_is_open, locks,
                                       today)
        label = f"{decision.get('symbol')} {decision.get('action')}"
        if not ok:
            print(f"SKIP {label}: {reason}")
            rejected.append((decision, reason))
            continue
        if args.dry_run:
            print(f"[dry-run] {label}: {details['shares']:.4f} shares × "
                  f"{details['price']:.2f} $ = {details['amount']:,.2f} $")
            continue
        if not executed:
            # Snapshot before the first mutation, so --rollback has a clean state.
            write_json(snapshot_path, read_json(PORTFOLIO_PATH, portfolio))
        record = execute(decision, portfolio, details, moment)
        details["recorded_action"] = record["action"]
        locks[details["lock"]] = iso(moment)
        executed.append((decision, details))
        print(f"DONE {label}: {record['shares']} shares × {record['price']} $ "
              f"= {record['amount_usd']} $ · cash {portfolio['cash_usd']} $")

    if args.dry_run:
        return 0

    if executed:
        write_json(PORTFOLIO_PATH, portfolio)
        write_json(lock_path, locks)
    write_log(moment, executed, rejected)
    for decision, reason in rejected:
        append_note(notes_path,
                    f"{iso(moment)} · {decision.get('symbol')} · DECISION NOT EXECUTED",
                    f"**Proposed action:** {decision.get('action')}\n\n"
                    f"**Why it was not executed:** {reason}\n\n"
                    f"**The model's reasoning:** {decision.get('reasoning', '-')}\n\n"
                    "The Saturday round reassesses this decision.")

    # The decision bundle has been consumed; it must not be executed again next run.
    os.remove(decision_path)

    gh_output = env("GITHUB_OUTPUT")
    if gh_output:
        summary = "; ".join(
            f"{d['symbol']} {x['recorded_action']} {x['shares']:.4f}@{x['price']:.2f}"
            for d, x in executed) or "none"
        with open(gh_output, "a", encoding="utf-8") as handle:
            handle.write(f"trade_count={len(executed)}\n")
            handle.write(f"trade_summary={summary}\n")
            handle.write(f"rejected_count={len(rejected)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
