#!/usr/bin/env python3
"""Structured weekly decisions, deterministic execution and crash-safe local replay."""
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
from market_time import session, weekly_slot as slot
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
are imposed. Prices come only from measured closing data. Supply theses for exactly
the final held symbols. Every claim needs a supported measurable condition. Include
all watchlist symbols. Explain every pending note in F; set pending_notes_addressed
true only when all have been answered. No model-written prices, balances or fills.
Use source references for numeric factual prose; numeric choice fields remain numbers.
"""


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


def validate_theses(theses, book, moment):
    symbols = {p['symbol'] for p in book['positions']}
    if not isinstance(theses, dict) or set(theses) != symbols:
        raise ValueError('Theses must match the final holdings exactly')
    allowed = {'price_below', 'stop_proximity_pct', 'volume_ratio_20d',
               'daily_change_pct', 'sector_etf_change_pct', 'earnings_approaching'}
    ids = set()
    for symbol, block in theses.items():
        if set(block) != {'thesis_summary', 'claims'}:
            raise ValueError('Unexpected thesis fields')
        if not block.get('thesis_summary') or not block.get('claims'):
            raise ValueError('Each holding requires a thesis and measurable claims')
        block['source'] = 'deterministic weekly round ' + slot(moment).date().isoformat()
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
                if set(condition) - {'type', 'value', 'days', 'severity', 'symbol'}:
                    raise ValueError('Unexpected condition fields')
                kind = condition.get('type')
                if kind not in allowed or condition.get('severity') not in {'warning', 'claim', 'thesis'}:
                    raise ValueError('Unsupported detector condition')
                field = 'days' if kind == 'earnings_approaching' else 'value'
                val = number(condition.get(field))
                if val is None or (kind in {'price_below', 'volume_ratio_20d'} and val <= 0):
                    raise ValueError('Invalid condition threshold')
                if kind in {'earnings_approaching', 'stop_proximity_pct'} and val < 0:
                    raise ValueError('Negative condition distance')
                if kind == 'sector_etf_change_pct' and condition.get('symbol') not in {'SMH', 'SPY'}:
                    raise ValueError('Unsupported sector benchmark')
            claim.update(last_updated=moment.isoformat(), trigger=None)


def prepare(proposal, book, old_theses, data, moment, existing_log):
    """All validation is performed on copies before writing anything."""
    if set(proposal) != {'sections', 'decisions', 'theses', 'watchlist', 'pending_notes_addressed'}:
        raise ValueError('Use exactly the requested weekly response fields')
    if set(proposal.get('sections', {})) != set('ABCDEF') or any(not t.strip() for t in proposal['sections'].values()):
        raise ValueError('Every accountability section A-F is mandatory')
    if proposal.get('pending_notes_addressed') is not True:
        raise ValueError('Pending notes must be answered explicitly')
    result = copy.deepcopy(book)
    decisions = proposal.get('decisions')
    if not isinstance(decisions, list) or not decisions:
        raise ValueError('Missing decisions')
    held = {p['symbol'] for p in book['positions']}
    seen, locks, fills = set(), {}, []
    expected_date = closing_day(slot(moment))
    measured = {}
    for symbol, row in data.items():
        if not symbol.startswith('_') and isinstance(row, dict) and row.get('price_date') == expected_date:
            measured[symbol] = {'price': row.get('last_price'), 'data_source': 'weekly_close'}
    for decision in decisions:
        if set(decision) - {'symbol', 'action', 'amount_usd', 'shares', 'new_stop', 'reasoning', 'falsifier'}:
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
                                        slot(moment).date(), price_source='weekly_close')
        if not ok:
            raise ValueError(f'{symbol}: {reason}')
        record = execute(decision, result, details, moment, source='weekly_autonomous')
        record.update(round_id=slot(moment).date().isoformat(), price_date=expected_date,
                      price_provider=data.get(symbol, {}).get('providers', {}).get('history', 'unknown'))
        fills.append(record)
        locks[details['lock']] = True
    if not held <= seen:
        raise ValueError('Every existing holding needs a decision, including HOLD')
    theses = copy.deepcopy(proposal.get('theses'))
    validate_theses(theses, result, moment)
    theses['_meta'] = copy.deepcopy(old_theses['_meta'])
    for position in result['positions']:
        position['next_earnings'] = data.get(position['symbol'], {}).get('earnings_date')
    result.setdefault('completed_weekly_rounds', []).append(slot(moment).date().isoformat())
    indices = [int(n) for n in re.findall(r'^## #(\d+) ', existing_log, re.M)]
    lines = [f"\n## #{max(indices, default=0) + 1} — {slot(moment).date().isoformat()} · WEEKLY ROUND\n",
             f"Executed at {moment.isoformat()}; closing-price session {expected_date}.\n"]
    for key, title in zip('ABCDEF', ['Data status', 'Causes of moves', 'Thesis health', 'Decisions', 'Theme risk', 'Accounting for yourself']):
        lines += [f'### {key}. {title}\n', proposal['sections'][key], '']
    lines += ['### Deterministic execution\n', '```json', json.dumps(fills, indent=2), '```']
    for d in decisions:
        lines += [f"\n**{d['symbol']} — {d['action']}**: {d['reasoning']}", f"Falsifier: {d['falsifier']}"]
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
    allowed = {'portfolio.json', 'theses.json', 'DECISION_LOG.md', 'state/pending_notes.md', 'state/watchlist.json'}
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


def build_targets(proposal, book, old_theses, data, moment, original_log):
    book, theses, log = prepare(proposal, book, old_theses, data, moment,
                                original_log)
    watchlist = proposal.get('watchlist', [])
    expected = {s for s in data if not s.startswith('_')}
    if len(watchlist) != len(expected) or {r['symbol'] for r in watchlist} != expected:
        raise ValueError('Every researched symbol needs a watchlist disposition')
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    moment = datetime.now(timezone.utc)
    if not args.dry_run and recover(BASE):
        print('Recovered the validated weekly transaction; no second decision requested')
        return
    book = read_json(str(BASE/'portfolio.json'), None)
    if already_done(BASE, book, moment):
        print('Weekly slot already recorded; no replay')
        return
    # Catch-up is confined to the weekend, before another market session can open.
    if moment.weekday() not in {5, 6}:
        raise ValueError('Weekly catch-up window is Saturday/Sunday only')
    data = read_json(str(BASE/'weekly_data.json'), None)
    if not data or data.get('_meta', {}).get('date') != moment.date().isoformat():
        raise ValueError('Weekly inputs must be freshly collected today')
    facts = evidence.ledger(data, data['_meta'].get('collected_at', moment.isoformat()), 'weekly_data/market_data')
    context = {}
    for name in ('RULES.md', 'WEEKLY_INSTRUCTIONS.md', 'portfolio.json', 'REPORT.md',
                 'DECISION_LOG.md', 'theses.json', 'state/pending_notes.md', 'AUDIT.md', 'AUDIT_LOG.md'):
        path = BASE/name
        context[name] = path.read_text()[-50000:] if path.exists() else 'unavailable'
    context['weekly_data.json'] = data
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise ValueError('Weekly decision API key is missing')
    old_theses = read_json(str(BASE/'theses.json'), {})
    original_log = (BASE/'DECISION_LOG.md').read_text()
    def validate_proposal(payload):
        build_targets(payload, book, old_theses, data, moment, original_log)
    (BASE/'output').mkdir(exist_ok=True)
    write_json(str(BASE/'output/weekly_evidence.json'), {'ledger': facts, 'input_data': data})
    proposal, status = call_llm(os.environ.get('OPENROUTER_MODEL_WEEKLY') or 'anthropic/claude-opus-5.5',
                                SYSTEM, json.dumps(context), key, source_ledger=facts,
                                response_validator=validate_proposal)
    if not proposal:
        raise ValueError('Weekly proposal rejected: ' + status)
    targets = build_targets(proposal, book, old_theses, data, moment, original_log)
    (BASE/'output').mkdir(exist_ok=True)
    write_json(str(BASE/'output/weekly_evidence.json'), {'ledger': facts, 'input_data': data, 'proposal': proposal})
    if args.dry_run:
        print('Validated weekly proposal; dry-run writes no investment records')
        return
    commit_bundle(BASE, targets)
    print('Weekly proposal validated and saved with crash recovery and replay protection')


if __name__ == '__main__':
    main()
