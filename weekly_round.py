#!/usr/bin/env python3
"""Structured weekly decisions, deterministic execution and crash-safe local replay."""

import llm_transport
import argparse
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import evidence
from execute_trade import execute, number, read_json, validate, write_json
from market_time import session, market_open, recent, weekly_slot as slot
from reassess import call_llm

BASE = Path(__file__).resolve().parent
SYSTEM = """You are the autonomous weekly portfolio decision-maker. Follow the supplied
charter and weekly instructions, preserving their aggressive fundamental investment
mandate and all accountability sections. You have no filesystem tools. Return ONLY
one JSON object with this schema:
{
 "sections": {"A": "data status", "B": "causes of moves", "C": "thesis health",
              "D": "decisions, risks and exit plans", "E": "theme risk", "F": "audit and pending-note response"},
 "decisions": [{"symbol": "TICKER", "action": "HOLD|BUY|SELL|TRIM",
                "amount_usd": null, "shares": null, "new_stop": null,
                "reasoning": "qualitative rationale with evidence references",
                "falsifier": "measurable falsifier explained qualitatively"}],
 "theses": {"TICKER": {"thesis_summary": "summary", "claims": [
    {"id": "TICKER-claim-name", "text": "claim", "status": "valid|weakened|invalid",
     "conditions": [{"type": "price_below", "value": 100, "severity": "thesis"}]}]}},
 "watchlist": [{"symbol": "TICKER", "action": "KEEP|DROP|OPEN", "reasoning": "reason"}],
 "pending_notes_addressed": true
}
List one decision for EVERY currently held symbol, then any new buys. Order sells
before buys if the proceeds fund buys. SELL means full exit; TRIM needs shares;
BUY needs amount_usd. HOLD may update new_stop. No position, cash or weight caps
are imposed. Weekend output is a research plan, never an executed order. During the session,
reconsider that plan against current evidence and prices. Execution prices are measured by code. Supply theses for exactly
the final held symbols. Every claim needs a supported measurable condition. Economic growth, margin and cash-flow
claims must include at least one fundamental_below/fundamental_above condition per holding
when measured fundamentals are available, with metric, value, unit and severity.
Supported metrics: revenue_yoy_pct, gross_margin_pct, operating_margin_pct,
quarter_operating_cash_flow, quarter_free_cash_flow, net_debt, total_debt. Use the source
unit exactly. Do not substitute a price threshold for an economic falsifier. Include
all watchlist symbols. Explain every pending note in F; set pending_notes_addressed
true only when all have been answered. Answer each note with its date and symbol,
and adopt, reject with reasons, or defer with an explicit unresolved-data explanation.
Addressed means answered, not that every uncertainty has been resolved or that a
weekend trade occurred. If there are no notes, say so in F and set the flag true.
No model-written prices, balances or fills.
Use source references for numeric factual prose; numeric choice fields remain numbers.
For every watchlist rationale, do not claim a trend, discontinuity, seasonal pattern
or balance-sheet change from a single-period snapshot or an unspecified dossier.
Name the dated comparative sources or explicitly label the pattern unverified.
"""


def read_weekly_context(root):
    context = {}
    for name in ('RULES.md', 'WEEKLY_INSTRUCTIONS.md', 'portfolio.json', 'REPORT.md',
                 'DECISION_LOG.md', 'theses.json', 'state/pending_notes.md', 'AUDIT.md', 'AUDIT_LOG.md',
                 'state/audit_disagreements.json'):
        path = root/name
        if not path.exists():
            context[name] = 'unavailable'
            continue
        text = path.read_text()
        # Pending work is a queue, not historical narrative: trimming its prefix
        # hid unacknowledged notes while requiring the model to answer all of them.
        context[name] = text if name == 'state/pending_notes.md' else text[-50000:]
    return context


