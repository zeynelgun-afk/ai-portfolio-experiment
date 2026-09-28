#!/usr/bin/env python3
"""Build the Thesis Watch dashboard: template + current theses.json/portfolio.json -> HTML.

The dashboard is published as an artifact and embeds the thesis text as it stood at publish
time. That is why the template lives in the repository: the theses change every Saturday, so
the dashboard has to be rebuilt and republished. A hand-edited one-off HTML file would be
stale by the second round — the very problem the dashboard exists to solve.

Live prices are not embedded: the page fetches those from the viewer's own FMP connector.
The only things embedded are the thesis text, the thresholds, the stop levels and the stamp.

Usage:
    python dashboard/build.py                 # writes dashboard/thesis-watch.html
    python dashboard/build.py --out /path.html
Then, in a Claude session, republish to the same artifact URL.
"""

import argparse
import csv
import json
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(BASE, "dashboard", "thesis-watch.template.html")
DEFAULT_OUT = os.path.join(BASE, "dashboard", "thesis-watch.html")


def load(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as handle:
        return json.load(handle)


def equity_curve():
    """The weekly value series from history.csv: portfolio vs SPY vs SMH."""
    path = os.path.join(BASE, "history.csv")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                rows.append({
                    "date": row["date"],
                    "portfolio": float(row["portfolio_usd"]),
                    "spy": float(row["spy_usd"]),
                    "smh": float(row["smh_usd"]),
                })
            except (KeyError, ValueError):
                continue  # a malformed row is skipped, never guessed at
    return rows


def latest_round_label(default="DECISION_LOG.md (no round found)"):
    """Return the heading of the most recent weekly round as a label."""
    path = os.path.join(BASE, "DECISION_LOG.md")
    if not os.path.exists(path):
        return default
    latest = None
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("## #") and "WEEKLY ROUND" in line.upper():
                latest = line[3:].split("·")[0].strip()
    return f"DECISION_LOG.md {latest}" if latest else default


def main():
    parser = argparse.ArgumentParser(description="Build the Thesis Watch dashboard")
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    theses = load("theses.json")
    portfolio = load("portfolio.json")
    payload = {
        "stamp": date.today().isoformat(),
        "source_round": latest_round_label(),
        "cash_usd": portfolio["cash_usd"],
        "dividend_receivable_usd": portfolio.get("dividend_receivable_usd",0),
        "benchmark_total_return_basis": portfolio.get("benchmark_total_return_basis",{}),
        "positions": {p["symbol"]: {
            "shares": p["shares"],
            "entry_price": p["entry_price"],
            "stop": p.get("stop_weekly_close"),
            "earnings": p.get("next_earnings"),
            "cost_usd": p.get("cost_usd"),
        } for p in portfolio["positions"]},
        "theses": {key: value for key, value in theses.items()
                   if not key.startswith("_") and key in {p["symbol"] for p in portfolio["positions"]}},
        # The dashboard also serves as the portfolio view: the equity curve, the
        # benchmark references and every trade to date.
        "starting_capital_usd": portfolio["starting_capital_usd"],
        "start_date": portfolio["start_date"],
        "benchmark": portfolio["benchmark"],
        "history": equity_curve(),
        "trades": portfolio.get("trade_history", []),
    }

    with open(TEMPLATE, encoding="utf-8") as handle:
        template = handle.read()
    if template.count("__DATA__") != 1:
        raise SystemExit("The template must contain exactly one __DATA__ placeholder")
    html = template.replace(
        "__DATA__", json.dumps(payload, ensure_ascii=False, allow_nan=False,
                               separators=(",", ":")).replace("<", "\\u003c"))
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(html)

    claims = sum(len(v["claims"]) for v in payload["theses"].values())
    print(f"wrote {args.out} · {len(payload['theses'])} positions, {claims} claims, "
          f"{len(payload['history'])} history points, {len(payload['trades'])} trades, "
          f"source: {payload['source_round']}")


if __name__ == "__main__":
    main()
