#!/usr/bin/env python3
"""The audit layer — measure the decision-maker against its own record.

Why this exists: the weekly reminder asks a human to read a 180 KB decision log and judge
whether the reasoning holds up. That audit was not happening, and an audit that does not
happen is not a safeguard. So the parts of it that can be computed are computed.

This file contains NO LLM. Everything here is derived from the repository's own history:
the decision log, the trade history, the thesis file and the permanent trigger log. An
auditor that reads the same data as the decision-maker and offers an opinion produces a
correlated second guess; an auditor that computes what actually happened does not.

The scorecard's questions are the ones the charter already asks but nobody could answer:

  * Does the label match the action? The instructions forbid marking a thesis BROKEN and
    quietly holding it. Now that is checked rather than trusted.
  * Is a label being deferred? The same label three rounds running is the instructions'
    own trigger for "something must change this round".
  * Were the exits right? Every SELL and TRIM is scored against what the symbol did
    afterwards. This is the one thing the decision-maker could not know at the time and
    the auditor can — SNDK, sold at 1212 $ and up 43% a month later, is exactly this.
  * Which thresholds are noise? A condition that fires on every check measures nothing; a
    thesis-level condition that has never fired was tied to a number that cannot happen.
  * Is the commentary layer failing quietly? Claims stuck on `unassessed` mean the LLM
    layer is rejecting its own output and nobody noticed.

Usage:
    python audit.py                 # print the scorecard and write AUDIT.md
    python audit.py --json          # machine-readable, for the reviewer layer
    python audit.py --no-prices     # skip the exit scoring (no network)
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE, "DECISION_LOG.md")
PORTFOLIO_PATH = os.path.join(BASE, "portfolio.json")
THESES_PATH = os.path.join(BASE, "theses.json")
REPORT_PATH = os.path.join(BASE, "AUDIT.md")

# The instructions' own threshold: the same label three rounds running means something
# must change that round. The audit uses the same number so the two never disagree.
LABEL_STREAK_LIMIT = 3
# The deferral rule only bites on labels that leave a question open. A thesis that has
# been VALID for seven rounds while the position is held is a settled state, not a
# deferral — flagging it would make the scorecard cry wolf, and a scorecard that cries
# wolf is one nobody reads. The instructions' own example is a WEAKENING streak.
UNSETTLED_LABELS = {"WEAKENING", "BROKEN"}
# A condition confirmed on more than this share of the checks it was measured in is
# firing on noise rather than on meaning.
NOISE_SHARE = 0.5

ROUND_HEADING = re.compile(r"^## #(\d+) — (\d{4}-\d{2}-\d{2})", re.MULTILINE)
INTRADAY_HEADING = re.compile(r"^## S#(\d+) — (\d{4}-\d{2}-\d{2})", re.MULTILINE)
# "**MU (1082.28 $, Friday 25 September) — memory super-cycle → VALID and STRONG**"
HEALTH_LINE = re.compile(
    r"^\*\*([A-Z]{1,6})\s*\([^)]*\)\s*—.*?→\s*(VALID|WEAKENING|BROKEN)", re.MULTILINE)
# "#### DECISION 1: TRIM — AVGO (position cut in half)"
DECISION_LINE = re.compile(
    r"^#### DECISION \d+:\s*([A-Z ]+?)\s*—\s*(.+)$", re.MULTILINE)

ACTION_WORDS = {"TRIM", "SELL", "CLOSE", "BUY", "OPEN A NEW POSITION"}


def read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return default


def read_rounds(text):
    """Split the log into weekly rounds: [(number, date, body), ...]."""
    matches = [(m.start(), int(m.group(1)), date.fromisoformat(m.group(2)))
               for m in ROUND_HEADING.finditer(text)]
    rounds = []
    for index, (start, number, when) in enumerate(matches):
        end = matches[index + 1][0] if index + 1 < len(matches) else len(text)
        rounds.append((number, when, text[start:end]))
    return rounds


# --------------------------------------------------------------- label vs. action

def label_audit(rounds):
    """Two checks the instructions state as rules but nothing enforced.

    A. Label/action agreement — a thesis marked BROKEN while the position is held.
    B. Label deferral — the same label for LABEL_STREAK_LIMIT rounds running.
    """
    history = defaultdict(list)          # symbol -> [(round, label)]
    acted_on = defaultdict(set)          # round -> {symbols acted on}

    for number, _, body in rounds:
        for symbol, label in HEALTH_LINE.findall(body):
            history[symbol].append((number, label))
        for action, targets in DECISION_LINE.findall(body):
            action = action.strip()
            if action not in ACTION_WORDS:
                continue
            for symbol in re.findall(r"\b([A-Z]{2,6})\b", targets):
                acted_on[number].add(symbol)

    broken_but_held, streaks = [], []
    for symbol, entries in history.items():
        for number, label in entries:
            if label == "BROKEN" and symbol not in acted_on.get(number, set()):
                broken_but_held.append({"round": number, "symbol": symbol,
                                        "label": label})
        run_label, run_start = None, None
        for index, (number, label) in enumerate(entries):
            if label != run_label:
                run_label, run_start = label, index
            length = index - run_start + 1
            if (length >= LABEL_STREAK_LIMIT and label in UNSETTLED_LABELS
                    and symbol not in acted_on.get(number, set())):
                streaks.append({"symbol": symbol, "label": label, "rounds": length,
                                "through_round": number})
    # keep only the longest streak reported per symbol+label
    longest = {}
    for item in streaks:
        key = (item["symbol"], item["label"])
        if item["rounds"] >= longest.get(key, {"rounds": 0})["rounds"]:
            longest[key] = item
    return {"broken_but_held": broken_but_held,
            "label_streaks": sorted(longest.values(),
                                    key=lambda x: -x["rounds"]),
            "labels_seen": {s: len(e) for s, e in history.items()}}


# ------------------------------------------------------------------ exit scoring

def exit_audit(portfolio, prices):
    """Score every exit against what the symbol did afterwards.

    This is the auditor's one real advantage over the decision-maker: hindsight. The
    verdict is about the OUTCOME only — a good decision can have a bad outcome, which is
    why this feeds the reviewer rather than standing as a judgement on its own.
    """
    results = []
    for trade in portfolio.get("trade_history", []):
        if trade["action"] not in ("SELL", "TRIM"):
            continue
        later = prices.get(trade["symbol"])
        if later is None:
            results.append({"date": trade["date"], "symbol": trade["symbol"],
                            "action": trade["action"], "exit_price": trade["price"],
                            "later_price": None, "move_pct": None,
                            "verdict": "unmeasured"})
            continue
        move = (later / trade["price"] - 1) * 100
        results.append({
            "date": trade["date"], "symbol": trade["symbol"], "action": trade["action"],
            "exit_price": trade["price"], "later_price": round(later, 2),
            "move_pct": round(move, 1),
            # "costly" means the exit avoided nothing; "vindicated" means it avoided a fall.
            "verdict": "costly" if move > 10 else "vindicated" if move < -10 else "neutral",
        })
    return results


def fetch_prices_since(symbols):
    """Latest price per symbol, for exit scoring. Returns {} when the network fails."""
    if not symbols:
        return {}
    try:
        import yfinance as yf
    except ImportError:
        print("NOTE: yfinance is not installed — exit scoring skipped")
        return {}
    try:
        frame = yf.download(" ".join(sorted(symbols)), period="5d", interval="1d",
                            auto_adjust=False, progress=False)["Close"]
        frame = frame.dropna(how="all")
        if frame.empty:
            return {}
        last = frame.ffill().iloc[-1]
        if hasattr(last, "index"):
            return {symbol: float(last[symbol]) for symbol in symbols
                    if symbol in last.index and last[symbol] == last[symbol]}
        return {sorted(symbols)[0]: float(last)}
    except Exception as error:
        print(f"NOTE: exit scoring skipped ({error})")
        return {}


# ------------------------------------------------------------- threshold quality

def threshold_audit(trigger_log_path, theses):
    """Which conditions are measuring something, and which are decoration?"""
    fired = defaultdict(int)
    acted = defaultdict(int)
    checks = 0
    seen_stamps = set()
    if os.path.exists(trigger_log_path):
        with open(trigger_log_path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                seen_stamps.add(entry.get("checked_at"))
                key = (entry["claim_id"], entry["type"])
                fired[key] += 1
                if entry.get("acted_on"):
                    acted[key] += 1
    checks = len(seen_stamps)

    rows = []
    for symbol, position in theses.items():
        if symbol.startswith("_"):
            continue
        for claim in position.get("claims", []):
            for condition in claim.get("conditions", []):
                key = (claim["id"], condition["type"])
                count = fired.get(key, 0)
                share = (count / checks) if checks else 0.0
                if count == 0:
                    quality = "never fired"
                elif share > NOISE_SHARE:
                    quality = "noisy"
                else:
                    quality = "informative"
                rows.append({
                    "claim_id": claim["id"], "symbol": symbol,
                    "type": condition["type"], "severity": condition.get("severity"),
                    "fired": count, "acted_on": acted.get(key, 0),
                    "share_of_checks": round(share, 3), "quality": quality,
                })
    return {"checks_recorded": checks, "conditions": rows}


# --------------------------------------------------------- attribution and churn

def attribution_audit(portfolio):
    """Weekly decisions versus intraday decisions — the charter's new question."""
    weekly, intraday = [], []
    for trade in portfolio.get("trade_history", []):
        (intraday if trade.get("source") == "intraday_autonomous" else weekly).append(trade)

    def summarise(trades):
        return {
            "count": len(trades),
            "buys": sum(1 for t in trades if t["action"] == "BUY"),
            "exits": sum(1 for t in trades if t["action"] in ("SELL", "TRIM")),
            "gross_usd": round(sum(t["amount_usd"] for t in trades), 2),
        }

    return {"weekly": summarise(weekly), "intraday": summarise(intraday)}