def review_weekly_proposal(root, proposal, old_theses, data, facts, key):
    """Retain a rejected draft as evidence, never as an executable plan."""
    from claim_evidence import semantic_review
    snapshot = {'ledger': facts, 'input_data': data, 'proposal': proposal,
                'semantic_status': 'pending'}
    path = str(root/'output/weekly_evidence.json')
    write_json(path, snapshot)
    try:
        context = read_weekly_context(root)
        report = semantic_review(
            {'proposal': proposal, 'previous_theses': old_theses,
             'previous_accountability_records': {name: context[name] for name in
                  ('state/pending_notes.md', 'AUDIT.md', 'AUDIT_LOG.md')},
             'review_focus': 'Compare old and new conditions; reject price-only excuses for changing thresholds.'},
            data, facts, key, llm_transport.MODEL)
    except ValueError as error:
        snapshot.update(semantic_status='rejected', semantic_error=str(error))
        write_json(path, snapshot)
        raise
    snapshot.update(semantic_status='supported', semantic_review=report)
    write_json(path, snapshot)
    return report


def closing_day(round_time):
    day = round_time.date() - timedelta(days=1)
    for _ in range(10):
        bounds = session(day)
        if bounds and bounds[1] < round_time:
            return day.isoformat()
        day -= timedelta(days=1)
    raise ValueError('No completed weekly session')


def already_done(root, book, moment):
    round_date = slot(moment).date().isoformat()
    if round_date in book.get('completed_weekly_rounds', []):
        return True
    # Migration: existing historical rounds count, without editing those records.
    log = (root / 'DECISION_LOG.md').read_text()
    return bool(re.search(r'^## #\d+ — ' + round_date + r' · (?:WEEKLY ROUND|ROUND SKIPPED)', log, re.M))


def validate_theses(theses, book, moment, data=None):
    symbols = {p['symbol'] for p in book['positions']}
    if not isinstance(theses, dict) or set(theses) != symbols:
        raise ValueError('Theses must match the final holdings exactly')
    allowed = {'price_below_sma50_pct','price_above_sma50_pct','price_below_sma200_pct','price_above_sma200_pct','price_below', 'price_above', 'daily_change_above_pct', 'sector_etf_above_pct', 'stop_proximity_pct', 'volume_ratio_20d',
               'daily_change_pct', 'sector_etf_change_pct', 'earnings_approaching', 'fundamental_below', 'fundamental_above'}
    ids = set()
    for symbol, block in theses.items():
        if set(block) != {'thesis_summary', 'claims'}:
            raise ValueError('Unexpected thesis fields')
        if not block.get('thesis_summary') or not block.get('claims'):
            raise ValueError('Each holding requires a thesis and measurable claims')
        block['source'] = 'deterministic weekly round ' + slot(moment).date().isoformat()
        from fundamentals import MONITOR_METRICS, measured_fact
        available={metric:fact for metric,fact in (data or {}).get(symbol,{}).get('fundamental_research',{}).get('facts',{}).items() if metric in MONITOR_METRICS}
        if available and not any(c.get('type','').startswith('fundamental_') for claim in block['claims'] for c in claim.get('conditions',[])):
            raise ValueError('A holding with measured fundamentals needs at least one economic thesis condition')
        for claim in block['claims']:
            if set(claim) != {'id', 'text', 'status', 'conditions'}:
                raise ValueError('Unexpected claim fields')
            ident = claim.get('id', '')
            if not isinstance(ident, str) or not ident.startswith(symbol + '-') or ident in ids:
                raise ValueError('Invalid or duplicate claim identity')
            ids.add(ident)
            if not claim.get('text') or claim.get('status') not in {'valid', 'weakened', 'invalid'}:
                raise ValueError('Invalid claim text/status')
            if not claim.get('conditions'):
                raise ValueError('Unmeasurable claim')
            for condition in claim['conditions']:
                if set(condition) - {'type', 'value', 'days', 'severity', 'symbol', 'metric', 'unit'}:
                    raise ValueError('Unexpected condition fields')
                kind = condition.get('type')
                if kind not in allowed or condition.get('severity') not in {'warning', 'claim', 'thesis'}:
                    raise ValueError('Unsupported detector condition')
                if kind.startswith('fundamental_'):
                    from fundamentals import MONITOR_METRICS
                    if condition.get('metric') not in MONITOR_METRICS or not isinstance(condition.get('unit'), str) or not condition['unit']:
                        raise ValueError('Fundamental condition needs supported metric and explicit unit')
                    if data is not None and measured_fact(condition,data.get(symbol,{}),moment.date()) is None:
                        raise ValueError('Fundamental condition has no fresh matching metric/unit evidence')
                if '_sma' in kind and data is not None:
                    average=number(data.get(symbol,{}).get(kind.split('_')[2]))
                    if average is None or average<=0:raise ValueError('Moving-reference condition has no measured average')
                field = 'days' if kind == 'earnings_approaching' else 'value'
                val = number(condition.get(field))
                if val is None or (kind in {'price_below', 'price_above', 'volume_ratio_20d'} and val <= 0):
                    raise ValueError('Invalid condition threshold')
                if kind in {'earnings_approaching', 'stop_proximity_pct'} and val < 0:
                    raise ValueError('Negative condition distance')
                if kind in {'sector_etf_change_pct','sector_etf_above_pct'} and condition.get('symbol') not in {'SMH', 'SPY'}:
                    raise ValueError('Unsupported sector benchmark')
            claim.update(last_updated=moment.isoformat(), trigger=None)


