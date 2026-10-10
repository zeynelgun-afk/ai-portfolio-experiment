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
import subprocess
import secrets
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
        # Bind only this installed pre-job hook's file-command output to its
        # private owner record. Runner-generated context names are random GUIDs;
        # their shape alone is not evidence that an unknown step is this hook.
        if env.get('GITHUB_OUTPUT'):
            attempt['hook_claim'] = secrets.token_hex(32)
        atomic_json(root / 'active.json', attempt)
        atomic_json(receipt, attempt)
        if 'hook_claim' in attempt:
            with open(env['GITHUB_OUTPUT'], 'a') as handle:
                handle.write('local_runner_claim=' + attempt['hook_claim'] + '\n')
                handle.flush()
                os.fsync(handle.fileno())


# A deliberately closed contract: unknown/new workflow steps cannot auto-release.
PARTIAL_STEP_IDS = set('checkout baseline dependencies mode session corporate corporate_commit corporate_notify weekly_execution weekly_commit weekly_notify weekly_evidence detector reassess intraday_evidence trade refresh prompt_adapt research_metrics commit decision_notify daily_notify assessment_summary reassessment_health news_health prompt_health provider_health provider_evidence'.split())
WEEKLY_PARTIAL_STEP_IDS = set('checkout baseline dependencies corporate corporate_commit corporate_notify valuation valuation_commit valuation_evidence audit audit_notify research_metrics prompt_adapt scout weekly_inputs weekly_decision weekly_evidence refresh commit plan_notify amend proposal_evidence amend_commit exit_notify report_notify audit_reminder prompt_health provider_health analyst_health provider_evidence'.split())


def checkout_git(workspace, *args):
    return subprocess.check_output(['git', '-C', str(workspace), *args],
        stderr=subprocess.DEVNULL, timeout=30,
        env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})


def checkpoint_checkout(root, env):
    """Bind actual checkout baseline before application steps, never event SHA."""
    validate_context(env)
    with locked(root) as root:
        active = root / 'active.json'
        attempt = json.loads(active.read_text())
        receipt = root / (env['GITHUB_RUN_ID'] + '.json')
        expected = {'run_id': env['GITHUB_RUN_ID'], 'attempt': env['GITHUB_RUN_ATTEMPT'],
                    'workflow': env['GITHUB_WORKFLOW'], 'sha': env.get('GITHUB_SHA')}
        if (any(attempt.get(k) != v for k, v in expected.items())
                or attempt.get('status') != 'started' or 'checkout_sha' in attempt
                or json.loads(receipt.read_text()) != attempt
                or env.get('LOCAL_RUNNER_CHECKOUT_OUTCOME') != 'success'):
            raise RuntimeError('Exact uncheckpointed checkout owner required')
        workspace = Path(env['GITHUB_WORKSPACE'])
        if checkout_git(workspace, 'status', '--porcelain', '--untracked-files=all').strip():
            raise RuntimeError('Clean checkout baseline required')
        attempt['checkout_sha'] = checkout_git(workspace, 'rev-parse', 'HEAD').decode().strip()
        atomic_json(receipt, attempt)
        atomic_json(active, attempt)


