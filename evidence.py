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
         'market_cap': 'USD', 'volume': 'shares', 'volume_avg20': 'shares',
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
                                      'rsi', 'volume', 'volume_avg20', 'price_date', 'price_at'} or metric.startswith('return_')
            stamp = (row.get('price_at') or row.get('price_date')) if quote_metric else observed_at
            if not stamp:
                continue
            ident = f'{symbol}.{metric}'
            facts[ident] = dict(symbol=symbol, metric=metric, value=value, unit=unit,
                                as_of=stamp, source=(origin + (' / FMP price-target-summary.lastQuarterAvgPriceTarget' if metric == 'analyst_target' and origin.startswith('weekly_data') else '')), snapshot=snapshot)
        for metric in ('sma50', 'sma200'):
            price_id = f'{symbol}.last_price' if f'{symbol}.last_price' in facts else f'{symbol}.price'
            base_id = f'{symbol}.{metric}'
            if price_id in facts and base_id in facts and facts[base_id]['value'] > 0:
                name = f'above_{metric}_pct'
                facts[f'{symbol}.{name}'] = dict(symbol=symbol, metric=name,
                    value=round((facts[price_id]['value'] / facts[base_id]['value'] - 1) * 100, 4),
                    unit=f'% vs {metric}', as_of=facts[price_id]['as_of'], source=origin,
                    snapshot=snapshot, operands=[price_id, base_id])
    return facts


def render(text, facts):
    if not isinstance(text, str):
        raise ValueError('Evidence prose must be text')
    stripped = REFERENCE.sub('', text)
    # Indicator names are parameters, not asserted measured values.
    stripped = re.sub(r'\b(?:SMA(?:50|200)|RSI\(14\)|(?:50|200)(?:[- ]day|d))\b', '', stripped)
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
    def visit(value):
        if isinstance(value, dict):
            for key, child in list(value.items()):
                if isinstance(child, str) and key not in {'symbol', 'id', 'status', 'action', 'severity', 'type'}:
                    value[key] = render(child, facts)
                elif key == 'sections':
                    value[key] = {k: render(v, facts) for k, v in child.items()}
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(result)
    return result
