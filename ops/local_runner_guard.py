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
import hashlib
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
        attempt = json.loads(active.read_text()) if active.exists() else {}
        expected = {'run_id': env['GITHUB_RUN_ID'], 'attempt': env['GITHUB_RUN_ATTEMPT'],
                    'workflow': env['GITHUB_WORKFLOW'], 'sha': env.get('GITHUB_SHA')}
        if not attempt or any(attempt.get(key) != value for key, value in expected.items()):
            # A rejected setup never owned this workspace. Keep the primary job
            # failure, without archiving stale data or touching another claim.
            if outcome != 'success' and not (root / (env['GITHUB_RUN_ID'] + '.json')).exists():
                return 'not-owned'
            raise RuntimeError('Attempt ownership mismatch')
        if attempt.get('status') != 'started':
            raise RuntimeError('Attempt already finalized; reconciliation required')
        receipt = root / (env['GITHUB_RUN_ID'] + '.json')
        if not receipt.exists() or json.loads(receipt.read_text()) != attempt:
            raise RuntimeError('Interrupted receipt; reconciliation required')
        if any((root / (env['GITHUB_RUN_ID'] + suffix)).exists()
               for suffix in ('-artifacts.tar.gz', '-unverified-workspace.tar.gz')):
            raise RuntimeError('Existing evidence; reconciliation required')
        # Save exact partial results before a future checkout can clean workspace.
        workspace_value = env.get('GITHUB_WORKSPACE')
        if not workspace_value:
            raise RuntimeError('Missing workspace')
        workspace = Path(workspace_value)
        if not workspace.is_dir():
            raise RuntimeError('Workspace is not an existing directory')
        checkout = env.get('LOCAL_RUNNER_CHECKOUT_OUTCOME', 'unknown')
        verified_checkout = checkout == 'success'
        if outcome == 'success' and not verified_checkout:
            raise RuntimeError('Successful checkout required for successful release')
        archive = root / (env['GITHUB_RUN_ID'] + (
            '-artifacts.tar.gz' if verified_checkout else '-unverified-workspace.tar.gz'))
        attempt.update(checkout_outcome=checkout, archive=archive.name,
                       workspace_provenance='current-checkout' if verified_checkout else 'unverified-checkout')
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
            fd = os.open(root, os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        else:
            atomic_json(active, attempt)


def reconcile(root, expected, audit):
    """Operator-only release after private evidence review; never mark success."""
    with locked(root) as root:
        active = root / 'active.json'
        attempt = json.loads(active.read_text())
        if attempt != expected or attempt.get('status') not in {'failure', 'cancelled'} or not attempt.get('finished_at'):
            raise RuntimeError('Exact finished attempt required')
        run_id = attempt.get('run_id', '')
        if not isinstance(run_id, str) or not run_id.isascii() or not run_id.isdigit():
            raise RuntimeError('Invalid run identity')
        receipt = root / (run_id + '.json')
        archive_name = attempt.get('archive', run_id + '-artifacts.tar.gz')
        if archive_name not in {run_id + '-artifacts.tar.gz', run_id + '-unverified-workspace.tar.gz'}:
            raise RuntimeError('Invalid archive identity')
        archive = root / archive_name
        record = root / (run_id + '-reconciliation.json')
        if record.exists():
            raise RuntimeError('Existing reconciliation requires manual inspection')
        if json.loads(receipt.read_text()) != attempt:
            raise RuntimeError('Receipt identity mismatch')
        if (hashlib.sha256(receipt.read_bytes()).hexdigest() != audit.get('receipt_sha256')
                or hashlib.sha256(archive.read_bytes()).hexdigest() != audit.get('archive_sha256')):
            raise RuntimeError('Receipt or archive digest mismatch')
        checks = audit.get('checks', {})
        evidence_items = audit.get('evidence')
        if (audit.get('resolution') != 'persisted-no-replay'
                or not isinstance(audit.get('reason'), str) or not audit['reason'].strip()
                or not isinstance(checks, dict)
                or any(not isinstance(checks.get(key), str) or not checks[key].strip()
                       for key in ('commit', 'trades', 'pending', 'notifications'))
                or not isinstance(evidence_items, list) or not evidence_items
                or any(not isinstance(item, dict)
                       or not isinstance(item.get('path'), str) or not item['path'].strip()
                       or not isinstance(item.get('sha256'), str)
                       for item in evidence_items)):
            raise RuntimeError('Complete operator evidence review required')
        for evidence in audit['evidence']:
            if hashlib.sha256(Path(evidence['path']).read_bytes()).hexdigest() != evidence['sha256']:
                raise RuntimeError('Evidence digest mismatch')
        atomic_json(record,
                    {'attempt': attempt, 'audit': audit,
                     'reconciled_at': datetime.now(timezone.utc).isoformat()})
        active.unlink()
        fd = os.open(root, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['start', 'finish', 'plan', 'reconcile'])
    parser.add_argument('--expected', type=Path, help='Exact reviewed active record (operator only)')
    parser.add_argument('--audit', type=Path, help='Private evidence manifest (operator only)')
    parser.add_argument('--outcome', choices=['success', 'failure', 'cancelled'])
    parser.add_argument('--state', default=str(Path.home()/'.local/state/ai-portfolio-runner'))
    args = parser.parse_args()
    if args.command == 'plan':
        print(json.dumps({'repository': REPOSITORY, 'workflows': sorted(WORKFLOWS),
                          'paid_fallback': False, 'state': args.state}))
        return
    if args.command == 'reconcile':
        if not args.expected or not args.audit:
            parser.error('reconcile requires --expected and --audit; stop listener and verify idle first')
        reconcile(args.state, json.loads(args.expected.read_text()), json.loads(args.audit.read_text()))
        return
    if args.command == 'start':
        start(args.state, os.environ)
    else:
        finish(args.state, os.environ, args.outcome)


if __name__ == '__main__':
    main()
