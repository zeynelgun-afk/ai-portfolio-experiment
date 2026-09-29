"""Dated, non-scoring macro context for the research-only theme radar."""
import math
import os

import requests


def _valid(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _fred_series(series_id, api_key):
    response = requests.get('https://api.stlouisfed.org/fred/series/observations',
        params={'series_id': series_id, 'api_key': api_key, 'file_type': 'json',
                'sort_order': 'desc', 'limit': 8}, timeout=15)
    response.raise_for_status()
    payload = response.json()
    rows = []
    for row in payload.get('observations', []):
        value = _valid(row.get('value'))
        if value is not None and row.get('date'):
            rows.append({'date': row['date'], 'value': value})
    if not rows:
        raise ValueError('No observations')
    latest = rows[0]
    older = next((row for row in rows[5:] if row['date'] < latest['date']), None)
    return {'series': series_id, 'value': latest['value'], 'as_of': latest['date'],
            'change_over_observations': latest['value'] - older['value'] if older else None,
            'comparison_as_of': older['date'] if older else None}


def _electricity_sales(api_key):
    response = requests.get('https://api.eia.gov/v2/electricity/retail-sales/data/',
        params={'api_key': api_key, 'frequency': 'monthly', 'data[0]': 'sales',
                'sort[0][column]': 'period', 'sort[0][direction]': 'desc', 'length': 5000},
        timeout=20)
    response.raise_for_status()
    rows = response.json().get('response', {}).get('data', [])
    by_period = {}
    # EIA's ALL sector already contains each state's total. Sum that one row per
    # state and period, excluding any national aggregate to avoid double counting.
    for row in rows:
        state = str(row.get('stateid') or '').upper()
        period = row.get('period')
        value = _valid(row.get('sales'))
        if (state in {'US', 'USA', 'NUS'} or row.get('sectorid') != 'ALL' or
                not period or value is None):
            continue
        by_period[period] = by_period.get(period, 0.0) + value
    periods = sorted(by_period, reverse=True)
    if not periods:
        raise ValueError('No electricity sales observations')
    latest = periods[0]
    prior_year = next((p for p in periods if p[:4] == str(int(latest[:4]) - 1) and p[5:] == latest[5:]), None)
    prior_month = periods[1] if len(periods) > 1 else None
    return {'series': 'EIA US electricity retail sales (sum of state ALL-sector observations)',
            'value': by_period[latest], 'units': 'million kWh', 'as_of': latest,
            'year_over_year_pct': (100 * (by_period[latest] / by_period[prior_year] - 1)
                                    if prior_year and by_period[prior_year] else None),
            'prior_year_as_of': prior_year,
            'month_over_month_pct': (100 * (by_period[latest] / by_period[prior_month] - 1)
                                      if prior_month and by_period[prior_month] else None),
            'prior_month_as_of': prior_month}


def collect():
    """Return available context independently; missing credentials/data never block Scout."""
    result = {'status': 'partial', 'scoring_use': False, 'fred': [], 'eia': [], 'failures': []}
    fred_key = os.environ.get('FRED_API_KEY', '').strip()
    eia_key = os.environ.get('EIA_API_KEY', '').strip()
    if fred_key:
        for series in ('DGS10', 'FEDFUNDS'):
            try:
                result['fred'].append(_fred_series(series, fred_key))
            except Exception:
                result['failures'].append({'provider': 'FRED', 'series': series,
                                           'reason': 'unavailable_or_invalid'})
    else:
        result['failures'].append({'provider': 'FRED', 'reason': 'credential_unavailable'})
    if eia_key:
        try:
            result['eia'].append(_electricity_sales(eia_key))
        except Exception:
            result['failures'].append({'provider': 'EIA', 'series': 'electricity_retail_sales',
                                       'reason': 'unavailable_or_invalid'})
    else:
        result['failures'].append({'provider': 'EIA', 'reason': 'credential_unavailable'})
    if result['fred'] or result['eia']:
        result['status'] = 'available' if not result['failures'] else 'partial'
    else:
        result['status'] = 'unavailable'
    return result