def prepare(proposal, book, old_theses, data, moment, existing_log, *, preview=False, quotes=None, decision_at=None):
    """All validation is performed on copies before writing anything."""
    if set(proposal) != {'sections', 'decisions', 'theses', 'watchlist', 'pending_notes_addressed'}:
        raise ValueError('Use exactly the requested weekly response fields')
    if set(proposal.get('sections', {})) != set('ABCDEF') or any(not t.strip() for t in proposal['sections'].values()):
        raise ValueError('Every accountability section A-F is mandatory')
    if proposal.get('pending_notes_addressed') is not True:
        raise ValueError('Pending notes must be answered explicitly in F: adopt, reject with reasons, or defer with the data gap. After answering every note, set pending_notes_addressed=true; this does not assert uncertainty is resolved or a weekend trade executed.')
    result = copy.deepcopy(book)
    decisions = proposal.get('decisions')
    if not isinstance(decisions, list) or not decisions:
        raise ValueError('Missing decisions')
    held = {p['symbol'] for p in book['positions']}
    seen, locks, fills = set(), {}, []
    for trade in book.get('trade_history', []):
        if str(trade.get('date', ''))[:10] == moment.date().isoformat():
            direction = 'SELL' if trade.get('action') in {'SELL', 'TRIM'} else trade.get('action')
            locks[f"{moment.date().isoformat()}:{trade.get('symbol')}:{direction}"] = True
    if not preview and not market_open(moment):
        raise ValueError('Weekly execution requires an open NYSE session')
    expected_date = closing_day(slot(moment))
    measured = {}
    for symbol, row in data.items():
        if not symbol.startswith('_') and isinstance(row, dict) and row.get('price_date') == expected_date:
            measured[symbol] = {'price': row.get('last_price'), 'data_source': 'weekly_close'}
    if not preview:
        measured = quotes or {}
        for symbol, row in measured.items():
            if (not recent(row.get('price_at'), moment, 900) or
                    not market_open(datetime.fromisoformat(row['price_at']))):
                raise ValueError(f'{symbol}: stale or out-of-session execution quote')
    for decision in decisions:
        if set(decision) - {'symbol', 'action', 'amount_usd', 'shares', 'new_stop', 'reasoning', 'falsifier', 'monitoring', 'analyst_review'}:
            raise ValueError('Unexpected decision fields')
        symbol = decision.get('symbol')
        if not isinstance(symbol, str) or not re.fullmatch(r'[A-Z][A-Z0-9.-]{0,9}', symbol) or symbol in seen:
            raise ValueError('Invalid or duplicate decision symbol')
        seen.add(symbol)
        if not decision.get('reasoning') or not decision.get('falsifier'):
            raise ValueError('Missing rationale or falsifier')
        stop = decision.get('new_stop')
        if stop is not None and (number(stop) is None or number(stop) <= 0):
            raise ValueError('Invalid exit level')
        if decision.get('action') == 'HOLD':
            if symbol not in held:
                raise ValueError('Cannot HOLD a missing position')
            if stop is not None:
                next(p for p in result['positions'] if p['symbol'] == symbol)['stop_weekly_close'] = number(stop)
            continue
        ok, reason, details = validate(decision, result, measured, True, locks,
                                        moment.date(), price_source='weekly_close' if preview else 'intraday_5m')
        if not ok:
            raise ValueError(f'{symbol}: {reason}')
        record = execute(decision, result, details, moment, source='weekly_autonomous')
        record.update(round_id=slot(moment).date().isoformat(),
                      price_date=expected_date if preview else moment.date().isoformat(),
                      research_session=expected_date,
                      price_provider=(data.get(symbol, {}).get('providers', {}).get('history', 'unknown') if preview else measured[symbol]['price_provider']),
                      price_at=expected_date if preview else measured[symbol]['price_at'],
                      decision_at=(decision_at or moment).isoformat())
        fills.append(record)
        locks[details['lock']] = True
    if not held <= seen:
        raise ValueError('Every existing holding needs a decision, including HOLD')
    theses = copy.deepcopy(proposal.get('theses'))
    validate_theses(theses, result, moment, data)
    theses['_meta'] = copy.deepcopy(old_theses['_meta'])
    for position in result['positions']:
        position['next_earnings'] = data.get(position['symbol'], {}).get('earnings_date')
    result.setdefault('completed_weekly_rounds', []).append(slot(moment).date().isoformat())
    indices = [int(n) for n in re.findall(r'^## #(\d+) ', existing_log, re.M)]
    lines = [f"\n## #{max(indices, default=0) + 1} — {slot(moment).date().isoformat()} · WEEKLY ROUND\n",
             f"{'Preview only' if preview else 'Executed in session'} at {moment.isoformat()}; research closing session {expected_date}.\n"]
    for key, title in zip('ABCDEF', ['Data status', 'Causes of moves', 'Thesis health', 'Decisions', 'Theme risk', 'Accounting for yourself']):
        lines += [f'### {key}. {title}\n', proposal['sections'][key], '']
    lines += ['### Deterministic execution\n', '```json', json.dumps(fills, indent=2), '```']
    for d in decisions:
        lines += [f"\n**{d['symbol']} — {d['action']}**: {d['reasoning']}", f"Falsifier: {d['falsifier']}"]
    for decision in decisions:
        if decision.get('monitoring') and decision['symbol'] in theses:
            import decision_lifecycle as lifecycle
            symbol=decision['symbol']
            facts=evidence.ledger(data,moment.isoformat(),'weekly_data/market_data')
            monitor=lifecycle.validate_monitoring(decision['monitoring'],symbol,old_theses.get(symbol,{}),data,facts,moment, next((p.get('stop_weekly_close') for p in book['positions'] if p['symbol']==symbol),None),decision.get('new_stop'))
            if monitor['claims'] != proposal['theses'][symbol]['claims']:
                raise ValueError('Decision monitors and thesis claims must be identical')
            theses[symbol]['monitoring']=monitor
            if decision.get('analyst_review'):
                from analyst_revisions import validate_review
                theses[symbol]['analyst_review'] = validate_review(decision['analyst_review'], symbol, data, facts)
    return result, theses, existing_log + '\n'.join(lines) + '\n'


