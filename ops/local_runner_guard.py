#!/usr/bin/env python3
"""Installed outside checkout as the Actions runner's pre-job safety hook.

The listener itself must run under flock; this journal also blocks sequential
replay and requires explicit reconciliation after interrupted/failed work.
No dotenv, application modules, credentials or network are loaded here.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import tarfile

REPOSITORY = 'zeynelgun-afk/ai-portfolio-experiment'
WORKFLOWS = {'Weekly Portfolio Round', 'Intraday Detector', 'Local Hermes Smoke'}


def validate_context(env):
    if (env.get('GITHUB_REPOSITORY') != REPOSITORY
            or env.get('GITHUB_REF') != 'refs/heads/main'
            or env.get('GITHUB_EVENT_NAME') not in {'schedule', 'workflow_dispatch'}
            or env.get('GITHUB_WORKFLOW') not in WORKFLOWS
            or not env.get('GITHUB_RUN_ID', '').isdigit()
            or not env.get('GITHUB_RUN_ATTEMPT', '').isdigit()):
        raise RuntimeError('Unapproved local runner context')


@contextmanager
def locked(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / 'journal.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield root


def atomic_json(path, data):
    tmp = path.with_suffix('.tmp')
    with tmp.open('w') as handle:
        json.dump(data, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def start(root, env):
    validate_context(env)
    with locked(root) as root:
        if (root / 'active.json').exists():
            raise RuntimeError('Unresolved prior attempt: reconcile private evidence before retry')
        receipt = root / (env['GITHUB_RUN_ID'] + '.json')
        if receipt.exists():
            raise RuntimeError('Run already attempted; automatic replay forbidden')
        attempt = {'run_id': env['GITHUB_RUN_ID'], 'attempt': env['GITHUB_RUN_ATTEMPT'],
                   'workflow': env['GITHUB_WORKFLOW'], 'sha': env.get('GITHUB_SHA'),
                   'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'started'}
        atomic_json(root / 'active.json', attempt)
        atomic_json(receipt, attempt)


def finish(root, env, outcome):
    validate_context(env)
    if outcome not in {'success', 'failure', 'cancelled'}:
        raise RuntimeError('Unknown job outcome')
    with locked(root) as root:
        active = root / 'active.json'
        attempt = json.loads(active.read_text())
        if attempt['run_id'] != env['GITHUB_RUN_ID'] or attempt['attempt'] != env['GITHUB_RUN_ATTEMPT']:
            raise RuntimeError('Attempt ownership mismatch')
        # Save exact partial results before a future checkout can clean workspace.
        workspace_value = env.get('GITHUB_WORKSPACE')
        if not workspace_value:
            raise RuntimeError('Missing workspace')
        workspace = Path(workspace_value)
        if not workspace.is_dir():
            raise RuntimeError('Workspace is not an existing directory')
        archive = root / (env['GITHUB_RUN_ID'] + '-artifacts.tar.gz')
        tmp = archive.with_suffix('.tmp')
        with tmp.open('wb') as handle:
            with tarfile.open(fileobj=handle, mode='w:gz') as tar:
                paths = [*workspace.glob('*.json'), *workspace.glob('*.md'),
                         workspace / 'state', workspace / 'output']
                for path in paths:
                    if path.exists() and not path.is_symlink():
                        tar.add(path, arcname=path.name, filter=lambda info: None if info.issym() or info.islnk() else info)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(archive)
        fd = os.open(root, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        attempt.update(status=outcome, finished_at=datetime.now(timezone.utc).isoformat())
        atomic_json(root / (env['GITHUB_RUN_ID'] + '.json'), attempt)
        if outcome == 'success':
            active.unlink()
        else:
            atomic_json(active, attempt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['start', 'finish', 'plan'])
    parser.add_argument('--outcome', choices=['success', 'failure', 'cancelled'])
    parser.add_argument('--state', default=str(Path.home()/'.local/state/ai-portfolio-runner'))
    args = parser.parse_args()
    if args.command == 'plan':
        print(json.dumps({'repository': REPOSITORY, 'workflows': sorted(WORKFLOWS),
                          'paid_fallback': False, 'state': args.state}))
        return
    if args.command == 'start':
        start(args.state, os.environ)
    else:
        finish(args.state, os.environ, args.outcome)


if __name__ == '__main__':
    main()
