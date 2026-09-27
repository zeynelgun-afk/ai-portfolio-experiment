#!/usr/bin/env python3
"""Collect market data for the weekly decision round."""
import json
import math
from datetime import datetime, timedelta

import yfinance as yf

# Portfolio positions + watchlist
# PLTR and VRT were dropped from the list in round #7; the fetch list must stay identical
# to the watchlist.
SYMBOLS = ['MU', 'AMD', 'SNDK', 'ANET', 'AVGO', 'NVDA', 'TSM', 'MRVL', 'MSFT', 'GOOGL']

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
             'Sunday']

results = {}
missing_data = []


def day_name_of(value):
    """The weekday name for a date. Names live here so they are never computed by hand."""
    if value is None:
        return None
    try:
        return DAY_NAMES[value.weekday()]
    except AttributeError:
        return None


def headline(item):
    """The yfinance news schema varies by version: a flat 'title' or 'content.title'."""
    return item.get('title') or item.get('content', {}).get('title', '')


for symbol in SYMBOLS:
    try:
        ticker = yf.Ticker(symbol)
        # A 200-day SMA needs at least 200 trading days — 6mo (~126 days) is not enough.
        history = ticker.history(period="2y")

        if history.empty:
            print(f"WARNING: no data for {symbol}")
            missing_data.append(f"{symbol}: no price data")
            continue

        # yfinance can return a final row that is entirely NaN (an unclosed or empty day).
        # That row made price, SMAs and returns ALL NaN through .iloc[-1], while RSI still
        # looked healthy because ewm skips NaN — the failure was silent. (See round #6.)
        history = history[history['Close'].notna()]
        if history.empty:
            print(f"WARNING: no valid close for {symbol}")
            missing_data.append(f"{symbol}: no price data (every close is NaN)")
            continue

        # The real day the price belongs to — the report's date label must rest on this.
        # The day name comes from here too: round #7 wrote "4 September, Wednesday" (a
        # Friday) and "2 September, Monday" (a Wednesday); a hand-computed day name errs.
        price_day = history.index[-1].date()
        price_date = price_day.isoformat()
        price_day_name = DAY_NAMES[price_day.weekday()]

        last_price = history['Close'].iloc[-1]

        sma50 = history['Close'].rolling(window=50).mean().iloc[-1] \
            if len(history) >= 50 else None
        sma200 = history['Close'].rolling(window=200).mean().iloc[-1] \
            if len(history) >= 200 else None

        # RSI (Wilder)
        delta = history['Close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
        rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] else float('inf')
        rsi = 100 - (100 / (1 + rs))

        return_1m = ((history['Close'].iloc[-1] / history['Close'].iloc[-21]) - 1) * 100 \
            if len(history) >= 21 else None
        return_3m = ((history['Close'].iloc[-1] / history['Close'].iloc[-63]) - 1) * 100 \
            if len(history) >= 63 else None
        # The weekly move — the instructions' "investigate the cause" threshold (±10%)
        # reads this field.
        return_1w = ((history['Close'].iloc[-1] / history['Close'].iloc[-6]) - 1) * 100 \
            if len(history) >= 6 else None

        try:
            calendar = ticker.calendar
            earnings_date = calendar.get('Earnings Date', [None])[0] if calendar else None
        except Exception:
            earnings_date = None
        if earnings_date is None:
            missing_data.append(f"{symbol}: earnings date unavailable")

        try:
            news_titles = [title for title in
                           (headline(item) for item in (ticker.news or [])[:5]) if title]
        except Exception:
            news_titles = []
        if not news_titles:
            missing_data.append(f"{symbol}: no news headlines")

        def numeric(value, field, places=2):
            """NaN/Inf never reach the JSON: return None and record it as missing."""
            if value is None or not math.isfinite(float(value)):
                missing_data.append(f"{symbol}: could not compute {field}")
                return None
            return round(float(value), places)

        results[symbol] = {
            'last_price': numeric(last_price, 'price'),
            'price_date': price_date,
            'price_day_name': price_day_name,
            'sma50': numeric(sma50, 'SMA50'),
            'sma200': numeric(sma200, 'SMA200'),
            'rsi': numeric(rsi, 'RSI', 1),
            'return_1w_pct': numeric(return_1w, '1w return', 1),
            'return_1m_pct': numeric(return_1m, '1m return', 1),
            'return_3m_pct': numeric(return_3m, '3m return', 1),
            'earnings_date': str(earnings_date) if earnings_date else None,
            'earnings_day_name': day_name_of(earnings_date),
            'news_titles': news_titles,
        }

        if results[symbol]['last_price'] is None:
            print(f"WARNING {symbol}: could not compute the price")
        else:
            print(f"OK {symbol}: ${last_price:.2f} ({price_date})")

    except Exception as error:
        print(f"ERROR {symbol}: {error}")
        missing_data.append(f"{symbol}: {error}")

# Date information — so the decision round never computes a day name itself.
today = datetime.now()
next_friday = today + timedelta(days=(4 - today.weekday()) % 7 or 7)
next_round = today + timedelta(days=(5 - today.weekday()) % 7 or 7)

results['_meta'] = {
    'date': today.strftime('%Y-%m-%d'),
    'day_name': DAY_NAMES[today.weekday()],
    'next_friday': f"{next_friday.strftime('%Y-%m-%d')} (Friday — the weekly close)",
    'next_round': f"{next_round.strftime('%Y-%m-%d')} (Saturday — the next decision round)",
    'symbol_count': f"{len(results)}/{len(SYMBOLS)}",
    'missing_data': missing_data,
}

with open('weekly_data.json', 'w', encoding='utf-8') as handle:
    json.dump(results, handle, indent=2, ensure_ascii=False, allow_nan=False)

print(f"\nCollected data for {len(results) - 1}/{len(SYMBOLS)} symbols")
if missing_data:
    print(f"MISSING DATA ({len(missing_data)} entries):")
    for item in missing_data:
        print(f"  - {item}")
print(f"Date: {today.strftime('%Y-%m-%d %H:%M:%S')} ({DAY_NAMES[today.weekday()]})")
