"""Research-only, cross-sector theme and relative-strength candidate radar."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import math
from collections import OrderedDict

import market_data
import theme_macro_context
import article_reader
import pandas as pd

MIN_MARKET_CAP = 200_000_000
MAX_INDUSTRIES = 5
MAX_COMPANIES_PER_INDUSTRY = 3
MAX_INDUSTRY_HISTORY_CHECKS = 20
POSITIVE_INDUSTRY_SAMPLE = 12
NEGATIVE_INDUSTRY_SAMPLE = 8
MAX_BREADTH_THEMES = 10
MAX_HOLDINGS_PER_THEME = 10
MIN_BREADTH_COVERAGE = 0.7
THEME_PROXIES = (
    ('Bitcoin', 'IBIT'), ('Semiconductors', 'SMH'), ('Genomics', 'ARKG'),
    ('Quantum computing', 'QTUM'), ('Biotechnology', 'XBI'),
    ('Healthcare', 'XLV'), ('Airlines', 'JETS'), ('China internet', 'KWEB'),
    ('Artificial intelligence', 'AIQ'), ('Medical devices', 'IHI'),
    ('Homebuilders', 'XHB'), ('Bitcoin miners', 'WGMI'), ('Robotics', 'BOTZ'),
    ('Industrials', 'XLI'), ('Software', 'IGV'), ('Retail', 'XRT'),
    ('Social media', 'SOCL'), ('Cybersecurity', 'CIBR'), ('Energy', 'XLE'),
    ('Uranium', 'URA'), ('Data centers', 'SRVR'),
    ('Electric grid', 'GRID'), ('Cloud computing', 'SKYY'),
    ('Aerospace and defense', 'ITA'),
)


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


def rank_industry_momentum(rows, spy_returns=None):
    """Rank sampled FMP industries by 5/21-session return without blending horizons."""
    spy_returns = spy_returns or {}
    rankings = {}
    for horizon, field in (('5_sessions', 'return_5_sessions_pct'),
                           ('21_sessions', 'return_21_sessions_pct')):
        ordered = sorted((row for row in rows if _number(row.get(field))),
                         key=lambda row: row[field], reverse=True)
        rankings[horizon] = []
        for rank, row in enumerate(ordered, 1):
            spy = spy_returns.get(horizon)
            rankings[horizon].append({**row, 'rank': rank,
                'spy_return_pct': spy,
                'excess_spy_pp': row[field] - spy if _number(spy) else None})
    return rankings


def _rank_theme_proxies(rows, spy_returns=None):
    spy_returns = spy_returns or {}
    rankings = {}
    for horizon, field in (('5_sessions', 'return_5_sessions_pct'),
                           ('21_sessions', 'return_21_sessions_pct')):
        ordered = sorted((row for row in rows if _number(row.get(field))),
                         key=lambda row: row[field], reverse=True)
        rankings[horizon] = []
        for rank, row in enumerate(ordered, 1):
            spy = spy_returns.get(horizon)
            rankings[horizon].append({**row, 'rank': rank,
                'spy_return_pct': spy,
                'excess_spy_pp': row[field] - spy if _number(spy) else None})
    return rankings


def _history_return(frame, sessions, now):
    today = market_data.last_closed(now)
    history = frame.loc[frame.index.date <= today]
    if len(history) < sessions + 1:
        return None
    base, latest = float(history['total_close'].iloc[-sessions-1]), float(history['total_close'].iloc[-1])
    if min(base, latest) <= 0:
        return None
    return 100 * (latest / base - 1)


def _theme_proxy_history(symbol, now):
    start = (now.date() - timedelta(days=75)).isoformat()
    end = market_data.last_closed(now).isoformat()

    def primary():
        rows = market_data.fmp('historical-price-eod/dividend-adjusted', symbol=symbol,
                               **{'from': start, 'to': end})
        if any(row.get('symbol', symbol) != symbol for row in rows):
            raise market_data.ProviderError('Theme proxy symbol mismatch')
        records = []
        for row in rows:
            close = row.get('adjClose', row.get('close'))
            if not row.get('date') or not _number(close):
                continue
            records.append({'Date': row['date'], 'Close': float(close),
                            'Volume': row.get('volume', 0) or 0})
        if not records:
            raise market_data.ProviderError('Theme proxy history unavailable')
        frame = pd.DataFrame(records).set_index('Date')
        frame.index = pd.to_datetime(frame.index)
        return frame

    def backup():
        import yfinance
        return yfinance.Ticker(symbol).history(period='3mo', interval='1d',
                                                auto_adjust=True, actions=False)

    frame, provider = market_data.select(symbol, 'theme_proxy_history', primary, backup,
                                         lambda value: market_data.validate_history(value, '1d', now))
    frame = frame.rename(columns={'Close': 'total_close'})[['total_close']]
    frame.attrs['provider'] = provider
    return frame


def theme_proxy_momentum(now, spy_returns=None):
    rows, failures = [], []
    for theme, symbol in THEME_PROXIES:
        try:
            frame = _theme_proxy_history(symbol, now)
            ret5, ret21 = _history_return(frame, 5, now), _history_return(frame, 21, now)
            if ret5 is None or ret21 is None:
                raise market_data.ProviderError('Theme proxy history too short')
            expected_week = ((1 + ret21 / 100) ** (5 / 21) - 1) * 100
            rows.append({'theme': theme, 'proxy_symbol': symbol,
                'return_5_sessions_pct': ret5, 'return_21_sessions_pct': ret21,
                'weekly_vs_monthly_pace_pp': ret5 - expected_week,
                'as_of': market_data.last_closed(now).isoformat(),
                'source': ('FMP dividend-adjusted EOD price' if frame.attrs.get('provider') == 'FMP'
                           else 'yfinance auto-adjusted EOD price'),
                'provider': frame.attrs.get('provider', 'unknown')})
        except market_data.ProviderError:
            failures.append({'dataset': 'theme_proxy_history', 'symbol': symbol,
                             'reason': 'provider_unavailable'})
    rankings = _rank_theme_proxies(rows, spy_returns)
    breadth = _theme_constituent_breadth(rankings, now)
    return {'as_of': market_data.last_closed(now).isoformat(),
        'sampled_theme_count': len(rows),
        'rankings': rankings, 'constituent_breadth': breadth['rows'],
        'failures': failures + breadth['failures'],
        'limits': ['ETF proxy returns measure market prices, not net fund flows.',
                   'Theme definitions are represented by one ETF proxy each and can be imperfect.',
                   'Breadth covers up to the 10 highest-weight disclosed holdings of the leading ETFs, not every constituent.',
                   'Daily breadth is the share of covered holdings with a positive daily change; it is not a multi-day breadth measure.']}


def _theme_constituent_breadth(rankings, now):
    """Daily breadth of disclosed top holdings for the union of short and medium-term leaders."""
    chosen = {}
    for horizon in ('5_sessions', '21_sessions'):
        for row in rankings.get(horizon, [])[:5]:
            chosen[row['proxy_symbol']] = row
    chosen = dict(list(chosen.items())[:MAX_BREADTH_THEMES])
    if not chosen:
        return {'rows': [], 'failures': []}
    holdings_by_etf, symbols, failures = {}, set(), []
    for etf, theme_row in chosen.items():
        try:
            items = market_data.fmp('etf/holdings', symbol=etf, allow_empty=True)
            selected = []
            for item in items:
                ticker = item.get('asset') or item.get('symbol')
                weight = item.get('weightPercentage')
                updated = item.get('updatedAt') or item.get('date')
                if (not isinstance(ticker, str) or not ticker.strip() or ticker == etf or
                    not _number(weight) or float(weight) <= 0):
                    continue
                selected.append({'symbol': ticker.strip(), 'weight_pct': float(weight),
                                 'updated_at': str(updated or '')[:10] or None})
            selected.sort(key=lambda x: x['weight_pct'], reverse=True)
            selected = selected[:MAX_HOLDINGS_PER_THEME]
            if not selected:
                raise market_data.ProviderError('No valid disclosed holdings')
            dates = [x['updated_at'] for x in selected if x['updated_at']]
            if len(dates) != len(selected):
                raise market_data.ProviderError('Holdings disclosure date unavailable')
            latest = max(dates)
            try:
                if (market_data.last_closed(now) - date.fromisoformat(latest)).days > 35:
                    raise market_data.ProviderError('Holdings disclosure is stale')
            except ValueError:
                raise market_data.ProviderError('Invalid holdings disclosure date') from None
            holdings_by_etf[etf] = {'theme': theme_row['theme'], 'holdings': selected,
                                    'holdings_as_of': latest}
            symbols.update(item['symbol'] for item in selected)
        except market_data.ProviderError:
            failures.append({'dataset': 'theme_etf_holdings', 'symbol': etf,
                             'reason': 'provider_unavailable'})
    changes = {}
    if symbols:
        try:
            quotes = market_data.fmp('batch-quote', symbols=','.join(sorted(symbols)), allow_empty=True)
            for quote in quotes:
                ticker = quote.get('symbol')
                value = quote.get('changePercentage')
                if ticker in symbols and _number(value):
                    changes[ticker] = float(value)
        except market_data.ProviderError:
            failures.append({'dataset': 'theme_constituent_quotes', 'reason': 'provider_unavailable'})
    output = []
    for etf, data in holdings_by_etf.items():
        holdings = data['holdings']
        observed = [item for item in holdings if item['symbol'] in changes]
        advances = sum(changes[item['symbol']] > 0 for item in observed)
        declines = sum(changes[item['symbol']] < 0 for item in observed)
        coverage = len(observed) / len(holdings)
        valid = coverage >= MIN_BREADTH_COVERAGE
        output.append({'theme': data['theme'], 'proxy_symbol': etf,
            'holdings_count': len(holdings), 'quoted_count': len(observed),
            'advancing_count': advances, 'declining_count': declines,
            'unchanged_count': len(observed) - advances - declines,
            'advancing_pct': 100 * advances / len(observed) if valid and observed else None,
            'net_advancing_pct': 100 * (advances - declines) / len(observed) if valid and observed else None,
            'coverage_pct': 100 * coverage, 'holdings_as_of': data['holdings_as_of'],
            'as_of': market_data.last_closed(now).isoformat(),
            'status': 'available' if valid else 'insufficient_quote_coverage',
            'scope': 'top_weighted_disclosed_holdings'})
    return {'rows': output, 'failures': failures}


def _industry_sample(rows):
    """Use a bounded positive/negative daily-mover sample; never imply full coverage."""
    unique = {}
    for row in rows:
        current = unique.get(row['industry'])
        if current is None or abs(row['averageChange']) > abs(current['averageChange']):
            unique[row['industry']] = row
    values = list(unique.values())
    positive = sorted((row for row in values if row['averageChange'] > 0),
                      key=lambda row: row['averageChange'], reverse=True)[:POSITIVE_INDUSTRY_SAMPLE]
    negative = sorted((row for row in values if row['averageChange'] < 0),
                      key=lambda row: row['averageChange'])[:NEGATIVE_INDUSTRY_SAMPLE]
    selected = positive + negative
    selected.sort(key=lambda row: row['averageChange'], reverse=True)
    return selected[:MAX_INDUSTRY_HISTORY_CHECKS]


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
    news = article_reader.enrich_news(validate_news(news_rows, now))
    snapshot = market_data.fmp('industry-performance-snapshot', date=date_text, allow_empty=True)
    daily = _dated_rows(snapshot, 'averageChange', as_of)
    daily = [r for r in daily if r.get('exchange') in {'NYSE', 'NASDAQ', 'AMEX'} and
             isinstance(r.get('industry'), str) and r['industry']]
    daily = _industry_sample(daily)
    ranked, failures = [], []
    momentum_rows = []
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
            if not rows or max(row['date'] for row in rows) != date_text:
                continue
            change5, change21 = compound_change(rows, 5), compound_change(rows, 21)
            change20, change60 = compound_change(rows, 20), compound_change(rows, 60)
            if change5 is None or change21 is None:
                continue
            momentum = {'industry': industry,
                'sector': daily_row.get('sector'), 'exchange': exchange,
                'daily_change_pct': daily_row['averageChange'],
                'return_5_sessions_pct': change5, 'return_21_sessions_pct': change21,
                'weekly_vs_monthly_pace_pp': change5 - ((1 + change21 / 100) ** (5 / 21) - 1) * 100,
                'return_20_sessions_pct': change20, 'return_60_sessions_pct': change60,
                'as_of': date_text, 'source': 'FMP historical-industry-performance'}
            momentum_rows.append(momentum)
            if change20 is None or change60 is None:
                continue
            ranked.append(momentum)
        except market_data.ProviderError:
            failures.append({'dataset': 'historical_industry_performance', 'industry': industry,
                             'exchange': exchange, 'reason': 'provider_unavailable'})
            continue
    leaders = sorted((r for r in ranked if r['return_20_sessions_pct'] > 0 and
                      r['return_60_sessions_pct'] > 0),
                     key=lambda r: (r['return_60_sessions_pct'], r['return_20_sessions_pct']), reverse=True)[:MAX_INDUSTRIES]
    candidates = []
    benchmarks = None
    spy_returns = {}
    if momentum_rows:
        try:
            benchmarks = market_data.return_history('SPY', now)
            for horizon, sessions in (('5_sessions', 5), ('21_sessions', 21)):
                spy_returns[horizon] = _history_return(benchmarks, sessions, now)
        except market_data.ProviderError:
            failures.append({'dataset': 'theme_momentum_benchmark', 'symbol': 'SPY',
                             'reason': 'provider_unavailable'})
    theme_momentum = {'as_of': date_text, 'sampled_industry_count': len(momentum_rows),
        'sample_method': f'top {POSITIVE_INDUSTRY_SAMPLE} positive and bottom {NEGATIVE_INDUSTRY_SAMPLE} negative daily industry movers, capped at {MAX_INDUSTRY_HISTORY_CHECKS}',
        'source': 'FMP industry-performance-snapshot + historical-industry-performance',
        'rankings': rank_industry_momentum(momentum_rows, spy_returns),
        'limits': ['Ranks cover the bounded daily-mover sample, not every industry.',
                   'Returns are price-performance signals, not observed fund or capital flows.']}
    theme_proxies = theme_proxy_momentum(now, spy_returns)
    failures.extend(theme_proxies.pop('failures'))
    macro_context = theme_macro_context.collect()
    for leader in leaders:
        if benchmarks is None:
            break
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
        'news': news, 'theme_momentum': theme_momentum,
        'theme_proxy_momentum': theme_proxies, 'macro_context': macro_context,
        'leading_industries': leaders, 'candidates': candidates,
        'failures': failures,
        'limits': ['Industry performance and share price strength are not direct measures of capital inflows.',
          'News is context for research; this deterministic stage does not infer causality or theme exposure.',
          'Only the three largest screened US companies per leading industry are checked.',
          'Candidates go to a separate research inbox and are not merged into the trading watchlist.']}


def validate_theme_analysis(payload, radar):
    """Ground theme and company claims in the exact dated articles supplied."""
    if not isinstance(payload, dict) or not isinstance(payload.get('themes'), list):
        raise ValueError('Theme analysis schema invalid')
    article_map = {row['id']: row for row in radar.get('news', [])}
    article_ids = set(article_map)
    industry_names = {row['industry'] for row in radar.get('leading_industries', [])}
    themes = []
    for row in payload['themes'][:8]:
        if not isinstance(row, dict) or not isinstance(row.get('name'), str):
            continue
        theme_article_ids = row.get('article_ids'); industries = row.get('industries')
        counter = row.get('counterevidence_article_ids', [])
        stance = row.get('stance')
        if (not isinstance(theme_article_ids, list) or not isinstance(industries, list) or
            not isinstance(counter, list) or stance not in ('tailwind', 'headwind', 'mixed', 'watch')):
            continue
        cited = sorted({value for value in theme_article_ids if isinstance(value, str) and value in article_ids})
        mapped = sorted({value for value in industries if isinstance(value, str) and value in industry_names})
        counter_cited = sorted({value for value in counter if isinstance(value, str) and value in article_ids})
        if not cited or not mapped:
            continue
        themes.append({'name': row['name'].strip()[:100], 'stance': stance,
            'article_ids': cited, 'industries': mapped,
            'counterevidence_article_ids': counter_cited})
    exposures = []
    for row in payload.get('company_exposures', [])[:8]:
        if not isinstance(row, dict):
            continue
        company = row.get('company_name'); symbol = row.get('symbol')
        article_ids_for_row = row.get('article_ids'); quote = row.get('article_evidence_quote')
        if (not isinstance(company, str) or not company.strip() or
            not isinstance(symbol, str) or
            not isinstance(article_ids_for_row, list) or not isinstance(quote, str)):
            continue
        cited = sorted({value for value in article_ids_for_row
                        if isinstance(value, str) and value in article_ids and
                        article_map[value].get('content_read_status') == 'article_body_extracted'})
        normalized_quote = ' '.join(quote.split())
        supported = any(normalized_quote and normalized_quote in
                        ' '.join(str(article_map[ident].get('article_body_text', '')).split())
                        for ident in cited)
        if not cited or not supported or len(normalized_quote) < 35:
            continue
        exposures.append({'theme': str(row.get('theme') or '')[:100],
            'company_name': company.strip()[:160], 'symbol': symbol.strip().upper()[:12],
            'product': str(row.get('product') or '')[:160],
            'component': str(row.get('component') or '')[:160],
            'role': str(row.get('role') or '')[:180],
            'article_ids': cited, 'article_evidence_quote': normalized_quote[:500]})
    return {'themes': themes, 'company_exposures': exposures}


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


def attach_company_exposures(radar, exposures):
    """Add only filing-supported exposure candidates to the separate research inbox."""
    result = dict(radar)
    candidates = list(result.get('candidates', []))
    known = {row.get('symbol') for row in candidates}
    verified = []
    for row in exposures:
        if row.get('verification_status') != 'verified':
            continue
        candidate = {'symbol': row['symbol'], 'company': row.get('company_name'),
            'industry': 'Supply-chain exposure', 'theme_links': [row['theme']] if row.get('theme') else [],
            'candidate_type': 'verified_company_product_exposure',
            'product': row.get('product'), 'component': row.get('component'),
            'exposure_role': row.get('role'), 'article_ids': row.get('article_ids', []),
            'article_evidence_quote': row.get('article_evidence_quote'),
            'filing_form': row.get('filing_form'), 'filing_date': row.get('filing_date'),
            'filing_url': row.get('filing_url'),
            'filing_evidence_quote': row.get('filing_evidence_quote'),
            'source': 'Dated article + SEC issuer filing'}
        verified.append(candidate)
        if candidate['symbol'] in known:
            candidates = [({**item, **{key: value for key, value in candidate.items()
                           if key not in {'symbol', 'industry'}}}
                           if item.get('symbol') == candidate['symbol'] else item) for item in candidates]
        else:
            candidates.append(candidate)
            known.add(candidate['symbol'])
    result['candidates'] = candidates
    result['verified_company_exposures'] = verified
    result['unverified_company_exposure_leads'] = [row for row in exposures
        if row.get('verification_status') != 'verified']
    return result


def merge_snapshot(result, previous=None):
    """Append/replace one dated snapshot without erasing older candidate evidence."""
    previous = previous if isinstance(previous, dict) else {}
    prior_latest = previous.get('latest') if isinstance(previous.get('latest'), dict) else {}
    prior_symbols = {row.get('symbol') for row in prior_latest.get('candidates', [])
                     if isinstance(row, dict)}
    snapshot = dict(result)
    if snapshot.get('theme_analysis_status') == 'unavailable':
        # A failed analysis cannot confirm disappearance from the pool.
        snapshot['no_longer_confirmed'] = []
        snapshot['pool_comparison_status'] = 'unknown_analysis_unavailable'
    else:
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
