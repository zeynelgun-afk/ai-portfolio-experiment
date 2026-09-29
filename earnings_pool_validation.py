"""Offline validation of an earnings-based research-pool admission rule."""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
from statistics import mean, median

import pandas_market_calendars as calendars


def _stats(rows):
    if not rows:
        return {'n': 0, 'issuers': 0}
    return {'n': len(rows), 'issuers': len({r['symbol'] for r in rows}),
            'median_gross_20_pct': median(r['gross_20'] for r in rows),
            'median_excess_20_pp': median(r['excess_20'] for r in rows),
            'positive_excess_20_fraction': mean(r['excess_20'] > 0 for r in rows),
            'median_net_20_at_100bp_pct': median(r['gross_20'] - 1 for r in rows),
            'median_gross_60_pct': median(r['gross_60'] for r in rows),
            'median_excess_60_pp': median(r['excess_60'] for r in rows),
            'positive_excess_60_fraction': mean(r['excess_60'] > 0 for r in rows),
            'median_net_60_at_100bp_pct': median(r['gross_60'] - 1 for r in rows),
            'median_drawdown_60_pct': median(r['drawdown_60'] for r in rows),
            'worst_gross_60_pct': min(r['gross_60'] for r in rows)}


def validate(report):
    events = report.get('filing_events', [])
    dates = [date.fromisoformat(e['filing_date']) for e in events if e.get('filing_date')]
    if not dates:
        raise ValueError('No dated filing events')
    schedule = calendars.get_calendar('NYSE').schedule(
        start_date=min(dates) - timedelta(days=10), end_date=max(dates) + timedelta(days=120))
    sessions = schedule.index.tz_localize(None)
    index = {d.date(): i for i, d in enumerate(sessions)}
    eligible = []
    for event in events:
        change = event.get('operating_change', {})
        if event.get('status') != 'exploratory_only' or change.get('operating_improvement_group') != 'improving':
            continue
        outcomes = event.get('outcomes', {}).get('IWM', {})
        r20, r60 = outcomes.get('20'), outcomes.get('60')
        if not r20 or not r60:
            continue
        event_day = date.fromisoformat(event['filing_date'])
        event_session = next((d for d in sessions if d.date() >= event_day), None)
        if event_session is None:
            continue
        eligible.append({'symbol': event['symbol'], 'sector': event.get('sector'),
            'filing_date': event['filing_date'], 'entry_date': event.get('entry_date'),
            'session_index': index[event_session.date()], 'gross_20': r20['gross_pct'],
            'excess_20': r20['excess_benchmark_pp'], 'gross_60': r60['gross_pct'],
            'excess_60': r60['excess_benchmark_pp'],
            'drawdown_60': r60['max_close_drawdown_pct'],
            'revenue_positive_yoy': change.get('operating_indicators', {}).get('revenue_positive_yoy'),
            'gross_margin_expanding': change.get('operating_indicators', {}).get('gross_margin_expanding'),
            'operating_cash_flow_improving': change.get('operating_indicators', {}).get('operating_cash_flow_improving')})
    eligible.sort(key=lambda r: (r['symbol'], r['filing_date']))
    # A new admission is counted only after a 60-session pool review interval;
    # intervening qualifying filings are updates, not fresh independent candidates.
    admissions, last = [], {}
    for row in eligible:
        if row['session_index'] - last.get(row['symbol'], -10_000) < 60:
            continue
        admissions.append(row)
        last[row['symbol']] = row['session_index']
    tech = [r for r in admissions if r['sector'] == 'Technology']
    all_symbols = sorted({r['symbol'] for r in admissions})
    return {'status': 'exploratory_only', 'admission_rule':
        'At least two measurable same-quarter YoY operating indicators, all known indicators positive; one counted admission per issuer per 60 NYSE sessions.',
        'baseline': 'Next-session-close proxy; 20/60-session price and IWM-relative outcomes. Not a buy/sell rule.',
        'limits': ['Survivorship and transcript coverage bias; small issuer count.',
          'Financial-statement historical values may be retrospectively restated.',
          'No point-in-time news, guidance, sector narrative or management-call catalyst labels.',
          'Assumed 100 bp round-trip deduction is illustrative and not observed execution cost.',
          'Technology sector is only a rough charter-scope proxy; large-cap and AI-infrastructure eligibility was not validated.'],
        'qualifying_filing_events': len(eligible), 'distinct_qualifying_issuers': len({r['symbol'] for r in eligible}),
        'deduplicated_pool_admissions': len(admissions), 'admission_issuers': all_symbols,
        'deduplicated_technology_sector_admissions': len(tech),
        'technology_admission_issuers': sorted({r['symbol'] for r in tech}),
        'all_admissions': _stats(admissions), 'technology_only': _stats(tech),
        'events': admissions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = validate(json.loads(args.report.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: report[k] for k in ('qualifying_filing_events', 'distinct_qualifying_issuers',
        'deduplicated_pool_admissions', 'deduplicated_technology_sector_admissions', 'all_admissions',
        'technology_only')}, indent=2))


if __name__ == '__main__':
    main()