def persisted_no_trade_partial(env, outcome, workspace, attempt):
    """Prove a known health-only failure has no unresolved financial side effect.

    Never used for historical reconciliation. Any missing evidence/network error
    leaves the ordinary failure claim locked for operator review.
    """
    if (outcome != 'failure' or env.get('GITHUB_WORKFLOW') != 'Intraday Detector'
            or env.get('LOCAL_RUNNER_CHECKOUT_OUTCOME') != 'success'):
        return None
    try:
        steps = json.loads(env.get('LOCAL_RUNNER_STEPS', '{}'))
        if not isinstance(steps, dict):
            return None
        allowed = PARTIAL_STEP_IDS.copy()
        claim = attempt.get('hook_claim')
        if (not isinstance(claim, str) or len(claim) != 64
                or any(c not in '0123456789abcdef' for c in claim)):
            return None
        hooks = [key for key, step in steps.items()
                 if key not in PARTIAL_STEP_IDS and step == {
                     'outputs': {'local_runner_claim': claim},
                     'outcome': 'success', 'conclusion': 'success'}]
        if len(hooks) != 1:
            return None
        hook = hooks[0]
        if len(hook) != 32 or any(c not in '0123456789abcdef' for c in hook):
            return None
        allowed.add(hook)
        if set(steps) != allowed:
            return None
        failed = set()
        for key, step in steps.items():
            if (not isinstance(step, dict) or step.get('outcome') != step.get('conclusion')
                    or step.get('outcome') not in {'success', 'failure', 'skipped'}):
                return None
            if step['outcome'] == 'failure':
                failed.add(key)
        if not failed or not failed <= {'news_health', 'reassessment_health'}:
            return None
        for key in ('checkout', 'baseline', 'dependencies', 'mode', 'session', 'corporate',
                    'weekly_execution', 'detector', 'commit', 'assessment_summary',
                    'weekly_evidence', 'intraday_evidence', 'provider_health', 'provider_evidence'):
            if steps[key]['outcome'] != 'success':
                return None
        def output(key, field):
            return steps[key].get('outputs', {}).get(field)
        if (output('session', 'run') != 'true'
                or output('corporate', 'changed') != 'false'
                or output('weekly_execution', 'executed') not in {None, '', 'false'}
                or output('commit', 'changed') != 'true'
                or output('detector', 'code') not in {'0', '10', '20'}):
            return None
        if steps['trade']['outcome'] == 'success':
            if output('trade', 'trade_count') != '0':
                return None
        elif steps['trade']['outcome'] != 'skipped':
            return None
        if (workspace / 'state').is_symlink():
            return None
        for name in ('state/violations.json', 'portfolio.json'):
            path = workspace / name
            if (path.is_symlink() or not path.is_file()
                    or path.read_bytes() != checkout_git(workspace, 'show', 'HEAD:' + name)):
                return None
        state = json.loads((workspace / 'state/violations.json').read_text())
        if not isinstance(state, dict):
            return None
        if 'news_health' in failed and not (state.get('news_errors') or state.get('measurement_errors')):
            return None
        if 'reassessment_health' in failed and not state.get('assessment_errors'):
            return None
        if any((workspace / 'state' / name).exists() for name in
               ('pending_decision.json', 'weekly_transaction.json')):
            return None
        plan_path = workspace / 'state/weekly_plan.json'
        if plan_path.exists() and json.loads(plan_path.read_text()).get('status') == 'pending':
            return None
        # Successful git push alone is not readback. Compare exact remote HEAD,
        # and ensure neither tracked nor untracked durable changes were lost.
        def git(*args):
            return checkout_git(workspace, *args).decode().strip()
        if git('status', '--porcelain', '--untracked-files=all'):
            return None
        head = git('rev-parse', 'HEAD')
        remote = git('ls-remote', '--exit-code', 'origin', 'refs/heads/main').split()
        if remote != [head, 'refs/heads/main']:
            return None
        start_sha = attempt.get('checkout_sha', '')
        if len(start_sha) != 40 or any(c not in '0123456789abcdef' for c in start_sha):
            return None
        # Even a misleading/missing execution output cannot hide portfolio changes.
        if git('diff', start_sha, head, '--', 'portfolio.json'):
            return None
        return {'head': head, 'remote_head': remote[0], 'steps': steps}
    except (ValueError, TypeError, AttributeError, OSError, subprocess.SubprocessError):
        return None


