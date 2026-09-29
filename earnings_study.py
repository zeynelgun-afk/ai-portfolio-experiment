"""Read-only earnings feasibility pilot; historical snapshots are NOT point-in-time proof."""
import argparse
from datetime import datetime, timezone, timedelta, date
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

import pandas as pd
import pandas_market_calendars as calendars
import market_data

BASE = Path(__file__).resolve().parent
DEFAULT_SYMBOLS = ('AEHR', 'ACMR', 'PDFS', 'PLAB', 'AOSL', 'ICHR')
LIMITATIONS = [
    'Historical consensus vintages are unverified; current downloaded estimates may be revised.',
    'Announcement times are absent; entry is the next NYSE session CLOSE, not the first tradable price.',
    'Manually selected semiconductor-related survivors; no representative small-cap or delisted universe.',
    'Event-date capitalization and liquidity eligibility have not been established.',
    'IWM is a broad size proxy, not a sector/size-matched control; overlapping events are dependent.',
    'Cost scenarios are assumptions; spreads, impact, borrow costs and intraday drawdowns are not measured.',
    'Text/guidance/peer-confirmation strategies and out-of-sample validation are not tested.',
]


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def classify(row):
    fields = ('epsActual', 'epsEstimated', 'revenueActual', 'revenueEstimated')
    if not all(finite(row.get(k)) for k in fields):
        return 'missing_consensus_or_actual'
    if row['revenueEstimated'] <= 0 or row['revenueActual'] < 0:
        return 'invalid_revenue'
    eps = row['epsActual'] > row['epsEstimated']
    revenue = row['revenueActual'] > row['revenueEstimated']
    if eps and revenue:
        return 'eps_and_revenue_beat'
    if eps:
        return 'eps_beat_only'
    return 'no_eps_beat'


def measure(stock, benchmark, days, entry, end, cost_bps):
    """Require every expected session; no nearest-bar fill or shortened horizons."""
    required = days[(days >= entry) & (days <= end)]
    if len(required) < 2:
        return {'status': 'insufficient_window'}
    values = []
    for frame in (stock, benchmark):
        if frame.index.has_duplicates:
            return {'status': 'duplicate_price_dates'}
        if 'total_close' not in frame:
            return {'status': 'missing_adjusted_prices'}
        series = frame['total_close'].reindex(required)
        if series.isna().any() or not all(finite(v) and v > 0 for v in series):
            return {'status': 'incomplete_price_path'}
        values.append(series.astype(float))
    s, b = values
    ret = 100 * (s.iloc[-1] / s.iloc[0] - 1)
    base = 100 * (b.iloc[-1] / b.iloc[0] - 1)
    return {'status': 'measured', 'entry_date': entry.date().isoformat(),
            'end_date': end.date().isoformat(), 'gross_return_pct': ret,
            'benchmark_return_pct': base, 'excess_pp': ret-base,
            'max_close_drawdown_pct': float(100 * (s/s.cummax()-1).min()),
            'net_return_pct_by_roundtrip_bps': {str(c): ret-c/100 for c in cost_bps}}


