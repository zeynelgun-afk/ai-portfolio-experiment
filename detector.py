#!/usr/bin/env python3
"""Event-driven reassessment — the deterministic change detector.

Why this exists: the commentary written in the Saturday round went stale during the week.
When the price slipped below the 50-day average on a Monday, theses.json still read
"+14.9% above the average". The principle: **data flows continuously, commentary is
updated only when the meaning changes.**

Price conditions are deterministic. Unseen news is assessed by a configurable model;
failed news assessments stay pending for retry. Commentary and trading decisions
belong to reassess.py.

Exit codes (the workflow branches on these):
    0  -> nothing changed (or only a `warning`-level flag)
    10 -> `claim` level: a single claim will be rewritten
    20 -> `thesis` level: the position's whole thesis will be re-evaluated

Anti-flapping, three layers together:
  * Hysteresis    — a condition counts as breached only after 2 consecutive checks.
                    If the data looks suspect (the price deviates more than 25% from
                    the previous close) 3 checks are required: a corrupt bar is filtered
                    out at the cost of one cycle, while a genuine crash is still caught
                    within 60 minutes.
  * Recovery band — 1% of the threshold. A drop below 850 triggers; clearing it takes a
                    move back above 858.5, so a price oscillating around the threshold
                    produces no signal.
  * Cooldown      — the same claim is not rewritten twice within 4 hours.

Usage:
    python detector.py                            # live intraday data
    python detector.py --full-review              # review every claim, threshold or not
    python detector.py --dry-run                  # writes no state files
    python detector.py --fixed-data tests/sample.json   # no network, data from a file
"""

import argparse
import json
import math
import os
import random
import sys
import time
from datetime import date, datetime, time as clock, timedelta, timezone
from market_time import market_open, recent
from prompt_policy import policy

BASE = os.path.dirname(os.path.abspath(__file__))
THESES_PATH = os.path.join(BASE, "theses.json")
PORTFOLIO_PATH = os.path.join(BASE, "portfolio.json")

# The recovery band is 1% of the threshold. One constant, because defining a separate
# band per condition type would turn the band itself into a negotiable number.
BAND_RATIO = 0.01
COOLDOWN_HOURS = 4
REQUIRED_STREAK = 2
REQUIRED_STREAK_SUSPECT = 3
# A price deviating from the previous close by more than this is treated as suspect
# (a corrupt yfinance bar).
SUSPECT_DEVIATION_PCT = 25.0

SEVERITY_CODE = {"warning": 0, "claim": 10, "thesis": 20}

# yfinance is rate-limited and occasionally flaky. A single failed call should not look
# like "the thesis could not be measured", so fetches retry with exponential backoff.
FETCH_ATTEMPTS = 3
BACKOFF_BASE = 3.0  # seconds; doubles each attempt, with jitter
SLEEP = time.sleep  # tests replace this to disable real waiting

# US session (UTC). Daylight-saving drift is not chased: the window is deliberately
# generous, and a run outside it refreshes commentary but never executes a trade
# (see execute_trade.py).
SESSION_OPEN = clock(13, 30)
SESSION_CLOSE = clock(20, 0)


def env(name, default=""):
    """Every env read is stripped: Actions secrets can carry a trailing newline."""
    return (os.environ.get(name) or default).strip()


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------- data fetching


def _retry(label, fetch):
    """Call `fetch` with exponential backoff. Returns None once attempts run out."""
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            result = fetch()
            if result is not None and not (hasattr(result, "empty") and result.empty):
                return result
            reason = "empty response"
        except Exception as error:  # yfinance raises a wide range of types
            reason = str(error)
        if attempt == FETCH_ATTEMPTS:
            print(f"WARNING: {label} failed after {FETCH_ATTEMPTS} attempts ({reason})")
            return None
        delay = BACKOFF_BASE * (2 ** (attempt - 1)) * (0.5 + random.random())
        print(f"WARNING: {label} failed ({reason}) — retrying in {delay:.1f}s "
              f"({attempt}/{FETCH_ATTEMPTS})")
        SLEEP(delay)
    return None


def _series(frame, field, symbol):
    """yfinance returns different column shapes for one vs. many symbols."""
    try:
        section = frame[field]
    except (KeyError, TypeError):
        return None
    if hasattr(section, "columns"):
        if symbol not in section.columns:
            return None
        section = section[symbol]
    return section.dropna()


def _last_valid(series):
    if series is None or len(series) == 0:
        return None
    value = float(series.iloc[-1])
    return value if math.isfinite(value) else None


