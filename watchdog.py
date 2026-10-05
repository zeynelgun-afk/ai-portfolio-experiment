#!/usr/bin/env python3
"""Independent heartbeat and bounded repairs. Never edits investment data or code."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit

from execute_trade import read_json, write_json
from market_time import session
from notify_failure import notify
from market_time import weekly_slot as slot

REPO = 'zeynelgun-afk/ai-portfolio-experiment'
SAFE_STEPS = {'Dependencies', 'Set up Python', 'Run pip install -r requirements.txt'}
ACTIVE = {'queued', 'in_progress', 'waiting', 'pending', 'requested'}


def stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def due_windows(now):
    result = {}
    weekly = slot(now)
    # Saturday review remains due even when Friday is an exchange holiday.
    if now.weekday() in {5, 6} and weekly + timedelta(hours=2) <= now < weekly + timedelta(days=2):
        result['weekly.yml'] = weekly
    bounds = session(now.astimezone(ZoneInfo('America/New_York')).date())
    if bounds and bounds[0] + timedelta(minutes=90) <= now <= bounds[1]:
        result['detector.yml'] = max(bounds[0], now - timedelta(minutes=90))
    close_review = now.replace(hour=21, minute=15, second=0, microsecond=0)
    if bounds and now >= close_review + timedelta(minutes=90):
        result['detector.yml'] = close_review
    return result


def attempt_time(run):
    # GitHub resets run_started_at for reruns; updated_at also includes queue
    # and postprocessing updates, so it cannot establish execution ordering.
    return stamp(run.get('run_started_at') or run['created_at'])


def attempt_order(run):
    return (attempt_time(run), int(run.get('id', 0)), int(run.get('run_attempt', 1)))


def overdue_runs(runs, now):
    return [r for r in runs if r.get('head_branch') == 'main' and
            r.get('event') in {'schedule', 'workflow_dispatch'} and
            r['status'] in ACTIVE and now - attempt_time(r) > timedelta(hours=2)]


def diagnose(runs, since, now):
    active = [r for r in runs if r.get('head_branch') == 'main' and r.get('event') in {'schedule', 'workflow_dispatch'} and r['status'] in ACTIVE]
    if active:
        overdue = overdue_runs(active, now)
        return ('stuck', min(overdue, key=attempt_order)) if overdue else ('running', max(active, key=attempt_order))
    relevant = [r for r in runs if r.get('head_branch') == 'main' and
                r.get('event') in {'schedule', 'workflow_dispatch'} and attempt_time(r) >= since]
    if any(r['status'] in ACTIVE for r in relevant):
        running = [r for r in relevant if r['status'] in ACTIVE]
        if any(now - attempt_time(r) > timedelta(hours=2) for r in running):
            return 'stuck', running[0]
        return 'running', running[0]
    latest = max(relevant, key=attempt_order, default=None)
    if latest and latest.get('status') == 'completed' and latest.get('conclusion') == 'success':
        return 'healthy', latest
    return ('failed', latest) if latest else ('missing', None)


def api(endpoint, method='GET', payload=None):
    command = ['gh', 'api', f'repos/{REPO}/{endpoint}', '--method', method]
    if payload is not None:
        command += ['--input', '-']
    # Do not expose authentication output or URLs containing credentials.
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            text=True, capture_output=True, timeout=45)
    if result.returncode:
        raise RuntimeError('GitHub monitoring API unavailable')
    return json.loads(result.stdout) if result.stdout.strip() else {}


def repair_plan(kind, run, jobs):
    if kind == 'missing':
        return 'dispatch'
    # Re-running a historical Actions run reuses its OLD workflow SHA, which may
    # still be hosted/paid. Local unresolved claims need operator reconciliation.
    if os.environ.get('PORTFOLIO_EXECUTOR') == 'local-hermes':
        return None
    if kind != 'failed' or not run or run.get('conclusion') != 'failure':
        return None
    failed_steps = [s['name'] for j in jobs for s in j.get('steps', []) if s.get('conclusion') == 'failure']
    # Only a dependency bootstrap failure is rerunnable. A validation rejection,
    # data gap, trade, commit or Telegram failure never causes the round to replay.
    if failed_steps and set(failed_steps) <= SAFE_STEPS:
        succeeded_sensitive = any(s.get('conclusion') == 'success' and
            any(word in s.get('name', '').lower() for word in ('decision', 'execute', 'commit', 'reassess'))
            for j in jobs for s in j.get('steps', []))
        if not succeeded_sensitive:
            return 'rerun-failed-jobs'
    return None


def daily_anchor(now):
    anchor = now.replace(hour=23, minute=0, second=0, microsecond=0)
    return anchor if now >= anchor else anchor - timedelta(days=1)


class RemoteState:
    """Durable state on a separate branch; SHA preconditions prevent lost updates."""
    def __init__(self, fetch=api):
        self.fetch = fetch
        self.path = 'contents/watchdog.json'
        packet = fetch(self.path + '?ref=watchdog-state')
        self.sha = packet['sha']
        self.state = json.loads(base64.b64decode(packet['content']))
        if not isinstance(self.state, dict):
            raise ValueError('Invalid remote watchdog state; refusing to reset repair limits')

    def save(self, state):
        clean = {k: v for k, v in state.items() if k != '_persist'}
        content = base64.b64encode((json.dumps(clean, indent=2) + '\n').encode()).decode()
        packet = self.fetch(self.path, 'PUT', {'branch': 'watchdog-state',
            'sha': self.sha, 'message': 'Checkpoint daily watchdog state', 'content': content})
        self.sha = packet['content']['sha']


def acknowledge(state, workflow, observation_id, evidence, operator, now):
    """Acknowledge exactly one observed incident, never its future observations."""
    incident = state.get('incidents', {}).get(workflow)
    observation = incident.get('observation') if incident else None
    if (not observation or incident.get('resolved') or observation['observation_id'] != observation_id
            or not observation.get('run_id') or observation['status'] not in {'failed', 'stuck'}):
        raise ValueError('Acknowledgement requires the exact current failed/stuck run observation')
    overdue = observation.get('overdue_runs', [])
    identities = overdue or [{'run_id': observation['run_id'], 'run_attempt': observation['run_attempt']}]
    required = {f"run:{r['run_id']}:attempt:{r['run_attempt']}" for r in identities}
    url = f"/actions/runs/{observation['run_id']}/attempts/{observation['run_attempt']}"
    tokens = evidence.split(';')[0].split() if evidence else []
    scoped = required <= set(tokens) or (len(identities) == 1 and any(urlsplit(token).scheme == 'https' and
                                      urlsplit(token).netloc == 'github.com' and
                                      urlsplit(token).path.endswith(url) for token in tokens))
    if not scoped or not operator.strip() or ';' not in evidence or not evidence.split(';', 1)[1].strip():
        raise ValueError('Provide exact run/attempt identity; concrete evidence description; and operator')

    incident['acknowledgement'] = {'observation_id': observation_id, 'run_id': observation['run_id'],
        'run_attempt': observation['run_attempt'], 'evidence': evidence, 'operator': operator,
        'acknowledged_at': now.isoformat()}
    if overdue:
        incident['acknowledgement']['overdue_runs'] = [dict(r) for r in overdue]


def monitor(now, state, fetch=api, send=notify, apply=False, daily=False):
    state.setdefault('incidents', {})
    state.setdefault('daily_repairs', {})
    observations = []
    windows = due_windows(daily_anchor(now) if daily else now)
    if state.get('monitoring_started_at'):
        windows = {name: since for name, since in windows.items()
                   if since >= stamp(state['monitoring_started_at'])}
    # Continue checking an existing incident after its schedule window, but never
    # perform an out-of-window catch-up trade.
    for workflow, incident in state['incidents'].items():
        if not incident.get('resolved'):
            windows.setdefault(workflow, stamp(incident['since']))
    for workflow, since in windows.items():
        old = state['incidents'].get(workflow)
        current_since = since
        if old and not old.get('resolved'):
            since = min(since, stamp(old['since']))
        runs = fetch(f'actions/workflows/{workflow}/runs?branch=main&per_page=100')['workflow_runs']
        # A green calendar-only skip is not a measurement heartbeat.
        checked_runs = []
        for candidate in runs:
            if candidate.get('conclusion') == 'success' and candidate.get('head_branch') == 'main' and candidate.get('event') in {'schedule', 'workflow_dispatch'} and attempt_time(candidate) >= since:
                jobs = fetch(f"actions/runs/{candidate['id']}/jobs")['jobs']
                required = '1) Detector' if workflow == 'detector.yml' else '3b) Structured decision'
                if not any(step.get('conclusion') == 'success' and step.get('name', '').startswith(required)
                           for job in jobs for step in job.get('steps', [])):
                    continue
            checked_runs.append(candidate)
        kind, run = diagnose(checked_runs, since, now)
        current_kind, current_run = diagnose(checked_runs, current_since, now)
        previous = old.get('last_failure') if old and not old.get('resolved') else None
        failures = [r for r in checked_runs if r.get('head_branch') == 'main' and
                    r.get('event') in {'schedule', 'workflow_dispatch'} and
                    r.get('status') == 'completed' and r.get('conclusion') != 'success' and
                    attempt_time(r) >= since]
        observed_failure = max(failures, key=attempt_order, default=None)
        if observed_failure and (not previous or
                attempt_order(observed_failure) > attempt_order(previous)):
            previous = observed_failure
        if previous and (kind == 'missing' or (kind in {'healthy', 'failed'} and
                attempt_order(run) <= attempt_order(previous))):
            kind, run = 'failed', previous
        if previous and old and not old.get('resolved'):
            old['last_failure'] = dict(previous)
        # Historical improvement does not satisfy a newer missing heartbeat.
        if kind == 'healthy' and current_kind != 'healthy':
            kind, run = current_kind, current_run
        if kind == 'healthy':
            assert run is not None  # diagnose only returns healthy with a verified run
            recovery = {'workflow': workflow, 'status': kind, 'current_status': current_kind,
                        'verification': 'verified_production', 'run_id': run['id'],
                        'run_attempt': run.get('run_attempt', 1), 'head_sha': run.get('head_sha'),
                        'attempt_started_at': attempt_time(run).isoformat(), 'verified_at': now.isoformat()}
            if old and not old.get('resolved'):
                if apply:
                    link = f"https://github.com/{REPO}/actions/runs/{run['id']}/attempts/{run.get('run_attempt', 1)}"
                    send(message=f'✅ AI Portföy — toparlanma doğrulandı\n{workflow}\nBaşarılı GitHub çalışması ve üretim adımı doğrulandı. Geçmiş yatırım kayıtlarına müdahale edilmedi.\n{link}')
                    old['resolved'] = now.isoformat()
                    old['recovery'] = recovery
            observations.append(recovery)
            continue
        if not old or old.get('resolved'):
            old = {'since': since.isoformat(), 'attempts': 0}
            state['incidents'][workflow] = old
        if previous:
            old['last_failure'] = dict(previous)
        jobs = fetch(f"actions/runs/{run['id']}/jobs")['jobs'] if kind == 'failed' else []
        plan = repair_plan(kind, run, jobs)
        eligible = workflow in due_windows(now)
        today = now.date().isoformat()
        cooldown = not old.get('last_attempt') or now - stamp(old['last_attempt']) >= timedelta(hours=2)
        can_repair = (plan and eligible and cooldown and old['attempts'] < 2
                      and state['daily_repairs'].get(today, 0) < 4)
        if kind in {'running', 'stuck'}:
            reason = 'production_running' if kind == 'running' else 'production_stuck'
        elif not eligible:
            reason = 'outside_due_window'
        elif not plan:
            reason = 'historical_rerun_disabled' if os.environ.get('PORTFOLIO_EXECUTOR') == 'local-hermes' else 'unsafe_failure'
        elif old['attempts'] >= 2:
            reason = 'incident_attempt_limit'
        elif state['daily_repairs'].get(today, 0) >= 4:
            reason = 'daily_attempt_limit'
        elif not cooldown:
            reason = 'repair_cooldown'
        else:
            reason = 'repair_eligible'
        observation = {'workflow': workflow, 'status': kind, 'current_status': current_kind,
            'run_created_at': run.get('created_at') if run else None, 'run_id': run.get('id') if run else None, 'run_attempt': run.get('run_attempt', 1) if run else None,
            'since': old['since'], 'due_since': current_since.isoformat() if eligible else None,
            'repair_eligible': bool(can_repair), 'reason': reason, 'verification': 'pending_production'}
        if kind == 'stuck':
            identities = {(r['id'], r.get('run_attempt', 1)) for r in overdue_runs(checked_runs, now)}
            observation['overdue_runs'] = [{'run_id': identity, 'run_attempt': attempt}
                                         for identity, attempt in sorted(identities)]
        # Intraday since slides every minute; its session/phase is the alert window.
        # Preserve the exact deadline for diagnostics without generating minute-by-minute alerts.
        fingerprint = dict(observation)
        if eligible and workflow == 'detector.yml':
            phase = 'close' if (current_since.hour, current_since.minute) == (21, 15) else 'intraday'
            fingerprint['due_since'] = current_since.date().isoformat() + ':' + phase
        observation_id = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
        observation['observation_id'] = observation_id
        old['observation'] = observation
        observations.append(observation)
        acknowledgement = old.get('acknowledgement', {})
        acknowledged = acknowledgement.get('observation_id') == observation_id
        if apply and can_repair:
            # Save intent before dispatching: a crash or ambiguous API timeout must
            # not create an unlimited repair loop. main provides persistence hook.
            old['attempts'] += 1
            old['last_attempt'] = now.isoformat()
            state['daily_repairs'][today] = state['daily_repairs'].get(today, 0) + 1
            persist = state.get('_persist')
            if persist:
                persist()
            if plan == 'dispatch':
                inputs = {'full_review': 'true'} if workflow == 'detector.yml' and session(now.date()) and now >= session(now.date())[1] else {}
                fetch(f'actions/workflows/{workflow}/dispatches', 'POST', {'ref': 'main', 'inputs': inputs})
            else:
                fetch(f"actions/runs/{run['id']}/rerun-failed-jobs", 'POST')
            old['repair_requested'] = now.isoformat()
            send(message=f'🛠 AI Portföy — sınırlı otomatik onarım istendi\n{workflow}: {kind}\nİşlem: {plan}\nHenüz başarı doğrulanmadı; sonuç ayrıca bildirilecek.')
            old['alerted'] = now.isoformat()
            old['alerted_observation_id'] = observation_id
        elif apply and kind != 'running' and not acknowledged and old.get('alerted_observation_id') != observation_id:
            explanation = {
                'outside_due_window': 'Güvenli çalışma penceresi dışında; planlı üretim çalışması bekleniyor.',
                'historical_rerun_disabled': 'Eski çalışma yeniden oynatılamaz; yerel yürütücüde planlı üretim çalışması bekleniyor.',
                'unsafe_failure': 'Bu hata için güvenli otomatik tekrar tanımlı değil; inceleme gerekiyor.',
                'incident_attempt_limit': 'Bu olayın otomatik onarım deneme sınırına ulaşıldı.',
                'daily_attempt_limit': 'Günlük otomatik onarım deneme sınırına ulaşıldı.',
                'repair_cooldown': 'İki saatlik onarım bekleme süresi dolmadı.',
                'production_stuck': 'Üretim çalışması iki saati aştı; yürütücü incelemesi gerekiyor.',
                'repair_eligible': 'Sınırlı otomatik onarım için uygun.',
            }[reason]
            scope = 'Geçmiş olay açık' if not eligible and kind == 'failed' else 'Açık olay'
            link = (f"https://github.com/{REPO}/actions/runs/{run['id']}/attempts/{run.get('run_attempt', 1)}"
                    if run else f'https://github.com/{REPO}/actions')
            if kind == 'stuck':
                link = '\n'.join(f"run:{r['run_id']}:attempt:{r['run_attempt']} "
                                 f"https://github.com/{REPO}/actions/runs/{r['run_id']}/attempts/{r['run_attempt']}"
                                 for r in observation['overdue_runs'])
            send(message=f"🚨 AI Portföy — çalışma gözcüsü\n{workflow}: {kind}\n{scope}; başlangıç: {old['since']}.\nÜretim doğrulaması bekleniyor; çözülmüş sayılmadı.\n{explanation}\nOnarım kodu: {reason}; deneme sayısı: {old['attempts']}.\n{link}")
            old['alerted'] = now.isoformat()
            old['alerted_observation_id'] = observation_id
    state['last_check'] = now.isoformat()
    return observations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote-state', action='store_true', help='persist repair limits on the watchdog-state branch')
    parser.add_argument('--daily', action='store_true', help='evaluate the last daily deadline even if the runner is delayed')
    parser.add_argument('--github-alerts', action='store_true', help='send through the existing GitHub Telegram secret configuration')
    parser.add_argument('--apply', action='store_true', help='enable bounded repairs and Telegram alerts')
    parser.add_argument('--state', default=str(Path.home()/'.local/state/ai-portfolio/watchdog.json'))
    parser.add_argument('--ack-workflow', choices=['detector.yml', 'weekly.yml'])
    parser.add_argument('--ack-observation', help='exact observation_id from a prior check')
    parser.add_argument('--ack-evidence', help='run:ID:attempt:N; concrete evidence location and findings')
    parser.add_argument('--ack-operator', help='operator identity')
    args = parser.parse_args()
    ack_args = (args.ack_workflow, args.ack_observation, args.ack_evidence, args.ack_operator)
    if any(ack_args):
        if not all(ack_args) or args.remote_state or args.apply or not any(value == '--state' or value.startswith('--state=') for value in sys.argv):
            parser.error('Acknowledgement requires all --ack-* fields and explicit local --state; no --apply/--remote-state')
    def send_alert(**kwargs):
        if args.github_alerts:
            api('actions/workflows/failure-alert.yml/dispatches', 'POST',
                {'ref': 'main', 'inputs': {'message': kwargs['message'][:3500]}})
            print('Telegram delivery requested through GitHub; delivery is confirmed by the notification workflow')
        else:
            notify(**kwargs)
    path = Path(args.state)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + '.lock', 'w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another watchdog is running')
            return
        remote = RemoteState() if args.remote_state else None
        state = remote.state if remote else read_json(str(path), {})
        def persist():
            if remote:
                remote.save(state)
            else:
                write_json(str(path), {k: v for k, v in state.items() if k != '_persist'})
        if args.ack_workflow:
            acknowledge(state, *ack_args, datetime.now(timezone.utc))
            persist()
            print('Exact incident observation acknowledged; unresolved; no monitoring or external action')
            return
        if args.apply:
            state['_persist'] = persist
        try:
            print(json.dumps(monitor(datetime.now(timezone.utc), state, send=send_alert, apply=args.apply, daily=args.daily)))
            if args.apply:
                state.pop('api_failure_alerted', None)
                persist()
        except Exception:
            if args.apply and not state.get('api_failure_alerted'):
                send_alert(message='🚨 AI Portföy — bağımsız gözcü kontrolü başarısız\nGitHub veya bildirim servisine erişilemiyor. Otomatik onarım doğrulanamadı.')
                state['api_failure_alerted'] = True
                persist()
            raise RuntimeError('Watchdog check failed; inspect connectivity/authentication') from None


if __name__ == '__main__':
    main()
