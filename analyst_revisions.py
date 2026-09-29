"""Observed analyst revisions: research triggers, never orders or return forecasts."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from functools import lru_cache
from statistics import median, pstdev
import copy
import hashlib
import json
import math
import re

import market_data

BASE = Path(__file__).resolve().parent
WINDOWS = (7, 30, 90)
INTEGRITY_VERSION = 2
LIMITS = ('Provider observations, not verified analyst reports. Targets are forecasts; '
          'revision reasons and forecast horizon are unknown unless separately sourced. '
          'Two independent firms is a research routing heuristic, not a fitted investment rule. '
          'Historical targets may be provider-restated. No automatic BUY/SELL or execution-lock bypass.')
ALIASES = {'jpmorgan': 'jpmorgan', 'jpmorganchase': 'jpmorgan',
           'jp morgan': 'jpmorgan', 'jp morgan chase': 'jpmorgan',
           'bofa securities': 'bank of america', 'bofa': 'bank of america',
           'bank of america securities': 'bank of america',
           'baird': 'robert w baird', 'rbc capital markets': 'rbc capital',
           'keybanc capital markets': 'keybanc', 'stifel': 'stifel nicolaus',
           'truist securities': 'truist financial', 'wells fargo securities': 'wells fargo',
           'citi': 'citigroup'}


REVIEW_INSTRUCTION = '''When analyst_revisions is supplied, include analyst_review with exactly
these four keys: earnings, company_news, sector_theme, valuation.
Each value has exactly {assessment, evidence_status, source_ids}. assessment is nonempty
qualitative prose (use SOURCE_LEDGER placeholders for numbers). evidence_status is one of
reported_reason, context_only, unknown; source_ids is a list of supplied fact/document IDs.
Earnings: compare same-period EPS/revenue forecasts, but improving earnings are NOT required
for a valid positive revision. Company_news: examine contracts, products, regulation,
partnerships and other issuer events. Sector_theme: examine industry demand, sector rotation,
theme/narrative attention and related news. Valuation: consider repricing of the growth story,
multiples, discount rates, positioning and any changed forecast horizon.
reported_reason requires an article explicitly attributing that reason to the analyst;
cite its news source ID. context_only requires evidence IDs and must label the connection
as a hypothesis, not the analyst's stated reason. unknown requires empty source_ids and an
explicit gap. Price/volume changes alone do not prove fund flows, investor attention or
causation. Missing EPS history must not veto news, sector or narrative evidence.
Weigh counterevidence and alternative explanations. A strong theme can coexist with weak
earnings, stretched valuation or crowded positioning. Never infer that a target revision
prescribes a trade or proves future returns. Keep this review separate from the action.'''


def validate_review(review, symbol, data, facts):
    if not isinstance(review, dict) or set(review) != {'earnings', 'company_news', 'sector_theme', 'valuation'}:
        raise ValueError('Analyst review must cover earnings, company news, sector/theme and valuation')
    sources = {k for k, v in facts.items() if v['symbol'] in {symbol, 'SPY', 'SMH'}}
    documents = data.get(symbol, {}).get('source_documents', {})
    sources.update(k for k, v in documents.items() if v.get('symbol') == symbol)
    for axis in review.values():
        if not isinstance(axis, dict) or set(axis) != {'assessment', 'evidence_status', 'source_ids'}:
            raise ValueError('Invalid analyst driver schema')
        if not isinstance(axis['assessment'], str) or not axis['assessment'].strip():
            raise ValueError('Explain each analyst driver or its evidence gap')
        status, ids = axis['evidence_status'], axis['source_ids']
        if status not in {'reported_reason', 'context_only', 'unknown'} or not isinstance(ids, list) or any(not isinstance(k, str) or k not in sources for k in ids):
            raise ValueError('Unknown driver status or source identity')
        if (status == 'unknown' and ids) or (status != 'unknown' and not ids):
            raise ValueError('Driver status must reflect evidence availability')
        if status == 'reported_reason' and not any(k.startswith('news:') and k in documents for k in ids):
            raise ValueError('A reported analyst reason requires an attributed news article; price or forecasts alone are context')
    return copy.deepcopy(review)


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:24]


def number(value):
    if isinstance(value, bool): return None
    try: result = float(value)
    except (ValueError, TypeError): return None
    return result if math.isfinite(result) else None


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None: raise ValueError('Timestamp timezone missing')
    return result.astimezone(timezone.utc)


def firm_name(value):
    name = re.sub(r'[^a-z0-9 ]', '', str(value or '').casefold())
    name = ' '.join(name.split())
    return ALIASES.get(name, name)


def analyze(symbol, rows, moment, complete):
    groups, rejected, conflicts, attribution_conflicts, quarantined = {}, 0, [], [], []
    known_firms = {firm_name(r.get('analystCompany')) for r in rows if isinstance(r, dict)} | set(ALIASES.values())
    for row in rows:
        try:
            when = stamp(row['publishedDate'])
            firm = firm_name(row.get('analystCompany'))
            target = number(row.get('adjPriceTarget'))
            # Never mix raw targets across a split or infer an adjustment ourselves.
            raw, price = number(row.get('priceTarget')), number(row.get('priceWhenPosted'))
            if row.get('symbol') != symbol or not firm or when > moment or target is None or target <= 0 or raw is None or raw <= 0:
                raise ValueError('Invalid target observation')
            title = str(row.get('newsTitle') or '')
            named = re.search(r'\b(?:at|by)\s+([A-Za-z .&-]+)$', title)
            reasons = []
            if named and firm_name(named[1]) in known_firms and firm_name(named[1]) != firm:
                attribution_conflicts.append({'firm': firm, 'title_firm': firm_name(named[1]), 'at': when.isoformat(), 'title': title})
                reasons.append('headline_firm_differs_from_provider_firm')
            headline_target = re.search(r'\b(?:price target|PT)\b.*?\bto\s+\$([\d,]+(?:\.\d+)?)', title, re.I)
            if headline_target and not math.isclose(float(headline_target[1].replace(',', '')), raw, abs_tol=0.01, rel_tol=0):
                reasons.append('headline_target_differs_from_raw_provider_target')
            if reasons:
                quarantined.append({'id': identity([symbol,row]), 'symbol': symbol, 'firm': firm,
                    'at': when.isoformat(), 'title': title, 'url': row.get('newsURL'), 'raw_record': copy.deepcopy(row),
                    'reasons': reasons, 'resolution': 'Awaiting a consistent provider record or independently verified source; no inferred repair'})
                continue
            initiation = bool(re.search(r'\b(?:re[- ]?)?initiat\w*\b.{0,70}\b(?:coverage|overweight|underweight|outperform|underperform|neutral|buy|hold|sell)\b|\b(?:starts?|resumes?|assumes?)\b.{0,100}\b(?:coverage|with an? (?:overweight|underweight|outperform|underperform|neutral|buy|hold|sell))\b', title, re.I))
            item = {'firm': firm, 'analyst': row.get('analystName'), 'at': when.isoformat(),
                    'target_adjusted': target, 'target_raw': raw, 'price_when_posted': price,
                    'url': row.get('newsURL'), 'title': row.get('newsTitle'),
                    'coverage_action': 'initiation_or_resumption' if initiation else 'update_or_unknown',
                    'reason': 'unknown', 'forecast_horizon': 'unknown'}
            groups.setdefault(firm, {}).setdefault(when.date().isoformat(), []).append(item)
        except (ValueError, TypeError, KeyError, AttributeError): rejected += 1
    revisions, latest, segment_counts = [], [], {}
    unpaired = 0
    for firm, days in sorted(groups.items()):
        observations = []
        for day, entries in sorted(days.items()):
            if len({r['target_adjusted'] for r in entries}) != 1:
                conflicts.append(firm + ':' + day)
                # Do not bridge an ambiguous observation to invent a revision.
                observations.append(None)
            else:
                observations.append(sorted(entries, key=lambda r: (r['at'], str(r['url'])))[-1])
        previous = None
        segment_count = 0
        for current in observations:
            if current is None:
                previous = None
                segment_count = 0
                continue
            if current['coverage_action'] == 'initiation_or_resumption':
                previous = None
                segment_count = 0
            segment_count += 1
            if previous and current['target_adjusted'] != previous['target_adjusted']:
                delta = 100 * (current['target_adjusted'] / previous['target_adjusted'] - 1)
                # Dates and targets define the event, not URL/publisher/collection time.
                event = identity([symbol, firm, previous['at'][:10], previous['target_raw'], current['at'][:10], current['target_raw']])
                raw_old, raw_new = previous['target_raw'], current['target_raw']
                p_old, p_new = previous['price_when_posted'], current['price_when_posted']
                same_basis = (raw_old and raw_new and raw_old > 0 and raw_new > 0 and
                              math.isclose(previous['target_adjusted']/raw_old, current['target_adjusted']/raw_new, rel_tol=1e-4))
                revisions.append({'id': event, 'firm': firm, 'at': current['at'],
                                  'previous': previous, 'current': current, 'revision_pct': round(delta, 4),
                                  'baseline_age_days': (stamp(current['at'])-stamp(previous['at'])).days,
                                  'comparison_scope': 'Last observed same-firm target; missing intermediate provider coverage cannot be ruled out.',
                                  'price_move_between_reports_pct': round(100*(p_new/p_old-1), 4) if same_basis and p_old and p_new and p_old > 0 and p_new > 0 else None,
                                  'gap_when_posted_pct': round(100*(raw_new/p_new-1), 4) if raw_new and p_new and raw_new > 0 and p_new > 0 else None})
            elif previous is None:
                unpaired += 1
            previous = current
        if previous:
            latest.append(previous)
            segment_counts[firm] = segment_count
    windows = {}
    for days in WINDOWS:
        cutoff = moment - timedelta(days=days)
        paired = {}
        for revision in sorted(revisions, key=lambda r: r['at']):
            if stamp(revision['at']) >= cutoff: paired[revision['firm']] = revision
        values = list(paired.values())
        up = sum(r['revision_pct'] > 0 for r in values)
        down = sum(r['revision_pct'] < 0 for r in values)
        current_targets = [r['target_adjusted'] for r in latest if stamp(r['at']) >= cutoff]
        recent = [r for r in latest if stamp(r['at']) >= cutoff]
        windows[str(days)] = {'up_firms': up, 'down_firms': down, 'matched_firms': len(values),
                             'unchanged_firms': sum(r['firm'] not in paired and segment_counts[r['firm']] > 1 for r in recent),
                             'unpaired_firms': sum(segment_counts[r['firm']] == 1 for r in recent),
                             'initiated_or_resumed_firms': sum(r['coverage_action'] == 'initiation_or_resumption' for r in recent),
                             'breadth': (up-down)/len(values) if values else None,
                             'median_revision_pct': round(median([r['revision_pct'] for r in values]), 4) if values else None,
                             'target_dispersion_pct': 100*pstdev(current_targets)/median(current_targets) if len(current_targets) > 1 else None,
                             'revisions': values}
    eligible = windows['30']
    recent_conflicts = [c for c in conflicts if c.rsplit(':', 1)[-1] >= (moment-timedelta(days=90)).date().isoformat()]
    recent_quarantine = [c for c in quarantined if stamp(c['at']) >= moment-timedelta(days=90)]
    direction = ('up' if eligible['up_firms'] >= 2 and eligible['up_firms'] > eligible['down_firms'] else
                 'down' if eligible['down_firms'] >= 2 and eligible['down_firms'] > eligible['up_firms'] else 'mixed_or_insufficient')
    return {'symbol': symbol, 'observed_at': moment.isoformat(), 'windows': windows, 'integrity_version': INTEGRITY_VERSION,
            'direction': direction, 'status': ('no_records' if not rows and complete else
                'ok' if complete and not rejected and not recent_conflicts and not recent_quarantine else 'incomplete'),
            'coverage': {'pagination_complete': complete, 'received_rows': len(rows), 'rejected_rows': rejected,
                         'conflicts': conflicts, 'recent_conflicts': recent_conflicts, 'unpaired_segments': unpaired, 'firms': len(groups)},
            'attribution_conflicts': attribution_conflicts,
            'quarantined_records': quarantined,
            'limits': LIMITS}


def estimates(rows, symbol):
    result = {}
    for row in rows:
        if row.get('symbol') != symbol: continue
        try: period = datetime.fromisoformat(row['date']).date().isoformat()
        except (ValueError, KeyError, TypeError): continue
        result[period] = {key: number(row.get(key)) for key in ('epsAvg', 'revenueAvg')}
    return result


def collect(symbol, moment, previous=None, fetch=None):
    fetch = fetch or market_data.fmp
    rows, complete, pages = [], False, set()
    try:
        for page in range(10):
            batch = fetch('price-target-news', symbol=symbol, page=page, limit=100, allow_empty=True)
            if not isinstance(batch, list): raise ValueError('Invalid target payload')
            fingerprint = identity(batch)
            if fingerprint in pages: break
            pages.add(fingerprint)
            rows.extend(batch)
            if len(batch) < 100:
                complete = True
                break
        result = analyze(symbol, rows, moment, complete)
    except (market_data.ProviderError, ValueError, TypeError):
        result = analyze(symbol, rows, moment, False)
        result['status'] = 'unavailable'
    try:
        result['estimates'] = estimates(fetch('analyst-estimates', symbol=symbol, period='annual', limit=10, allow_empty=True), symbol)
        result['estimates_status'] = 'ok' if result['estimates'] else 'unavailable'
    except (market_data.ProviderError, ValueError, TypeError, AttributeError):
        result.update(estimates={}, estimates_status='unavailable')
    changes = {}
    for period, current in result['estimates'].items():
        old = (previous or {}).get('estimates', {}).get(period, {})
        changes[period] = {key: {'previous': old.get(key), 'current': value,
                                 'change_pct': 100*(value-old[key])/abs(old[key]) if value is not None and old.get(key) not in (None, 0) else None}
                           for key, value in current.items()}
    result['estimate_changes'] = {'previous_observed_at': (previous or {}).get('observed_at'),
                                  'periods': changes, 'limits': 'Same fiscal period across observed snapshots; consensus co-movement is not a cause of any individual target change.'}
    return result


def refresh(symbol, moment, state, fetch=None):
    """One observation per UTC date; no historical backfilling into observation time."""
    key = moment.date().isoformat() + ':' + symbol + ':v' + str(INTEGRITY_VERSION)
    if key in state: return copy.deepcopy(state[key]), False
    previous = [v for v in state.values() if v.get('symbol') == symbol and stamp(v['observed_at']) < moment]
    prior = max(previous, key=lambda r: r['observed_at']) if previous else None
    result = collect(symbol, moment, prior, fetch)
    state[key] = copy.deepcopy(result)
    return result, True


def attach(row, report):
    row['analyst_revisions'] = report
    documents = row.setdefault('source_documents', {})
    for window in report['windows'].values():
        for revision in window['revisions']:
            documents['analyst:'+revision['id']] = {'symbol': report['symbol'], 'published_at': revision['at'],
                'url': revision['current']['url'], 'text': json.dumps(revision, sort_keys=True),
                'scope': 'FMP target observations and arithmetic; reasons and analyst horizon unknown'}


def review_trigger(symbol, report, cooldown, moment):
    if report.get('status') != 'ok' or report.get('direction') not in ('up', 'down'): return None
    if stamp(report['observed_at']).date() != moment.date(): return None
    positive = report['direction'] == 'up'
    relevant = [r for r in report['windows']['30']['revisions'] if (r['revision_pct'] > 0) == positive]
    unseen = [r for r in relevant if 'analyst:'+symbol+':'+r['id'] not in cooldown]
    if not unseen: return None
    return {'symbol': symbol, 'claim_id': 'analyst_revision_review', 'severity': 'thesis',
            'condition_type': 'analyst_revision', 'measured': len(relevant), 'threshold': 1,
            'trigger': 'Independent analyst targets revised '+report['direction']+'; reassess supporting and opposing evidence. No automatic trade.',
            'analyst_event_keys': ['analyst:'+symbol+':'+r['id'] for r in relevant],
            'cooldown_key': 'analyst:'+symbol+':'+identity(sorted(r['id'] for r in relevant))}


@lru_cache(maxsize=512)
def forward_days(observed):
    calendar = market_data.calendars.get_calendar('NYSE')
    schedule = calendar.schedule(start_date=observed+timedelta(days=1), end_date=observed+timedelta(days=130))
    return tuple(schedule.index.date[:61])


def forward_score(report, histories):
    """Observed cohorts; next-session close to 20/60-session total-return endpoints."""
    days = forward_days(stamp(report['observed_at']).date())
    result = []
    for horizon in (20, 60):
        values = {}
        for symbol in (report['symbol'], 'SPY'):
            frame = histories.get(symbol)
            if frame is None or 'total_close' not in frame: continue
            start = frame.loc[frame.index.date == days[0], 'total_close']
            end = frame.loc[frame.index.date == days[horizon], 'total_close']
            if len(start) == len(end) == 1 and number(start.iloc[0]) and start.iloc[0] > 0 and number(end.iloc[0]) and end.iloc[0] > 0:
                values[symbol] = 100*(float(end.iloc[0])/float(start.iloc[0])-1)
        result.append({'horizon_sessions': horizon, 'baseline_date': days[0].isoformat(),
                       'end_date': days[horizon].isoformat(), 'status': 'measured' if len(values) == 2 else 'pending',
                       'return_pct': values.get(report['symbol']),
                       'excess_spy_pp': values[report['symbol']]-values['SPY'] if len(values) == 2 else None})
    return result


def publish(state, root=BASE, histories=None):
    from execute_trade import write_json
    latest = {}
    for key, report in sorted(state.items()): latest[report['symbol']] = report
    lines = ['# Analyst revision research', '', LIMITS, '',
             '| Symbol | Observed | Coverage | Up / down firms (30d) | Median revision | Estimate history |',
             '|---|---|---|---|---|---|']
    for symbol, report in sorted(latest.items()):
        window = report['windows']['30']
        revision = f"{window['median_revision_pct']:.2f}%" if window['median_revision_pct'] is not None else 'unavailable'
        lines.append(f"| {symbol} | {report['observed_at']} | {report['status']} | {window['up_firms']} / {window['down_firms']} | {revision} | {report['estimate_changes']['previous_observed_at'] or 'not yet available'} |")
    lines += ['', '## Quarantined provider records', '',
              'Records below are excluded, not relabeled by inference. A consistent later provider observation can restore eligibility; previous observations remain immutable.']
    for symbol, report in sorted(latest.items()):
        for item in report.get('quarantined_records', []):
            lines.append(f"- {symbol} / {item['at']} / {item['firm']}: {', '.join(item['reasons'])}. Record `{item['id']}`; source: {item.get('url') or 'unavailable'}")
    lines += ['', 'Forward outcome records: [analyst_revision_performance.json](state/analyst_revision_performance.json).',
              'No baseline forecast history means unknown earnings support, not unchanged estimates.',
              'Earnings improvements are not required: reviews also examine company news, sector/theme attention and valuation. '
              'Attributed analyst reasons, contextual hypotheses and unknowns are stored separately.']
    if histories is not None:
        # Keep one forward cohort per unique matched-event set, not repeated daily votes.
        cohorts = {}
        for key, report in sorted(state.items()):
            events = sorted(r['id'] for r in report['windows']['30']['revisions'])
            ident = identity([report['symbol'], report['status'], events])
            if ident not in cohorts:
                cohorts[ident] = {'symbol': report['symbol'], 'observed_at': report['observed_at'],
                                 'direction': report['direction'], 'coverage_status': report['status'],
                                 'observation_key': key,
                                 'window_30d': {k: v for k, v in report['windows']['30'].items() if k != 'revisions'},
                                 'results': forward_score(report, histories)}
        output = {'cohorts': cohorts, 'limits': 'Prospective observed cohorts, overlapping and selected universe; total returns before costs, no causal attribution or proven predictive benefit. Baseline is next session close.'}
        write_json(str(root/'state/analyst_revision_performance.json'), output)
        lines += ['', output['limits'], '', f'Unique observed cohorts: {len(cohorts)}',
                  f"Mature endpoints: {sum(r['status']=='measured' for c in cohorts.values() for r in c['results'])}"]
    (root/'ANALYST_REVISIONS.md').write_text('\n'.join(lines)+'\n')