def collect_live_data(symbols, earnings_fallback=None):
    """Intraday price + previous close + 20-day average volume + earnings date.

    The price comes from the latest intraday 5-minute bar (yfinance, ~15 minutes
    delayed). If the intraday fetch fails the code falls back to the daily close and
    records that in `data_source` — quietly calling daily data "live" would be the very
    staleness this system exists to prevent.
    """
    import yfinance as yf

    joined = " ".join(symbols)
    daily = _retry("daily series", lambda: yf.download(
        joined, period="120d", interval="1d", auto_adjust=False, progress=False))
    if daily is None:
        raise RuntimeError("Daily data unavailable — no series for any symbol")

    intraday = _retry("intraday series", lambda: yf.download(
        joined, period="1d", interval="5m", auto_adjust=False, progress=False,
        prepost=False))
    if intraday is None:
        print("WARNING: intraday fetch failed — falling back to the daily close")

    result = {}
    for symbol in symbols:
        closes = _series(daily, "Close", symbol)
        if closes is None or len(closes) < 2:
            print(f"WARNING {symbol}: daily close series too short — skipped")
            continue

        today = date.today()
        # During the session the last row of the daily series is today's partial bar;
        # the previous close is the row before it, not that one.
        if closes.index[-1].date() == today and len(closes) >= 2:
            previous_close = float(closes.iloc[-2])
            daily_last = float(closes.iloc[-1])
        else:
            previous_close = float(closes.iloc[-1])
            daily_last = previous_close

        bars = _series(intraday, "Close", symbol) if intraday is not None else None
        price = _last_valid(bars)
        price_at = bars.index[-1].isoformat() if price is not None else None
        source = "intraday_5m"
        if price is None:
            price, source = daily_last, "daily_close"
            price_at = closes.index[-1].isoformat()
        elif not recent(price_at, now_utc()):
            source = "stale_intraday_5m"

        volumes = _series(daily, "Volume", symbol)
        volume_avg_20d = None
        if volumes is not None and len(volumes) >= 21:
            # Today's partial volume must not drag the average down: last 20 full days.
            window = volumes.iloc[-21:-1] if volumes.index[-1].date() == today \
                else volumes.iloc[-20:]
            average = float(window.mean())
            volume_avg_20d = average if math.isfinite(average) and average > 0 else None

        volume = None
        if intraday is not None:
            intraday_volume = _series(intraday, "Volume", symbol)
            if intraday_volume is not None and len(intraday_volume):
                volume = float(intraday_volume.sum())
        if volume is None and volumes is not None and len(volumes):
            volume = float(volumes.iloc[-1])

        result[symbol] = {
            "price": round(price, 4),
            "previous_close": round(previous_close, 4),
            "volume": volume,
            "volume_avg_20d": volume_avg_20d,
            "earnings_date": _earnings_date(yf, symbol, earnings_fallback),
            "data_source": source,
            "price_at": price_at,
        }

    # Fetch breaking news via FMP API
    fmp_key = env("FMP_API_KEY")
    if fmp_key:
        try:
            import urllib.request
            req = urllib.request.Request(f"https://financialmodelingprep.com/stable/news/stock?symbols={','.join(symbols)}&limit=30&apikey={fmp_key}")
            with urllib.request.urlopen(req, timeout=10) as res:
                news_data = json.loads(res.read().decode("utf-8"))
                for item in news_data:
                    sym = item.get("symbol")
                    if sym and sym in result:
                        result[sym].setdefault("recent_news", []).append(item)
        except Exception as e:
            raise RuntimeError("FMP news fetch failed; news monitoring is incomplete") from None

    return result


def _earnings_date(yf, symbol, fallback):
    """yfinance calendar -> the portfolio.json fallback -> none. Never raises."""
    try:
        calendar = yf.Ticker(symbol).calendar
        if calendar:
            dates = calendar.get("Earnings Date") or []
            if dates:
                first = dates[0]
                return first.isoformat() if hasattr(first, "isoformat") else str(first)
    except Exception:
        pass
    return (fallback or {}).get(symbol)


# -------------------------------------------------------------- condition measurement


