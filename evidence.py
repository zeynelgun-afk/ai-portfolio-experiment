"""Typed, snapshot-bound facts. Models reference facts; code prints their labels."""
import copy
import hashlib
import json
import math
import re

REFERENCE = re.compile(r"\{\{([A-Z][A-Z0-9.-]*\.[a-z][a-z0-9_]*)\}\}")
PROSE = {'text', 'thesis_summary', 'thesis_assessment', 'new_thesis_summary',
         'reasoning', 'falsifier', 'saturday_note', 'risk', 'exit_plan'}
INSTRUCTION = """Evidence protocol: Write qualitative prose. For EVERY numeric market
fact or date insert {{SYMBOL.metric}} using an exact ID from SOURCE_LEDGER. Do not
copy raw numbers into prose, including numbers from old commentary or research
opinions. The renderer inserts company, metric, value, unit, as-of and source.
Do not relabel a reference as another metric or company. If a fact has no ID, say
it is unavailable. Numeric decision parameters (amount_usd, shares, new_stop,
condition value/days) are your choices, not measured facts; keep those in JSON
fields and explain them qualitatively. Never fabricate a reference. Do not put
references in numeric decision fields. Research dossiers are opinions, not
verified quantitative sources. This changes evidence handling, not investment
strategy or decision autonomy.
"""

UNITS = {'price': 'USD', 'last_price': 'USD', 'previous_close': 'USD',
         'sma50': 'USD', 'sma200': 'USD', 'analyst_target': 'USD',
         'market_cap': 'USD', 'volume': 'shares', 'volume_avg20': 'shares', 'volume_avg_20d': 'shares',
         'forward_pe': 'ratio', 'trailing_pe': 'ratio', 'rsi': 'index',
         'return_1w_pct': '% vs previous week', 'return_1m_pct': '% vs previous month',
         'return_3m_pct': '% vs previous quarter', 'earnings_date': 'date',
         'price_date': 'date', 'price_at': 'timestamp'}


def ledger(data, observed_at, origin):
    snapshot = hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False).encode()).hexdigest()
    facts = {}
    for symbol, row in data.items():
        if symbol.startswith('_') or not isinstance(row, dict):
            continue
        for metric, unit in UNITS.items():
            value = row.get(metric)
            if value is None or isinstance(value, bool):
                continue
            if not isinstance(value, (str, int, float)):
                continue
            if isinstance(value, (int, float)) and not math.isfinite(value):
                continue
            # Fundamentals are observations at collection time, not statements
            # that their reporting period equals the quote's session date.
            quote_metric = metric in {'price', 'last_price', 'previous_close', 'sma50', 'sma200',
                                      'rsi', 'volume', 'volume_avg20', 'volume_avg_20d', 'price_date', 'price_at'} or metric.startswith('return_')
            stamp = ((row.get('price_at') or row.get('price_date')) if metric in {'price', 'last_price', 'price_at'}
                     else (row.get('price_date') or row.get('price_at'))) if quote_metric else observed_at
            if not stamp:
                continue
            providers = row.get('providers', {})
            if quote_metric:
                provider = row.get('daily_provider') if metric in {'previous_close', 'volume_avg20', 'volume_avg_20d'} else row.get('price_provider')
                provider = provider or providers.get('history')
            elif metric == 'earnings_date':
                provider = providers.get('earnings')
            elif metric == 'analyst_target':
                provider = 'FMP'
            else:
                provider = providers.get('fundamentals')
            field_source = origin + (' / ' + provider if provider else '')
            ident = f'{symbol}.{metric}'
            facts[ident] = dict(symbol=symbol, metric=metric, value=value, unit=unit,
                                as_of=stamp, source=(field_source + (' / FMP price-target-summary.lastQuarterAvgPriceTarget' if metric == 'analyst_target' and origin.startswith('weekly_data') else '')), snapshot=snapshot)
        for metric, fact in row.get('fundamental_research', {}).get('facts', {}).items():
            if not re.fullmatch(r'[a-z][a-z0-9_]*', metric) or not isinstance(fact, dict):
                raise ValueError('Invalid fundamental fact identity')
            if not fact.get('as_of') or not fact.get('source') or not fact.get('unit'):
                raise ValueError('Fundamental fact provenance missing')
            value = fact.get('value')
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Invalid fundamental fact value')
            facts[f'{symbol}.{metric}'] = dict(fact, symbol=symbol, metric=metric, snapshot=snapshot)
        analyst = row.get('analyst_revisions', {})
        for window, measurements in analyst.get('windows', {}).items():
            for field in ('up_firms', 'down_firms', 'matched_firms', 'unchanged_firms', 'unpaired_firms', 'median_revision_pct', 'target_dispersion_pct'):
                value = measurements.get(field)
                if value is None or analyst.get('status') != 'ok':
                    continue
                metric = 'analyst_' + field + '_' + window + 'd'
                facts[f'{symbol}.{metric}'] = dict(symbol=symbol, metric=metric, value=value,
                    unit='firms' if field.endswith('firms') else '%', as_of=analyst['observed_at'],
                    source='FMP price-target-news / same-firm matched observations', snapshot=snapshot)
        for period, changes in analyst.get('estimate_changes', {}).get('periods', {}).items():
            for field in ('epsAvg','revenueAvg'):
                change=changes.get(field,{})
                name = 'eps' if field == 'epsAvg' else 'revenue'
                for suffix, value, unit in (('', change.get('current'), 'USD/share' if name == 'eps' else 'USD'),
                                            ('_revision_pct', change.get('change_pct'), '% vs prior observed consensus')):
                    if value is None:
                        continue
                    metric = 'analyst_' + name + '_' + period.replace('-', '') + suffix
                    facts[f'{symbol}.{metric}'] = dict(symbol=symbol, metric=metric, value=value,
                        unit=unit, as_of=analyst['observed_at'], fiscal_period=period,
                        previous_observed_at=analyst['estimate_changes'].get('previous_observed_at'),
                        source='FMP analyst-estimates / annual consensus forecast, not reported result', snapshot=snapshot)
        for window, summary in analyst.get('estimate_revision_windows',{}).items():
            for change in summary.get('periods',[]):
                metric='analyst_revenue_'+change['fiscal_period'].replace('-','')+'_revision_'+window+'d_pct'
                facts[f'{symbol}.{metric}']=dict(symbol=symbol,metric=metric,
                    value=change['revision_pct'],unit='% vs same-period consensus snapshot',
                    as_of=analyst['observed_at'],fiscal_period=change['fiscal_period'],
                    previous_observed_at=summary.get('baseline_observed_at'),
                    source='FMP analyst-estimates / same-fiscal-period consensus snapshots; not individual analyst breadth',
                    snapshot=snapshot)
        for metric in ('sma50', 'sma200'):
            price_id = f'{symbol}.last_price' if f'{symbol}.last_price' in facts else f'{symbol}.price'
            base_id = f'{symbol}.{metric}'
            if price_id in facts and base_id in facts and facts[base_id]['value'] > 0:
                name = f'above_{metric}_pct'
                facts[f'{symbol}.{name}'] = dict(symbol=symbol, metric=name,
                    value=round((facts[price_id]['value'] / facts[base_id]['value'] - 1) * 100, 4),
                    unit=f'% vs {metric}', as_of=facts[price_id]['as_of'], source=facts[price_id]['source'],
                    snapshot=snapshot, operands=[price_id, base_id])
    return facts


