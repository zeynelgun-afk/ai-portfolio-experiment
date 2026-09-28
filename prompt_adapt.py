#!/usr/bin/env python3
"""Automatically select vetted evidence reminders; never generate or merge rules."""
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone

BASE = Path(__file__).parent
MIN_SAMPLES = 20
REGRESSION_MARGIN = 0.15


def load(path, default):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else default


def save(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write('\n')
        temporary = handle.name
    os.replace(temporary, path)


def recipes():
    return load(BASE/'prompts/adaptations.json', {})


def reminders():
    state = load(os.environ.get('PROMPT_ADAPTATION_STATE', BASE/'state/prompt_adaptation.json'), {})
    allowed = recipes()
    return '\n'.join(allowed[key]['text'] for key in state.get('active', []) if key in allowed)


def record_result(success):
    path = os.environ.get('PROMPT_METRICS_PATH')
    if not path:
        return
    metrics = load(path, {'success': 0, 'failure': 0})
    field = 'success' if success else 'failure'
    metrics[field] += 1
    save(path, metrics)


def adapt(patterns, state, metrics):
    state = json.loads(json.dumps(state))
    state.setdefault('active', [])
    state.setdefault('quarantined', [])
    state.setdefault('history', [])
    total = metrics.get('success', 0) + metrics.get('failure', 0)
    failures = metrics.get('failure', 0)
    trial = state.get('trial')
    event = None
    if trial:
        sample = total - trial['start_total']
        if sample >= MIN_SAMPLES:
            rate = (failures - trial['start_failures']) / sample
            if rate > trial['baseline_rate'] + REGRESSION_MARGIN:
                state['active'].remove(trial['recipe'])
                state['quarantined'].append(trial['recipe'])
                event = {'action': 'rollback', 'recipe': trial['recipe'], 'failure_rate': rate}
            else:
                event = {'action': 'retain', 'recipe': trial['recipe'], 'failure_rate': rate}
            state['trial'] = None
    elif total >= MIN_SAMPLES and not state['active']:
        for key, recipe in recipes().items():
            if key in state['quarantined'] or patterns.get(recipe['pattern'], {}).get('count', 0) < 3:
                continue
            state['active'] = [key]
            state['trial'] = {'recipe': key, 'start_total': total,
                              'start_failures': failures, 'baseline_rate': failures/total}
            event = {'action': 'activate', 'recipe': key, 'baseline_rate': failures/total}
            break
    if event:
        event['at'] = datetime.now(timezone.utc).isoformat()
        state['history'].append(event)
    return state, event


if __name__ == '__main__':
    state_path = BASE/'state/prompt_adaptation.json'
    patterns = load(BASE/'state/audit_patterns.json', {})
    metrics = load(os.environ.get('PROMPT_METRICS_PATH', BASE/'state/prompt_metrics.json'), {})
    before = load(state_path, {})
    after, event = adapt(patterns, before, metrics)
    rendered = '\n'.join(recipes()[key]['text'] for key in after.get('active', []) if key in recipes())
    (BASE/'state').mkdir(exist_ok=True)
    (BASE/'state/prompt_reminders.md').write_text(rendered + '\n', encoding='utf-8')
    if event:
        save(state_path, after)
        print('Prompt adaptation: ' + json.dumps(event))
        if event['action'] == 'rollback':
            raise SystemExit(2)
    else:
        print('Prompt adaptation: no change; waiting for evidence or monitoring an active reminder')