def churn_audit(theses):
    """Claims stuck on `unassessed` mean the commentary layer is failing quietly."""
    stuck, total = [], 0
    for symbol, position in theses.items():
        if symbol.startswith("_"):
            continue
        for claim in position.get("claims", []):
            total += 1
            if claim.get("status") == "unassessed":
                stuck.append({"claim_id": claim["id"], "symbol": symbol,
                              "last_updated": claim.get("last_updated")})
    return {"claims": total, "unassessed": stuck}


# ------------------------------------------------------------------- the report

def build_scorecard(state_dir, fetch_prices=True):
    text = open(LOG_PATH, encoding="utf-8").read() if os.path.exists(LOG_PATH) else ""
    rounds = read_rounds(text)
    portfolio = read_json(PORTFOLIO_PATH, {"trade_history": []})
    theses = read_json(THESES_PATH, {})

    exited = {t["symbol"] for t in portfolio.get("trade_history", [])
              if t["action"] in ("SELL", "TRIM")}
    prices = fetch_prices_since(exited) if fetch_prices else {}

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "weekly_rounds": len(rounds),
        "intraday_rounds": len(INTRADAY_HEADING.findall(text)),
        "labels": label_audit(rounds),
        "exits": exit_audit(portfolio, prices),
        "thresholds": threshold_audit(os.path.join(state_dir, "triggers.jsonl"), theses),
        "attribution": attribution_audit(portfolio),
        "churn": churn_audit(theses),
    }


