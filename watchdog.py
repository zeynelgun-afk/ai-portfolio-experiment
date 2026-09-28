#!/usr/bin/env python3
"""Independent heartbeat and bounded repairs. Never edits investment data or code."""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

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


def diagnose(runs, since, now):
    active = [r for r in runs if r.get('head_branch') == 'main' and r['status'] in ACTIVE]
    if active:
        return ('stuck' if any(now - stamp(r['created_at']) > timedelta(hours=2) for r in active) else 'running'), active[0]
    relevant = [r for r in runs if r.get('head_branch') == 'main' and
                r.get('event') in {'schedule', 'workflow_dispatch'} and stamp(r['created_at']) >= since]
    if any(r['status'] in ACTIVE for r in relevant):
        running = [r for r in relevant if r['status'] in ACTIVE]
        if any(now - stamp(r['created_at']) > timedelta(hours=2) for r in running):
            return 'stuck', running[0]
        return 'running', running[0]
    if any(r.get('conclusion') == 'success' for r in relevant):
        return 'healthy', None
    failed = sorted(relevant, key=lambda r: r['created_at'], reverse=True)
    return ('failed', failed[0]) if failed else ('missing', None)


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


def monitor(now, state, fetch=api, send=notify, apply=False):
    state.setdefault('incidents', {})
    state.setdefault('daily_repairs', {})
    observations = []
    windows = due_windows(now)
    # Continue checking an existing incident after its schedule window, but never
    # perform an out-of-window catch-up trade.
    for workflow, incident in state['incidents'].items():
        if not incident.get('resolved'):
            windows.setdefault(workflow, stamp(incident['since']))
    for workflow, since in windows.items():
        runs = fetch(f'actions/workflows/{workflow}/runs?branch=main&per_page=100')['workflow_runs']
        # A green calendar-only skip is not a measurement heartbeat.
        checked_runs = []
        for candidate in runs:
            if candidate.get('conclusion') == 'success' and candidate.get('head_branch') == 'main' and stamp(candidate['created_at']) >= since:
                jobs = fetch(f"actions/runs/{candidate['id']}/jobs")['jobs']
                required = '1) Detector' if workflow == 'detector.yml' else '3b) Structured decision'
                if not any(step.get('conclusion') == 'success' and step.get('name', '').startswith(required)
                           for job in jobs for step in job.get('steps', [])):
                    continue
            checked_runs.append(candidate)
        kind, run = diagnose(checked_runs, since, now)
        observations.append({'workflow': workflow, 'status': kind})
        old = state['incidents'].get(workflow)
        if kind == 'healthy':
            if old and not old.get('resolved'):
                if apply:
                    send(message=f'✅ AI Portföy — toparlanma doğrulandı\n{workflow}\nBaşarılı GitHub çalışması görüldü. Geçmiş yatırım kayıtlarına müdahale edilmedi.')
                    old['resolved'] = now.isoformat()
            continue
        if kind == 'running':
            continue
        if not old or old.get('resolved'):
            old = {'since': since.isoformat(), 'attempts': 0}
            state['incidents'][workflow] = old
        jobs = fetch(f"actions/runs/{run['id']}/jobs")['jobs'] if kind == 'failed' else []
        plan = repair_plan(kind, run, jobs)
        eligible = workflow in due_windows(now)
        today = now.date().isoformat()
        cooldown = not old.get('last_attempt') or now - stamp(old['last_attempt']) >= timedelta(hours=2)
        can_repair = (plan and eligible and cooldown and old['attempts'] < 2
                      and state['daily_repairs'].get(today, 0) < 4)
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
        elif apply and (not old.get('alerted') or now - stamp(old['alerted']) >= timedelta(hours=12)):
            send(message=f'🚨 AI Portföy — çalışma gözcüsü\n{workflow}: {kind}\nGüvenli otomatik onarım uygulanamadı veya deneme sınırına ulaşıldı. İnceleme gerekiyor.\nhttps://github.com/{REPO}/actions')
            old['alerted'] = now.isoformat()
    state['last_check'] = now.isoformat()
    return observations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--github-alerts', action='store_true', help='send through the existing GitHub Telegram secret configuration')
    parser.add_argument('--apply', action='store_true', help='enable bounded repairs and Telegram alerts')
    parser.add_argument('--state', default=str(Path.home()/'.local/state/ai-portfolio/watchdog.json'))
    args = parser.parse_args()
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
        state = read_json(str(path), {})
        def persist():
            write_json(str(path), {k: v for k, v in state.items() if k != '_persist'})
        if args.apply:
            state['_persist'] = persist
        try:
            print(json.dumps(monitor(datetime.now(timezone.utc), state, send=send_alert, apply=args.apply)))
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