def measure(condition, symbol, data, stop, today):
    """Measure one condition.

    Returns (measured, threshold, breach_side, detail), or None when unmeasurable.
    `breach_side` "below": breached when the measurement falls below the threshold;
    "above": breached when it rises above it.
    """
    kind = condition.get("type")
    row = data.get(symbol, {})
    price = row.get("price")

    if kind == "price_below":
        if price is None:
            return None
        return price, float(condition["value"]), "below", f"price {price:.2f}"

    if kind == "stop_proximity_pct":
        if price is None or not stop:
            return None
        distance = (price / float(stop) - 1) * 100
        return (round(distance, 2), float(condition["value"]), "below",
                f"stop distance {distance:+.1f}% (stop {stop})")

    if kind == "volume_ratio_20d":
        volume, average = row.get("volume"), row.get("volume_avg_20d")
        if not volume or not average:
            return None
        ratio = volume / average
        return round(ratio, 2), float(condition["value"]), "above", f"volume {ratio:.1f}x"

    if kind == "daily_change_pct":
        previous = row.get("previous_close")
        if price is None or not previous:
            return None
        change = (price / previous - 1) * 100
        return (round(change, 2), float(condition["value"]), "below",
                f"daily change {change:+.1f}%")

    if kind == "sector_etf_change_pct":
        etf = condition.get("symbol", "SMH")
        row_etf = data.get(etf, {})
        if row_etf.get("price") is None or not row_etf.get("previous_close"):
            return None
        change = (row_etf["price"] / row_etf["previous_close"] - 1) * 100
        return (round(change, 2), float(condition["value"]), "below",
                f"{etf} {change:+.1f}%")

    if kind == "earnings_approaching":
        raw = row.get("earnings_date")
        if not raw:
            return None  # no earnings date: skip the condition, do not fail
        try:
            earnings = date.fromisoformat(str(raw)[:10])
        except ValueError:
            return None
        remaining = (earnings - today).days
        if remaining < 0:
            return None  # a past earnings date triggers nothing
        return (remaining, float(condition["days"]), "below",
                f"{remaining} days to earnings ({earnings.isoformat()})")

    return None  # unknown types are skipped silently; the schema may grow later


def is_breach(measured, threshold, side):
    return measured < threshold if side == "below" else measured > threshold


def is_cleared(measured, threshold, side):
    """Recovery band: leaving a breach requires clearing the threshold by the band."""
    band = abs(threshold) * BAND_RATIO
    return measured >= threshold + band if side == "below" \
        else measured <= threshold - band


# ----------------------------------------------------------------------- state I/O


def read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError) as error:
        print(f"WARNING: could not read {os.path.basename(path)} ({error}) — "
              "starting from scratch")
        return default