def evaluate(rows, histories, as_of, benchmark='IWM', cost_bps=(0, 25, 100)):
    if any(not finite(c) or c < 0 for c in cost_bps):
        raise ValueError('Costs must be finite nonnegative roundtrip basis points')
    sessions = calendars.get_calendar('NYSE').schedule(
        start_date=(as_of.date()-timedelta(days=1000)),
        end_date=(as_of.date()+timedelta(days=400)))
    days = sessions.index
    completed = sessions.index[sessions['market_close'] <= as_of]
    last = completed[-1]
    results = []
    for symbol, raw in sorted(rows.items()):
        dates = []
        counts = {}
        for row in raw:
            try:
                d = date.fromisoformat(row['date'])
            except (KeyError, TypeError, ValueError):
                results.append({'symbol': symbol, 'status': 'invalid_event_date'})
                continue
            dates.append((d, row))
            counts[d] = counts.get(d, 0)+1
        dates.sort(key=lambda item: item[0])
        for pos, (d, row) in enumerate(dates):
            if not as_of.date()-timedelta(days=700) <= d <= as_of.date():
                continue
            record = {'symbol': symbol, 'event_date': str(d), 'group': classify(row)}
            results.append(record)
            if row.get('symbol') != symbol or counts[d] != 1:
                record['status'] = 'issuer_or_duplicate_event'; continue
            if record['group'] in ('missing_consensus_or_actual', 'invalid_revenue'):
                record['status'] = record['group']; continue
            if symbol not in histories or benchmark not in histories:
                record['status'] = 'missing_history'; continue
            entry = days[days > pd.Timestamp(d)][0]
            index = days.get_loc(entry)
            horizons = {str(n): days[index+n] for n in (20, 60)}
            # Future scheduled dates may move; use only the next already reported event.
            if pos+1 < len(dates):
                next_date, next_row = dates[pos+1]
                if (next_date <= as_of.date() and finite(next_row.get('epsActual'))
                        and next_row.get('symbol') == symbol and counts[next_date] == 1):
                    horizons['before_next_earnings'] = days[days < pd.Timestamp(next_date)][-1]
            record.update(status='exploratory_only', outcomes={})
            for label, end in horizons.items():
                record['outcomes'][label] = ({'status': 'pending'} if end > last else
                    measure(histories[symbol], histories[benchmark], days, entry, end, cost_bps))
    summary = {}
    for row in results:
        for horizon, outcome in row.get('outcomes', {}).items():
            if outcome['status'] == 'measured':
                summary.setdefault(row['group']+':'+horizon, []).append(outcome)
    summary = {key: {'n': len(items),
                      'mean_gross_return_pct': mean(x['gross_return_pct'] for x in items),
                      'median_gross_return_pct': median(x['gross_return_pct'] for x in items),
                      'mean_excess_pp': mean(x['excess_pp'] for x in items),
                      'positive_fraction': mean(int(x['gross_return_pct'] > 0) for x in items),
                      'worst_close_drawdown_pct': min(x['max_close_drawdown_pct'] for x in items),
                      'mean_net_return_pct_by_roundtrip_bps': {
                          str(c): mean(x['net_return_pct_by_roundtrip_bps'][str(c)] for x in items)
                          for c in cost_bps}}
               for key, items in sorted(summary.items())}
    return {'status': 'exploratory_only', 'strategy_validated': False,
            'as_of': as_of.isoformat(), 'benchmark': benchmark,
            'limitations': LIMITATIONS, 'events': results, 'summary': summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symbols', nargs='+', default=list(DEFAULT_SYMBOLS))
    parser.add_argument('--replay', type=Path, help='Replay an inputs.json snapshot without network access')
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory; existing snapshots are never overwritten')
    args = parser.parse_args()
    if not 1 <= len(set(args.symbols)) <= 20:
        parser.error('Choose 1-20 unique pilot symbols')
    now = datetime.now(timezone.utc)
    if args.replay:
        encoded = args.replay.read_bytes()
        inputs = json.loads(encoded)
        histories = {}
        for symbol, records in inputs['histories'].items():
            frame = pd.DataFrame.from_dict(records, orient='index')
            frame.index = pd.to_datetime(frame.index)
            histories[symbol] = frame.sort_index()
        report = evaluate(inputs['earnings'], histories, datetime.fromisoformat(inputs['observed_at']))
        report['inputs_sha256'] = hashlib.sha256(encoded).hexdigest()
        report['code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        print('Offline replay complete:', args.output/'report.json')
        return
    args.output.mkdir(parents=True, exist_ok=False)
    earnings, histories, failures, audit = {}, {}, [], {}
    for symbol in sorted(set(args.symbols)):
        try:
            earnings[symbol] = market_data.fmp('earnings', symbol=symbol, limit=100)
            audit[symbol] = {'earnings_rows': len(earnings[symbol]),
                             'fields': sorted(set().union(*(r.keys() for r in earnings[symbol]))),
                             'consensus_vintage_verified': False,
                             'provider': 'FMP'}
        except market_data.ProviderError as exc:
            failures.append({'symbol': symbol, 'dataset': 'earnings', 'reason': str(exc)})
    for symbol in sorted(set(args.symbols) | {'IWM'}):
        try:
            histories[symbol] = market_data.return_history(symbol, now=now)
        except market_data.ProviderError as exc:
            failures.append({'symbol': symbol, 'dataset': 'prices', 'reason': str(exc)})
    report = evaluate(earnings, histories, now)
    report.update(data_audit=audit, failures=failures,
                  price_providers={s: f.attrs.get('provider') for s, f in histories.items()})
    inputs = {'observed_at': now.isoformat(), 'earnings': earnings,
              'histories': {s: {str(k.date()): v for k, v in frame.to_dict('index').items()}
                            for s, frame in histories.items()}}
    encoded = json.dumps(inputs, indent=2, allow_nan=False).encode()
    (args.output/'inputs.json').write_bytes(encoded)
    report['code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['inputs_sha256'] = hashlib.sha256(encoded).hexdigest()
    (args.output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': report['status'], 'events': len(report['events']),
                      'failures': failures, 'summary': report['summary']}, indent=2))


if __name__ == '__main__':
    main()