def render(scorecard):
    lines = [f"# Audit scorecard — {scorecard['generated_at']}", "",
             "Computed from the repository's own record: the decision log, the trade "
             "history, the thesis file and the permanent trigger log. No model produced "
             "any number on this page.", "",
             f"{scorecard['weekly_rounds']} weekly rounds · "
             f"{scorecard['intraday_rounds']} intraday decisions", ""]

    labels = scorecard["labels"]
    lines += ["## Label against action", ""]
    if labels["broken_but_held"]:
        lines.append("A thesis marked BROKEN while the position was held — the "
                     "instructions require an action or a different label:")
        lines.append("")
        for item in labels["broken_but_held"]:
            lines.append(f"- round #{item['round']}: **{item['symbol']}** marked "
                         f"{item['label']}, no trade that round")
    else:
        lines.append("No thesis was marked BROKEN and held without an action.")
    lines.append("")
    if labels["label_streaks"]:
        lines += [f"An unsettled label ({' or '.join(sorted(UNSETTLED_LABELS))}) repeated "
                  f"for {LABEL_STREAK_LIMIT} rounds or more without an action:", ""]
        for item in labels["label_streaks"]:
            lines.append(f"- **{item['symbol']}** — {item['label']} for "
                         f"{item['rounds']} rounds, through round #{item['through_round']}")
    else:
        lines.append(f"No unsettled label was repeated {LABEL_STREAK_LIMIT} rounds "
                     "running without an action.")
    lines.append("")

    lines += ["## Exits, scored against what happened next", "",
              "The one thing the decision-maker could not know at the time. A good "
              "decision can still have a bad outcome — this measures the outcome, not "
              "the reasoning.", "",
              "| Date | Symbol | Action | Exit | Since | Move | Verdict |",
              "|---|---|---|---|---|---|---|"]
    for item in scorecard["exits"]:
        move = "—" if item["move_pct"] is None else f"{item['move_pct']:+.1f}%"
        later = "—" if item["later_price"] is None else f"{item['later_price']:.2f}"
        lines.append(f"| {item['date']} | {item['symbol']} | {item['action']} | "
                     f"{item['exit_price']:.2f} | {later} | {move} | "
                     f"{item['verdict']} |")
    lines.append("")

    thresholds = scorecard["thresholds"]
    lines += ["## Threshold quality", "",
              f"Based on {thresholds['checks_recorded']} recorded checks. A condition "
              "that fires on most checks measures noise; one that has never fired was "
              "tied to a number that does not happen.", ""]
    if not thresholds["checks_recorded"]:
        lines.append("No checks recorded yet — the trigger log starts empty and fills as "
                     "the detector runs.")
    else:
        lines += ["| Claim | Condition | Severity | Fired | Acted on | Quality |",
                  "|---|---|---|---|---|---|"]
        for row in thresholds["conditions"]:
            lines.append(f"| {row['claim_id']} | {row['type']} | {row['severity']} | "
                         f"{row['fired']} | {row['acted_on']} | {row['quality']} |")
    lines.append("")

    attribution = scorecard["attribution"]
    lines += ["## Decision cadence", "",
              "| Cadence | Trades | Buys | Exits | Gross traded |",
              "|---|---|---|---|---|"]
    for name in ("weekly", "intraday"):
        row = attribution[name]
        lines.append(f"| {name} | {row['count']} | {row['buys']} | {row['exits']} | "
                     f"{row['gross_usd']:,.0f} $ |")
    lines.append("")

    churn = scorecard["churn"]
    lines += ["## Commentary health", ""]
    if churn["unassessed"]:
        lines.append(f"{len(churn['unassessed'])} of {churn['claims']} claims are stuck "
                     "on `unassessed` — the commentary layer rejected its own output and "
                     "the claim was left unchanged:")
        lines.append("")
        for item in churn["unassessed"]:
            lines.append(f"- {item['claim_id']} ({item['symbol']}), last updated "
                         f"{item['last_updated']}")
    else:
        lines.append(f"All {churn['claims']} claims carry an assessed status.")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compute the audit scorecard")
    parser.add_argument("--json", action="store_true",
                        help="print the scorecard as JSON instead of Markdown")
    parser.add_argument("--no-prices", action="store_true",
                        help="skip exit scoring (no network)")
    parser.add_argument("--review", action="store_true",
                        help="also run the two adversarial auditors (needs an API key)")
    parser.add_argument("--out", default=REPORT_PATH)
    parser.add_argument("--state-dir", default=os.path.join(BASE, "state"))
    args = parser.parse_args()

    scorecard = build_scorecard(args.state_dir, fetch_prices=not args.no_prices)
    if args.json:
        print(json.dumps(scorecard, ensure_ascii=False, indent=2))
        return 0

    report = render(scorecard)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(report + "\n")
    print(report)

    if args.review:
        # The scorecard is computed first and passed in: the auditors argue from what
        # happened, not from the same prose the decision-maker wrote.
        import reviewers
        reviewers.review(scorecard, args.state_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
