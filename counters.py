#!/usr/bin/env python3
"""Compute the watchlist deferral counters from DECISION_LOG.md.

Why this is its own script: instructions version 6 made the counter mandatory. Round #7
wrote it in the right format but started TSM/MRVL/SNDK at 1/3 — all three had been
deferred since round #4. As long as a counter is the counter's own declaration, it can be
reset. So it is no longer something the AI writes but data placed in front of it:
update.py prints this into REPORT.md.

The counting rule (the mechanical equivalent of instruction section D):
  N = the number of rounds a symbol sat in the data set without a position being opened.
      Resetting it requires a "reset event": a trade in that symbol (portfolio.json
      trade_history) or the symbol being dropped from the list ("DROP FROM LIST" in the
      log). The definition is deliberately mechanical: if what counted as a "real
      assessment" were open to interpretation, the counter would become negotiable again.
      The data set is the list in weekly_data.py; the decision to drop a symbol is made
      in prose and this script reads it.
"""

import json
import os
import re
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE, "DECISION_LOG.md")
PORTFOLIO_PATH = os.path.join(BASE, "portfolio.json")
WEEKLY_DATA_PATH = os.path.join(BASE, "weekly_data.json")

THRESHOLD = 3  # on the third deferral: either open a position or drop the symbol
DROP_MARKER = "DROP FROM LIST"

# Weekly-round headings carry an ISO date: "## #10 — 2026-09-26 · WEEKLY ROUND".
# An English month name ("26 September 2026") is accepted as a fallback so an older or
# hand-written heading still parses instead of silently vanishing from the count.
ISO_HEADING = re.compile(r"^## #(\d+) — (\d{4}-\d{2}-\d{2})", re.MULTILINE)
NAMED_HEADING = re.compile(r"^## #(\d+) — (\d{1,2}) ([A-Za-z]+) (\d{4})", re.MULTILINE)


def _parse_named(day, month_name, year):
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(f"{day} {month_name} {year}", fmt).date()
        except ValueError:
            continue
    return None


def split_rounds(text):
    """Split the log into [(round_number, date, body), ...]."""
    matches = []
    for match in ISO_HEADING.finditer(text):
        matches.append((match.start(), int(match.group(1)),
                        date.fromisoformat(match.group(2))))
    for match in NAMED_HEADING.finditer(text):
        parsed = _parse_named(match.group(2), match.group(3), match.group(4))
        if parsed:
            matches.append((match.start(), int(match.group(1)), parsed))
    matches.sort()

    rounds = []
    for index, (start, number, when) in enumerate(matches):
        end = matches[index + 1][0] if index + 1 < len(matches) else len(text)
        rounds.append((number, when, text[start:end]))
    return rounds


def mentions(body, symbol):
    """Does this text mention the symbol (word boundary, so MU is not found inside AMU)?"""
    return re.search(rf"\b{re.escape(symbol)}\b", body) is not None


def compute_counters(rounds, trade_history, candidates):
    """Return (status, N, dropped_in_round) for each candidate symbol."""
    result = {}
    for symbol in candidates:
        resets = [date.fromisoformat(trade["date"])
                  for trade in trade_history if trade["symbol"] == symbol]
        dropped_in = None
        for number, when, body in rounds:
            for line in body.splitlines():
                if mentions(line, symbol) and DROP_MARKER in line.upper():
                    dropped_in = number
                    resets.append(when)

        last_reset = max(resets) if resets else None
        if last_reset is None:
            counted = [number for number, _, _ in rounds]
        else:
            counted = [number for number, when, _ in rounds if when > last_reset]

        if dropped_in is not None and (not counted or max(counted) <= dropped_in):
            result[symbol] = ("dropped", len(counted), dropped_in)
        else:
            result[symbol] = ("watching", len(counted), None)
    return result


def find_candidates(portfolio, weekly_data):
    """Watchlist candidates = symbols in the data set minus the open positions."""
    held = {position["symbol"] for position in portfolio["positions"]}
    return [symbol for symbol in weekly_data
            if symbol != "_meta" and symbol not in held]


def report_block():
    """Produce the text embedded into REPORT.md. Returns "" when data is missing."""
    if not (os.path.exists(LOG_PATH) and os.path.exists(WEEKLY_DATA_PATH)):
        return ""
    with open(LOG_PATH, encoding="utf-8") as handle:
        rounds = split_rounds(handle.read())
    with open(PORTFOLIO_PATH, encoding="utf-8") as handle:
        portfolio = json.load(handle)
    with open(WEEKLY_DATA_PATH, encoding="utf-8") as handle:
        weekly_data = json.load(handle)

    candidates = find_candidates(portfolio, weekly_data)
    if not rounds or not candidates:
        return ""

    counters = compute_counters(rounds, portfolio.get("trade_history", []), candidates)
    rows = []
    for symbol in candidates:
        status, count, dropped_in = counters[symbol]
        if status == "dropped":
            rows.append(f"| {symbol} | — | dropped from the list in round #{dropped_in} |")
        else:
            note = (f"**THRESHOLD REACHED — this round: open a position or "
                    f"{DROP_MARKER}**" if count >= THRESHOLD else "")
            rows.append(f"| {symbol} | {count}/{THRESHOLD} | {note} |")

    return f"""
## Deferral counters

Computed from DECISION_LOG.md (counters.py) — these numbers are not re-derived during the
round, they are read from here. Resetting one requires either a position being opened or
the symbol being dropped from the list.

| Symbol | Deferred | Note |
|---|---|---|
{chr(10).join(rows)}
"""


if __name__ == "__main__":
    print(report_block() or "(could not compute: the log or the data file is missing)")