def persisted_weekly_research_partial(env, outcome, workspace, attempt):
    """A fully persisted weekend plan with data gaps must not freeze next session.

    Only a source-health failure qualifies. Failed models, persistence/delivery,
    changed accounting/live theses or ambiguous execution still require review.
    The job stays failed and its original run can never be replayed.
    """
    if (outcome != 'failure' or env.get('GITHUB_WORKFLOW') != 'Weekly Portfolio Round'
            or env.get('LOCAL_RUNNER_CHECKOUT_OUTCOME') != 'success'):
        return None
    try:
        steps = json.loads(env.get('LOCAL_RUNNER_STEPS', '{}'))
        claim = attempt.get('hook_claim')
        if not isinstance(steps, dict) or not isinstance(claim, str) or len(claim) != 64:
            return None
        hooks = [key for key, value in steps.items() if key not in WEEKLY_PARTIAL_STEP_IDS
                 and value == {'outputs': {'local_runner_claim': claim},
                               'outcome': 'success', 'conclusion': 'success'}]
        if (len(hooks) != 1 or len(hooks[0]) != 32
                or any(c not in '0123456789abcdef' for c in hooks[0] + claim)
                or set(steps) != WEEKLY_PARTIAL_STEP_IDS | set(hooks)):
            return None
        optional = {'corporate_commit', 'corporate_notify', 'exit_notify', 'prompt_health'}
        for key, step in steps.items():
            expected = 'failure' if key == 'analyst_health' else 'success'
            if key in optional:
                expected = 'skipped'
            if (not isinstance(step, dict) or step.get('outcome') != expected
                    or step.get('conclusion') != expected):
                return None
        if steps['corporate'].get('outputs', {}).get('changed') != 'false':
            return None
        def git(*args):
            return checkout_git(workspace, *args).decode().strip()
        if (workspace / 'state').is_symlink() or git('status', '--porcelain', '--untracked-files=all'):
            return None
        start_sha = attempt.get('checkout_sha', '')
        if len(start_sha) != 40 or any(c not in '0123456789abcdef' for c in start_sha):
            return None
        head = git('rev-parse', 'HEAD')
        remote = git('ls-remote', '--exit-code', 'origin', 'refs/heads/main').split()
        if remote != [head, 'refs/heads/main']:
            return None
        for name in ('portfolio.json', 'theses.json', 'weekly_data.json', 'state/weekly_plan.json'):
            path = workspace / name
            if (path.is_symlink() or not path.is_file()
                    or path.read_bytes() != checkout_git(workspace, 'show', 'HEAD:' + name)):
                return None
        before = json.loads(git('show', start_sha + ':portfolio.json'))
        after = json.loads((workspace / 'portfolio.json').read_text())
        if not isinstance(before, dict) or not isinstance(after, dict):
            return None
        before.pop('last_updated', None)
        after.pop('last_updated', None)
        if before != after or git('diff', start_sha, head, '--', 'theses.json', 'DECISION_LOG.md'):
            return None
        if any((workspace / 'state' / name).exists() for name in
               ('pending_decision.json', 'weekly_transaction.json')):
            return None
        plan = json.loads((workspace / 'state/weekly_plan.json').read_text())
        if (not isinstance(plan, dict) or plan.get('status') != 'pending'
                or not isinstance(plan.get('proposal'), dict)
                or datetime.fromisoformat(plan['created_at']) < datetime.fromisoformat(attempt['started_at'])):
            return None
        data = json.loads((workspace / 'weekly_data.json').read_text())
        gaps = [symbol for symbol, row in data.items() if not symbol.startswith('_')
                and (row.get('analyst_revisions', {}).get('status') != 'ok'
                     or row.get('analyst_revisions', {}).get('estimates_status') != 'ok')]
        if not gaps:
            return None
        return {'head': head, 'remote_head': remote[0], 'steps': steps,
                'pending_plan': plan.get('round_id'), 'source_gaps': gaps}
    except (ValueError, TypeError, AttributeError, KeyError, OSError, subprocess.SubprocessError):
        return None


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
        partial = persisted_no_trade_partial(env, outcome, workspace, attempt)
        weekly_partial = persisted_weekly_research_partial(env, outcome, workspace, attempt)
        if partial:
            attempt.update(release_reason='persisted-no-trade-partial', partial_evidence=partial)
        elif weekly_partial:
            attempt.update(release_reason='persisted-weekly-research-partial', partial_evidence=weekly_partial)
        attempt.update(status=outcome, finished_at=datetime.now(timezone.utc).isoformat())
        atomic_json(root / (env['GITHUB_RUN_ID'] + '.json'), attempt)
        if outcome == 'success' or partial or weekly_partial:
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
    parser.add_argument('command', choices=['start', 'checkout', 'finish', 'plan', 'reconcile'])
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
    elif args.command == 'checkout':
        checkpoint_checkout(args.state, os.environ)
    else:
        finish(args.state, os.environ, args.outcome)


if __name__ == '__main__':
    main()
