"""Research-only, cross-sector theme and relative-strength candidate radar."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import math
from collections import OrderedDict

import market_data

MIN_MARKET_CAP = 200_000_000
MAX_INDUSTRIES = 5
MAX_COMPANIES_PER_INDUSTRY = 3
MAX_INDUSTRY_HISTORY_CHECKS = 10


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _dated_rows(rows, field, expected_date=None):
    if not isinstance(rows, list):
        raise market_data.ProviderError('Invalid theme data rows')
    result = []
    for row in rows:
        stamp = str(row.get('date') or '')[:10]
        value = row.get(field)
        if not stamp or not _number(value):
            continue
        try:
            day = date.fromisoformat(stamp)
        except ValueError:
            continue
        if expected_date and day != expected_date:
            continue
        result.append({**row, 'date': stamp, field: float(value)})
    return result


def compound_change(rows, sessions):
    """Compound provider daily percentage changes; require near-complete windows."""
    ordered = sorted(rows, key=lambda r: r['date'])
    if len({r['date'] for r in ordered}) != len(ordered):
        return None
    values = [r['averageChange'] for r in ordered]
    if len(values) < sessions:
        return None
    selected = values[-sessions:]
    result = math.prod(1 + value / 100 for value in selected) - 1
    return 100 * result if math.isfinite(result) else None


def _close_at_or_before(frame, target):
    eligible = frame.loc[frame.index.date <= target]
    if eligible.empty:
        return None
    value = float(eligible['total_close'].iloc[-1])
    return value if math.isfinite(value) and value > 0 else None


def relative_strength(stock, benchmark, now):
    """20/60-session total return and excess vs SPY, at identical endpoints."""
    today = market_data.last_closed(now)
    common = stock.index.intersection(benchmark.index)
    common = common[common.date <= today]
    if len(common) < 61:
        return None
    s, b = stock.loc[common], benchmark.loc[common]
    result = {}
    for horizon, offset in (('20', 20), ('60', 60)):
        stock_base = float(s['total_close'].iloc[-offset-1])
        bench_base = float(b['total_close'].iloc[-offset-1])
        stock_end = float(s['total_close'].iloc[-1])
        bench_end = float(b['total_close'].iloc[-1])
        if min(stock_base, bench_base, stock_end, bench_end) <= 0:
            return None
        sr = 100 * (stock_end / stock_base - 1)
        br = 100 * (bench_end / bench_base - 1)
        result[horizon] = {'return_pct': sr, 'spy_return_pct': br, 'excess_spy_pp': sr - br}
    return result


def validate_news(rows, now):
    if not isinstance(rows, list):
        raise market_data.ProviderError('Invalid general-news response')
    cutoff = now - timedelta(days=7)
    clean = []
    for row in rows:
        stamp = row.get('publishedDate') or row.get('date')
        title = row.get('title')
        url = row.get('url') or row.get('link')
        if not isinstance(title, str) or not title.strip() or not isinstance(url, str):
            continue
        try:
            published = datetime.fromisoformat(str(stamp).replace('Z', '+00:00'))
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
        if cutoff <= published <= now:
            clean.append({'id': hashlib.sha256((url + published.isoformat()).encode()).hexdigest()[:12],
                          'published_at': published.isoformat(), 'title': title.strip(),
                          'publisher': row.get('publisher') or row.get('site'),
                          'url': url, 'text': str(row.get('text') or row.get('content') or '')[:1200]})
    return clean


def collect(now=None):
    now = now or datetime.now(timezone.utc)
    as_of = market_data.last_closed(now)
    date_text = as_of.isoformat()
    news_rows = market_data.fmp('news/general-latest', page=0, limit=100, allow_empty=True)
    news = validate_news(news_rows, now)
    snapshot = market_data.fmp('industry-performance-snapshot', date=date_text, allow_empty=True)
    daily = _dated_rows(snapshot, 'averageChange', as_of)
    daily = [r for r in daily if r.get('exchange') in {'NYSE', 'NASDAQ', 'AMEX'} and
             isinstance(r.get('industry'), str) and r['industry'] and r['averageChange'] > 0]
    daily.sort(key=lambda r: r['averageChange'], reverse=True)
    daily = list({(r['industry'], r['exchange']): r for r in reversed(daily)}.values())
    daily.sort(key=lambda r: r['averageChange'], reverse=True)
    daily = daily[:MAX_INDUSTRY_HISTORY_CHECKS]
    ranked, failures = [], []
    start = (as_of - timedelta(days=130)).isoformat()
    for daily_row in daily:
        industry, exchange = daily_row['industry'], daily_row['exchange']
        try:
            history = market_data.fmp('historical-industry-performance', industry=industry,
                exchange=exchange, **{'from': start, 'to': date_text}, allow_empty=True)
            rows = _dated_rows(history, 'averageChange')
            if any(r.get('industry') not in (None, industry) or
                   r.get('exchange') not in (None, exchange) for r in rows):
                continue
            change20, change60 = compound_change(rows, 20), compound_change(rows, 60)
            if change20 is None or change60 is None:
                continue
            ranked.append({'industry': industry,
                'sector': daily_row.get('sector'), 'exchange': exchange,
                'daily_change_pct': daily_row['averageChange'],
                'return_20_sessions_pct': change20, 'return_60_sessions_pct': change60,
                'as_of': date_text, 'source': 'FMP historical-industry-performance'})
        except market_data.ProviderError:
            failures.append({'dataset': 'historical_industry_performance', 'industry': industry,
                             'exchange': exchange, 'reason': 'provider_unavailable'})
            continue
    leaders = sorted((r for r in ranked if r['return_20_sessions_pct'] > 0 and
                      r['return_60_sessions_pct'] > 0),
                     key=lambda r: (r['return_60_sessions_pct'], r['return_20_sessions_pct']), reverse=True)[:MAX_INDUSTRIES]
    candidates = []
    if leaders:
        benchmarks = market_data.return_history('SPY', now)
    else:
        benchmarks = None
    for leader in leaders:
        try:
            profiles = market_data.fmp('company-screener', industry=leader['industry'], country='US',
                exchange=leader['exchange'], isEtf=False, isFund=False, isActivelyTrading=True, marketCapMoreThan=MIN_MARKET_CAP,
                limit=100, allow_empty=True)
        except market_data.ProviderError:
            failures.append({'dataset': 'company_screener', 'industry': leader['industry'],
                             'exchange': leader['exchange'], 'reason': 'provider_unavailable'})
            continue
        clean = [r for r in profiles if isinstance(r.get('symbol'), str) and
                 (r.get('country') is None or r.get('country') in
                  ('US', 'USA', 'United States', 'United States of America') or r.get('countryCode') == 'US') and
                 not r.get('isEtf') and not r.get('isFund') and
                 _number(r.get('marketCap')) and r['marketCap'] >= MIN_MARKET_CAP]
        clean.sort(key=lambda r: r['marketCap'], reverse=True)
        for profile in clean[:MAX_COMPANIES_PER_INDUSTRY]:
            symbol = profile['symbol']
            if any(r['symbol'] == symbol for r in candidates):
                continue
            try:
                frame = market_data.return_history(symbol, now)
                strength = relative_strength(frame, benchmarks, now)
                if not strength or any(strength[h]['excess_spy_pp'] <= 0 for h in ('20', '60')):
                    continue
                candidates.append({'symbol': symbol, 'company': profile.get('companyName'),
                    'sector': profile.get('sector') or leader.get('sector'), 'industry': leader['industry'],
                    'exchange': leader['exchange'],
                    'market_cap_usd': profile['marketCap'], 'industry_20_pct': leader['return_20_sessions_pct'],
                    'industry_60_pct': leader['return_60_sessions_pct'], 'relative_strength': strength,
                    'as_of': date_text, 'source': 'FMP screener + total-return history'})
            except market_data.ProviderError:
                failures.append({'dataset': 'total_return_history', 'symbol': symbol,
                                 'reason': 'provider_unavailable'})
                continue
    candidates.sort(key=lambda r: (r['relative_strength']['60']['excess_spy_pp'],
                                   r['relative_strength']['20']['excess_spy_pp']), reverse=True)
    return {'observed_at': now.isoformat(), 'as_of': date_text, 'mode': 'research_only',
        'news': news, 'leading_industries': leaders, 'candidates': candidates,
        'failures': failures,
        'limits': ['Industry performance and share price strength are not direct measures of capital inflows.',
          'News is context for research; this deterministic stage does not infer causality or theme exposure.',
          'Only the three largest screened US companies per leading industry are checked.',
          'Candidates go to a separate research inbox and are not merged into the trading watchlist.']}


def validate_theme_analysis(payload, radar):
    """Keep only model links grounded in supplied, dated article and industry IDs."""
    if not isinstance(payload, dict) or not isinstance(payload.get('themes'), list):
        raise ValueError('Theme analysis schema invalid')
    article_ids = {row['id'] for row in radar.get('news', [])}
    industry_names = {row['industry'] for row in radar.get('leading_industries', [])}
    themes = []
    for row in payload['themes'][:8]:
        if not isinstance(row, dict) or not isinstance(row.get('name'), str):
            continue
        articles = row.get('article_ids'); industries = row.get('industries')
        counter = row.get('counterevidence_article_ids', [])
        stance = row.get('stance')
        if (not isinstance(articles, list) or not isinstance(industries, list) or
            not isinstance(counter, list) or stance not in ('tailwind', 'headwind', 'mixed', 'watch')):
            continue
        cited = sorted({value for value in articles if isinstance(value, str) and value in article_ids})
        mapped = sorted({value for value in industries if isinstance(value, str) and value in industry_names})
        counter_cited = sorted({value for value in counter if isinstance(value, str) and value in article_ids})
        if not cited or not mapped:
            continue
        themes.append({'name': row['name'].strip()[:100], 'stance': stance,
            'article_ids': cited, 'industries': mapped,
            'counterevidence_article_ids': counter_cited})
    return themes


def attach_theme_links(radar, themes):
    by_industry = {}
    for theme in themes:
        for industry in theme['industries']:
            by_industry.setdefault(industry, []).append(theme['name'])
    result = dict(radar)
    result['themes'] = themes
    result['theme_analysis_status'] = 'evidence_linked' if themes else 'no_validated_story_link'
    candidates, unlinked = [], []
    for row in radar.get('candidates', []):
        links = by_industry.get(row['industry'], [])
        enriched = {**row, 'theme_links': links}
        (candidates if links else unlinked).append(enriched)
    result['candidates'] = candidates
    result['price_leaders_without_news_link'] = unlinked
    return result


def merge_snapshot(result, previous=None):
    """Append/replace one dated snapshot without erasing older candidate evidence."""
    previous = previous if isinstance(previous, dict) else {}
    prior_latest = previous.get('latest') if isinstance(previous.get('latest'), dict) else {}
    prior_symbols = {row.get('symbol') for row in prior_latest.get('candidates', [])
                     if isinstance(row, dict)}
    snapshot = dict(result)
    for row in snapshot.get('candidates', []):
        row['pool_status'] = 'continued' if row.get('symbol') in prior_symbols else 'new'
    current_symbols = {row.get('symbol') for row in snapshot.get('candidates', [])}
    snapshot['no_longer_confirmed'] = sorted(s for s in prior_symbols - current_symbols if s)
    observations = OrderedDict()
    for item in previous.get('observations', []):
        if isinstance(item, dict) and item.get('as_of'):
            observations[item['as_of']] = item
    observations[snapshot['as_of']] = snapshot
    return {'schema_version': 1, 'updated_at': snapshot['observed_at'],
            'latest': snapshot, 'observations': list(observations.values())}