def render(text, facts, claim_ids=()):
    if not isinstance(text, str):
        raise ValueError('Evidence prose must be text')
    stripped = REFERENCE.sub('', text)
    for ident in claim_ids:
        stripped=re.sub(r'(?<![A-Za-z0-9_-])'+re.escape(ident)+r'(?![A-Za-z0-9_-])','',stripped)
    # Indicator names are parameters, not asserted measured values.
    stripped = re.sub(r'\b(?:SMA(?:50|200)|RSI\(14\)|(?:50|200)(?:[- ]day|d))\b', '', stripped)
    stripped = re.sub(r'\bprice_(?:below|above)_sma(?:50|200)_pct\b', '', stripped)
    if re.search(r'\d', stripped) or '{{' in stripped or '}}' in stripped:
        raise ValueError('Raw numeric claim or malformed evidence reference')
    def expand(match):
        key = match[1]
        if key not in facts:
            raise ValueError(f'Unknown evidence reference: {key}')
        fact = facts[key]
        if key != fact['symbol'] + '.' + fact['metric']:
            raise ValueError('Evidence identity mismatch')
        return (f"[{fact['symbol']} | {fact['metric']}: {fact['value']} {fact['unit']} | "
                f"as-of {fact['as_of']} | {fact['source']} | snapshot {fact['snapshot'][:12]}]")
    return REFERENCE.sub(expand, text)


def render_payload(payload, facts):
    """Render only prose fields; decision parameters stay numeric and executable."""
    result = copy.deepcopy(payload)
    issuers={fact['symbol'] for fact in facts.values()}
    claim_ids=set()
    def identifiers(value):
        if isinstance(value,dict):
            for claim in value.get('claims',[]) if isinstance(value.get('claims',[]),list) else []:
                ident=claim.get('id') if isinstance(claim,dict) else None
                if isinstance(ident,str) and any(re.fullmatch(re.escape(symbol)+r'-[A-Za-z0-9_-]{1,64}',ident) for symbol in issuers):
                    claim_ids.add(ident)
            for child in value.values():identifiers(child)
        elif isinstance(value,list):
            for child in value:identifiers(child)
    identifiers(result)
    def visit(value):
        if isinstance(value, dict):
            for key, child in list(value.items()):
                if isinstance(child, str) and key not in {'symbol', 'id', 'status', 'action', 'severity', 'type', 'next_review_at', 'claim_id'}:
                    value[key] = render(child, facts, claim_ids)
                elif key == 'sections':
                    value[key] = {k: render(v, facts, claim_ids) for k, v in child.items()}
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(result)
    return result
