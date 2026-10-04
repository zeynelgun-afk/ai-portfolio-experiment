"""Local runner guard tests: persistent claims and lazy/no-network planning."""
import importlib.util
from pathlib import Path
import pytest


def load_guard():
    path = Path(__file__).resolve().parents[1] / 'ops/local_runner_guard.py'
    spec = importlib.util.spec_from_file_location('guard', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def env(run='101'):
    return {'GITHUB_REPOSITORY': 'zeynelgun-afk/ai-portfolio-experiment',
            'GITHUB_REF': 'refs/heads/main', 'GITHUB_EVENT_NAME': 'workflow_dispatch',
            'GITHUB_WORKFLOW': 'Local Hermes Smoke', 'GITHUB_RUN_ID': run,
            'GITHUB_RUN_ATTEMPT': '1'}


def test_claim_survives_process_restart_and_rejects_overlap(tmp_path):
    guard = load_guard()
    guard.start(tmp_path, env())
    with pytest.raises(RuntimeError, match='Unresolved'):
        load_guard().start(tmp_path, env('102'))
    workspace = tmp_path/'checkout'; workspace.mkdir()
    guard.finish(tmp_path, {**env(), 'GITHUB_WORKSPACE': str(workspace)}, 'success')
    guard.start(tmp_path, env('102'))


def test_successful_run_cannot_be_replayed(tmp_path):
    guard = load_guard()
    guard.start(tmp_path, env())
    workspace = tmp_path/'checkout'; workspace.mkdir()
    guard.finish(tmp_path, {**env(), 'GITHUB_WORKSPACE': str(workspace)}, 'success')
    with pytest.raises(RuntimeError, match='already'):
        guard.start(tmp_path, env())


def test_failed_run_requires_manual_reconciliation(tmp_path):
    guard = load_guard()
    guard.start(tmp_path, env())
    workspace = tmp_path/'checkout'; workspace.mkdir()
    guard.finish(tmp_path, {**env(), 'GITHUB_WORKSPACE': str(workspace)}, 'failure')
    with pytest.raises(RuntimeError, match='Unresolved'):
        guard.start(tmp_path, env('102'))


@pytest.mark.parametrize('key,value', [('GITHUB_REF','refs/pull/1/merge'),
    ('GITHUB_EVENT_NAME','pull_request_target'), ('GITHUB_REPOSITORY','attacker/fork'),
    ('GITHUB_WORKFLOW','unknown')])
def test_only_approved_main_jobs_are_allowed(tmp_path, key, value):
    guard = load_guard()
    context = env(); context[key] = value
    with pytest.raises(RuntimeError):
        guard.start(tmp_path, context)
    assert not (tmp_path/'active.json').exists()


def test_watchdog_never_replays_legacy_hosted_jobs(monkeypatch):
    import watchdog
    monkeypatch.setenv('PORTFOLIO_EXECUTOR', 'local-hermes')
    run = {'conclusion': 'failure'}
    jobs = [{'steps': [{'name': 'Dependencies', 'conclusion': 'failure'}]}]
    assert watchdog.repair_plan('failed', run, jobs) is None
    assert watchdog.repair_plan('missing', None, []) == 'dispatch'


def test_two_real_processes_cannot_both_claim(tmp_path):
    import os
    import subprocess
    import sys
    script = str(Path(__file__).resolve().parents[1] / 'ops/local_runner_guard.py')
    command = [sys.executable, script, 'start', '--state', str(tmp_path)]
    children = [subprocess.Popen(command, env={**os.environ, **env(str(run))},
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for run in (201, 202)]
    statuses = []
    for child in children:
        child.communicate(timeout=10)
        statuses.append(child.returncode)
    assert sorted(statuses) == [0, 1]


def test_success_without_workspace_is_rejected(tmp_path):
    guard = load_guard()
    guard.start(tmp_path, env())
    with pytest.raises(RuntimeError, match='workspace'):
        guard.finish(tmp_path, env(), 'success')
    assert (tmp_path/'active.json').exists()


def test_archive_sync_failure_retains_unresolved_claim(tmp_path, monkeypatch):
    guard = load_guard()
    workspace = tmp_path/'checkout'; workspace.mkdir()
    (workspace/'portfolio.json').write_text('{}')
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace)}
    state = tmp_path/'journal'
    guard.start(state, context)
    def failed_sync(fd):
        raise OSError('simulated storage failure')
    monkeypatch.setattr(guard.os, 'fsync', failed_sync)
    with pytest.raises(OSError):
        guard.finish(state, context, 'success')
    assert not (state/'101-artifacts.tar.gz').exists()
    assert (state/'active.json').exists()


def test_finish_preserves_private_partial_artifacts(tmp_path):
    import tarfile
    guard = load_guard()
    workspace = tmp_path/'checkout'; workspace.mkdir()
    (workspace/'portfolio.json').write_text('{"paper":true}')
    (workspace/'.env').write_text('SECRET=never archive')
    state = tmp_path/'journal'
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace)}
    guard.start(state, context)
    guard.finish(state, context, 'failure')
    with tarfile.open(state/'101-artifacts.tar.gz') as archive:
        assert archive.getnames() == ['portfolio.json']
        assert archive.extractfile('portfolio.json').read() == b'{"paper":true}'