def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as out:
        out.write(text)
        out.flush()
        os.fsync(out.fileno())
    os.replace(out.name, path)


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def commit_bundle(root, targets):
    path = root / 'state/weekly_transaction.json'
    if path.exists():
        raise ValueError('Pending transaction must be recovered first')
    before = {name: digest((root/name).read_text() if (root/name).exists() else '') for name in targets}
    write_json(str(path), {'before': before, 'targets': targets})
    recover(root)


def recover(root):
    path = root / 'state/weekly_transaction.json'
    if not path.exists():
        return False
    journal = read_json(str(path), None)
    allowed = {'portfolio.json', 'theses.json', 'DECISION_LOG.md', 'state/pending_notes.md', 'state/watchlist.json', 'state/weekly_plan.json', 'state/research_observations.json', 'state/corporate_actions.json', 'CORPORATE_ACTIONS.md', 'state/violations.json', 'state/decision_history.json'}
    if set(journal['targets']) - allowed:
        raise ValueError('Unexpected transaction target')
    for name, target in journal['targets'].items():
        current = (root/name).read_text() if (root/name).exists() else ''
        if digest(current) not in {journal['before'][name], digest(target)}:
            raise ValueError('Transaction conflict: refuse to overwrite newer state')
    for name, target in journal['targets'].items():
        atomic_text(root/name, target)
    path.unlink()
    return True