def append_trigger_log(path, report):
    """Append this check's confirmed breaches to a permanent, line-delimited log.

    violations.json is overwritten on every run, so it can say what is true *now* but
    never what has been true. Threshold quality — is this condition firing constantly
    (noise), or has a thesis-level condition never fired at all (decoration)? — is a
    question about history, so the history has to be kept. One line per confirmed
    breach, appended, never rewritten.
    """
    confirmed = [record for record in report["conditions"].values()
                 if record.get("confirmed")]
    if not confirmed:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        for record in confirmed:
            handle.write(json.dumps({
                "checked_at": report["checked_at"],
                "symbol": record["symbol"],
                "claim_id": record["claim_id"],
                "type": record["type"],
                "severity": record["severity"],
                "measured": record["measured"],
                "threshold": record["threshold"],
                "acted_on": any(item["claim_id"] == record["claim_id"]
                                and item["condition_type"] == record["type"]
                                for item in report["triggered"]),
            }, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def in_cooldown(cooldown, key, moment):
    stamp = cooldown.get(key)
    if not stamp:
        return False
    try:
        last = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    return moment - last < timedelta(hours=COOLDOWN_HOURS)


# ---------------------------------------------------------------------------- run


def check_news_shock(symbol, thesis_summary, news_items):
    """Return True/False only for a completed assessment; None means retry later."""
    import urllib.request
    api_key = env("OPENROUTER_API_KEY")
    if not api_key or not news_items or not thesis_summary:
        return None, "news assessment prerequisites are missing"
    news_text = "\n".join([f"- {n.get('title', '')} ({n.get('publishedDate', '')})" for n in news_items])
    prompt = f"You are a strict risk management AI.\nTHESIS SUMMARY FOR {symbol}:\n{thesis_summary}\n\nBREAKING NEWS:\n{news_text}\n\nDoes this breaking news fundamentally invalidate or severely contradict the core thesis summary above? Answer strictly with YES or NO."
    try:
        req = urllib.request.Request(
            env("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            data=json.dumps({"model": env("OPENROUTER_MODEL_NEWS", env("OPENROUTER_MODEL_FAST", "anthropic/claude-haiku-4.5")), "messages": [{"role": "system", "content": policy()}, {"role": "user", "content": prompt}], "temperature": 0.0}).encode("utf-8")
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            answer = json.loads(res.read().decode("utf-8"))["choices"][0]["message"]["content"].strip().upper()
            if answer == "YES":
                return True, f"News Shock: {news_items[0].get('title', '')}"
            if answer == "NO":
                return False, ""
            return None, "news model did not return YES or NO"
    except Exception as e:
        print(f"WARNING: News shock LLM failed for {symbol}: {e}")
    return None, "news model request failed"


def run(theses, data, stops, previous_state, cooldown, moment, full_review=False, last_news=None, new_last_news=None, assess_news=True):
    """Measure conditions; optionally assess unseen news using the news model."""
    today = moment.date()
    state, triggered, flags = {}, [], []
    state_changed = False
    news_errors = []

    for symbol, position in theses.items():
        if symbol.startswith("_"):
            continue

        # News Sentiment Check
        recent_news = data.get(symbol, {}).get("recent_news", [])
        if assess_news and recent_news and last_news is not None and new_last_news is not None:
            recent_news = sorted(recent_news, key=lambda n: n.get("publishedDate", ""), reverse=True)
            latest_date = recent_news[0].get("publishedDate", "")
            last_checked = last_news.get(symbol, "")
            if latest_date and latest_date > last_checked:
                new_items = [n for n in recent_news if n.get("publishedDate", "") > last_checked]
                if new_items:
                    is_shock, shock_detail = check_news_shock(symbol, position.get("thesis_summary", ""), new_items)
                    if is_shock is None:
                        news_errors.append({"symbol": symbol, "error": shock_detail})
                    else:
                        new_last_news[symbol] = latest_date
                        state_changed = True
                    if is_shock:
                        triggered.append({
                            "symbol": symbol,
                            "claim_id": "news_shock",
                            "severity": "thesis",
                            "condition_type": "sentiment",
                            "measured": 1,
                            "threshold": 0,
                            "trigger": shock_detail,
                            "cooldown_key": f"thesis:{symbol}"
                        })

        row = data.get(symbol, {})
        suspect = False
        if row.get("price") and row.get("previous_close"):
            deviation = abs(row["price"] / row["previous_close"] - 1) * 100
            suspect = deviation > SUSPECT_DEVIATION_PCT
        required = REQUIRED_STREAK_SUSPECT if suspect else REQUIRED_STREAK

        for claim in position.get("claims", []):
            for index, condition in enumerate(claim.get("conditions", [])):
                key = f"{claim['id']}#{index}"
                previous = previous_state.get(key, {})
                measured = measure(condition, symbol, data, stops.get(symbol), today)
                if measured is None:
                    # An unmeasurable condition keeps its previous state; "no data" is
                    # not a breach.
                    if previous:
                        state[key] = dict(previous, unmeasurable=True)
                    continue
                value, threshold, side, detail = measured

                if previous.get("breach"):
                    breach = not is_cleared(value, threshold, side)
                else:
                    breach = is_breach(value, threshold, side)

                streak = (previous.get("streak", 0) + 1) if breach else 0
                confirmed = breach and streak >= required
                record = {
                    "symbol": symbol,
                    "claim_id": claim["id"],
                    "type": condition["type"],
                    "severity": condition.get("severity", "warning"),
                    "breach": breach,
                    "streak": streak,
                    "confirmed": confirmed,
                    "required_streak": required,
                    "data_suspect": suspect,
                    "measured": value,
                    "threshold": threshold,
                    "detail": detail,
                    "first_seen": previous.get("first_seen")
                    if breach and previous.get("breach")
                    else (iso(moment) if breach else None),
                }
                state[key] = record

                for field in ("breach", "streak", "confirmed"):
                    if previous.get(field) != record[field]:
                        state_changed = True

                if not confirmed:
                    continue
                severity = record["severity"]
                if severity == "warning":
                    flags.append(record)
                    continue
                lock = f"thesis:{symbol}" if severity == "thesis" else claim["id"]
                if in_cooldown(cooldown, lock, moment):
                    record["cooldown"] = True
                    continue
                triggered.append({
                    "symbol": symbol,
                    "claim_id": claim["id"],
                    "severity": severity,
                    "condition_type": condition["type"],
                    "measured": value,
                    "threshold": threshold,
                    "trigger": detail,
                    "cooldown_key": lock,
                })

    code = 0
    if triggered:
        code = max(SEVERITY_CODE[item["severity"]] for item in triggered)
    elif full_review:
        code = 10  # a bulk review is requested even though no threshold was crossed

    return {
        "checked_at": iso(moment),
        "market_open": market_open(moment),
        "full_review": full_review,
        "code": code,
        "conditions": state,
        "triggered": triggered,
        "flags": flags,
        "state_changed": state_changed or bool(triggered),
        "news_errors": news_errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Measure thesis validity conditions")
    parser.add_argument("--dry-run", action="store_true",
                        help="report only; write no state files")
    parser.add_argument("--fixed-data", metavar="FILE",
                        help="read data from this JSON file instead of the network")
    parser.add_argument("--full-review", action="store_true",
                        help="review every claim even if no threshold was crossed")
    parser.add_argument("--state-dir", default=os.path.join(BASE, "state"))
    args = parser.parse_args()

    theses = read_json(THESES_PATH, {})
    if not [key for key in theses if not key.startswith("_")]:
        print("No claims in theses.json — detector skipped")
        return 0

    portfolio = read_json(PORTFOLIO_PATH, {"positions": []})
    stops = {p["symbol"]: p.get("stop_weekly_close") for p in portfolio["positions"]}
    earnings_fallback = {p["symbol"]: p.get("next_earnings")
                         for p in portfolio["positions"]}

    moment = now_utc()
    if args.fixed_data:
        fixture = read_json(os.path.join(BASE, args.fixed_data), {})
        data = fixture.get("symbols", fixture)
        if fixture.get("time"):
            moment = datetime.fromisoformat(fixture["time"].replace("Z", "+00:00"))
    else:
        etfs = {condition.get("symbol", "SMH")
                for position in theses.values() if isinstance(position, dict)
                for claim in position.get("claims", [])
                for condition in claim.get("conditions", [])
                if condition.get("type") == "sector_etf_change_pct"}
        symbols = sorted({k for k in theses if not k.startswith("_")} | etfs)
        data = collect_live_data(symbols, earnings_fallback)

    violations_path = os.path.join(args.state_dir, "violations.json")
    cooldown_path = os.path.join(args.state_dir, "cooldown.json")
    last_news_path = os.path.join(args.state_dir, "last_news.json")
    
    previous = read_json(violations_path, {}).get("conditions", {})
    cooldown = read_json(cooldown_path, {})
    last_news = read_json(last_news_path, {})
    new_last_news = last_news.copy()

    report = run(theses, data, stops, previous, cooldown, moment, args.full_review, last_news, new_last_news,
                 assess_news=not args.dry_run)
    report["data"] = {symbol: data.get(symbol, {}) for symbol in sorted(data)}
    report["news_previous"] = last_news

    if not args.dry_run:
        write_json(violations_path, report)
        write_json(last_news_path, new_last_news)
        append_trigger_log(os.path.join(args.state_dir, "triggers.jsonl"), report)

    # --- human-readable summary ---
    print(f"Check {report['checked_at']} · market open: {report['market_open']} · "
          f"code {report['code']}")
    for item in report["triggered"]:
        print(f"  [{item['severity'].upper()}] {item['symbol']} {item['claim_id']}: "
              f"{item['trigger']} (threshold {item['threshold']})")
    for item in report["flags"]:
        print(f"  [flag] {item['symbol']} {item['claim_id']}: {item['detail']}")
    pending = [key for key, value in report["conditions"].items()
               if value.get("breach") and not value.get("confirmed")]
    if pending:
        print(f"  awaiting confirmation (hysteresis): {', '.join(sorted(pending))}")
    if not report["triggered"] and not report["flags"]:
        print("  nothing changed")

    gh_output = env("GITHUB_OUTPUT")
    if gh_output:
        thesis_symbols = sorted({item["symbol"] for item in report["triggered"]
                                 if item["severity"] == "thesis"})
        summary = "; ".join(f"{i['symbol']} {i['claim_id']}: {i['trigger']}"
                            for i in report["triggered"]) or "none"
        with open(gh_output, "a", encoding="utf-8") as handle:
            handle.write(f"code={report['code']}\n")
            handle.write(f"news_error_count={len(report['news_errors'])}\n")
            handle.write(f"market_open={'true' if report['market_open'] else 'false'}\n")
            handle.write(
                f"state_changed={'true' if report['state_changed'] else 'false'}\n")
            handle.write(f"thesis_symbols={','.join(thesis_symbols)}\n")
            handle.write(f"trigger_summary={' '.join(summary.splitlines())}\n")

    return report["code"]


if __name__ == "__main__":
    sys.exit(main())