def build_targets(proposal, book, old_theses, data, moment, original_log, **execution):
    book, theses, log = prepare(proposal, book, old_theses, data, moment,
                                original_log, **execution)
    watchlist = proposal.get('watchlist', [])
    expected = {s for s in data if not s.startswith('_')}
    if len(watchlist) != len(expected) or {r['symbol'] for r in watchlist} != expected:
        raise ValueError('Every researched symbol needs exactly one watchlist disposition; missing=' + ','.join(sorted(expected - {r['symbol'] for r in watchlist})) + '; unexpected=' + ','.join(sorted({r['symbol'] for r in watchlist} - expected)))
    kept = []
    from counters import compute_counters, split_rounds
    counters = {s: row[1] for s, row in compute_counters(split_rounds(original_log),
                book.get("trade_history", []), expected).items()}
    for row in watchlist:
        if set(row) != {'symbol', 'action', 'reasoning'} or not row['reasoning']:
            raise ValueError('Invalid watchlist response fields')
        symbol, action = row['symbol'], row['action']
        if action not in {'KEEP', 'DROP', 'OPEN'}:
            raise ValueError('Invalid watchlist disposition')
        opened = any(p['symbol'] == symbol for p in book['positions'])
        if action == 'OPEN' and not opened:
            raise ValueError('Watchlist OPEN requires an executed position')
        if counters.get(symbol, 0) >= 3 and action == 'KEEP' and not opened:
            raise ValueError('Deferral threshold requires opening or dropping')
        if action != 'DROP':
            kept.append(symbol)
        log += f"\n{symbol} — deferred: {counters.get(symbol, 0)}/3 — {'DROP FROM LIST' if action == 'DROP' else action} — {row['reasoning']}\n"
    targets = {'portfolio.json': json.dumps(book, indent=2) + '\n',
               'theses.json': json.dumps(theses, indent=2) + '\n', 'DECISION_LOG.md': log,
               'state/pending_notes.md': '', 'state/watchlist.json': json.dumps(kept, indent=2) + '\n'}
    return targets


def live_quotes(symbols, moment):
    import market_data
    quotes = {}
    for symbol in symbols:
        frame = market_data.history(symbol, '1d', '5m', now=moment)
        quotes[symbol] = {'price': float(frame['Close'].iloc[-1]),
                          'data_source': 'intraday_5m',
                          'price_at': frame.index[-1].isoformat(),
                          'price_provider': frame.attrs['provider']}
    return quotes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--execute-pending', action='store_true')
    args = parser.parse_args()
    moment = datetime.now(timezone.utc)
    if not args.dry_run and recover(BASE):
        print('Recovered an already validated transaction; no second decision requested')
        return
    plan_path = BASE/'state/weekly_plan.json'
    plan = read_json(str(plan_path), {})
    book = read_json(str(BASE/'portfolio.json'), None)
    if already_done(BASE, book, moment):
        print('Weekly slot already executed; no replay')
        return
    round_id = slot(moment).date().isoformat()
    if args.execute_pending:
        if not market_open(moment) or plan.get('status') != 'pending':
            print('No pending weekly plan eligible for session execution')
            return
        if plan.get('round_id') != round_id:
            raise ValueError('Expired weekly plan: new research is required')
        # Rebuild research against current provider data; never blindly fill a weekend plan.
        import weekly_data
        weekly_data.main()
        moment = datetime.now(timezone.utc)
        if not market_open(moment):
            raise ValueError('Session closed while refreshing research')
    else:
        if moment.weekday() not in {5, 6}:
            raise ValueError('Weekly research window is Saturday/Sunday only')
        if plan.get('round_id') == round_id and plan.get('status') == 'pending':
            print('Weekend research already queued; portfolio remains unchanged')
            return
    data = read_json(str(BASE/'weekly_data.json'), None)
    if not data or data.get('_meta', {}).get('date') != moment.date().isoformat():
        raise ValueError('Research inputs must be freshly collected today')
    if data.get('_meta', {}).get('research_errors'):
        raise ValueError('Incomplete specialist research; no decision or execution')
    symbols = {s for s in data if not s.startswith('_')}
    quotes = live_quotes(symbols, moment) if args.execute_pending else None
    if quotes:
        for symbol, quote in quotes.items():
            data[symbol].update(price=quote['price'], last_price=quote['price'], price_at=quote['price_at'],
                                price_provider=quote['price_provider'])
    facts = evidence.ledger(data, data['_meta'].get('collected_at', moment.isoformat()), 'weekly_data/market_data')
    context = read_weekly_context(BASE)
    accountability_times = evidence.record_timestamps(context[name] for name in
        ('state/pending_notes.md', 'AUDIT.md', 'AUDIT_LOG.md'))
    from llm_context import research_view
    model_data = research_view(data)
    context['weekly_data.json'] = model_data
    context['required_watchlist_symbols'] = sorted(symbols)
    context['watchlist_contract'] = 'Exactly one KEEP/DROP/OPEN row for EVERY required_watchlist_symbols entry, including existing holdings. Do not omit a symbol because it is already held.'
    if quotes:
        from research_metrics import exposure
        context['current_exposure'] = exposure(book, quotes, data)
    context['mode'] = 'SESSION REASSESSMENT: reconsider the weekend plan; HOLD is valid' if args.execute_pending else 'WEEKEND RESEARCH ONLY: no trades until session reassessment'
    if args.execute_pending:
        context['weekend_plan'] = plan['proposal']
    key = llm_transport.credential()
    if not key:
        raise ValueError('Weekly decision API key is missing')
    old_theses = read_json(str(BASE/'theses.json'), {})
    original_log = (BASE/'DECISION_LOG.md').read_text()
    import decision_lifecycle as lifecycle
    from analyst_revisions import REVIEW_INSTRUCTION, validate_review
    context['NOW']=moment.isoformat()
    context['monitoring_instruction']=lifecycle.INSTRUCTION
    def validate_proposal(payload):
        for decision in payload.get('decisions',[]):
            symbol=decision['symbol']
            if data.get(symbol, {}).get('analyst_revisions'):
                validate_review(decision.get('analyst_review'), symbol, model_data, facts)
            lifecycle.validate_monitoring(decision.get('monitoring'),symbol,old_theses.get(symbol,{}),model_data,facts,moment, next((p.get('stop_weekly_close') for p in book['positions'] if p['symbol']==symbol),None),decision.get('new_stop'))
        build_targets(payload, book, old_theses, data, moment, original_log,
                      preview=not args.execute_pending, quotes=quotes)
    (BASE/'output').mkdir(exist_ok=True)
    write_json(str(BASE/'output/weekly_evidence.json'), {'ledger': facts, 'input_data': data})
    reviewed = []
    def validate_semantics(candidate):
        reviewed[:] = [review_weekly_proposal(BASE, candidate, old_theses, data, facts, key)]
    proposal, status = call_llm(llm_transport.MODEL,
                                SYSTEM+"\n"+lifecycle.INSTRUCTION+"\n"+REVIEW_INSTRUCTION+"\nPut monitoring and analyst_review inside EACH decision; monitoring claims must exactly match the supplied final thesis claims.", json.dumps(context), key, source_ledger=facts,
                                response_validator=validate_proposal, semantic_validator=validate_semantics,
                                accountability_times=accountability_times, max_attempts=4)
    if not proposal:
        raise ValueError('Weekly proposal rejected: ' + status)
    from claim_evidence import semantic_review
    review = reviewed[0] if reviewed else semantic_review({'proposal':proposal,'previous_theses':old_theses,'review_focus':'Compare old and new conditions; reject price-only excuses for changing thresholds.'}, data, facts, key, llm_transport.MODEL)
    write_json(str(BASE/'output/weekly_evidence.json'), {'ledger': facts, 'input_data': data, 'proposal': proposal, 'semantic_review':review})
    if not args.execute_pending:
        build_targets(proposal, book, old_theses, data, moment, original_log, preview=True)
        if not args.dry_run:
            write_json(str(plan_path), {'round_id': round_id, 'created_at': moment.isoformat(),
                       'status': 'pending', 'proposal': proposal, 'research_snapshot': digest(json.dumps(data, sort_keys=True))})
        print('Weekend research queued; no portfolio, thesis, cash or fill changes')
        return
    # Reprice after the decision, check session again, and reject stale/over-budget batches.
    decision_at = datetime.now(timezone.utc)
    if not market_open(decision_at):
        raise ValueError('Session closed during decision generation')
    quotes = live_quotes(symbols, decision_at)
    executed_at = datetime.now(timezone.utc)
    targets = build_targets(proposal, book, old_theses, data, executed_at, original_log, quotes=quotes, decision_at=decision_at)
    final_theses=json.loads(targets['theses.json'])
    changes=[{'symbol':d['symbol'],'action':d['action'],'time':executed_at.isoformat(),
              'trigger':'Weekly research reassessed in-session','reasoning':d['reasoning'],
              'falsifier':d['falsifier'],'before':old_theses.get(d['symbol'],{}),'after':final_theses.get(d['symbol'],{})} for d in proposal['decisions']]
    history=lifecycle.history_update(read_json(str(BASE/'state/decision_history.json'),{}),changes)
    targets['state/decision_history.json']=json.dumps(history,indent=2)+'\n'
    plan.update(status='executed', executed_at=executed_at.isoformat())
    targets['state/weekly_plan.json'] = json.dumps(plan, indent=2) + '\n'
    from research_metrics import observation, exposure
    benchmarks = live_quotes({'SPY','SMH'}, datetime.now(timezone.utc))
    final_time = datetime.now(timezone.utc)
    if not market_open(final_time) or not recent(decision_at.isoformat(), final_time, 900) or any(not recent(q['price_at'], final_time, 900) for q in {**quotes, **benchmarks}.values()):
        raise ValueError('Session/quote expired before final commit')
    cohorts = read_json(str(BASE/'state/research_observations.json'), {})
    if round_id in cohorts:
        raise ValueError('Research cohort already recorded')
    cohorts[round_id] = observation(round_id, executed_at, proposal, data, quotes,
        read_json(str(BASE/'state/discovery.json'), {}), benchmarks,
        exposure(json.loads(targets['portfolio.json']), quotes, data))
    targets['state/research_observations.json'] = json.dumps(cohorts, indent=2) + '\n'
    if args.dry_run:
        print('Session proposal validated; dry-run writes no investment records')
        return
    commit_bundle(BASE, targets)
    print('Weekly plan reassessed and executed in-session with current prices')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            out.write('executed=true\n')


if __name__ == '__main__':
    main()
