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
            'GITHUB_RUN_ATTEMPT': '1', 'LOCAL_RUNNER_CHECKOUT_OUTCOME': 'success'}


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


def test_blocked_non_owner_finish_does_not_archive_or_change_prior_claim(tmp_path):
    guard = load_guard()
    guard.start(tmp_path, env())
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    with pytest.raises(RuntimeError, match='Unresolved'):
        guard.start(tmp_path, env('102'))
    assert guard.finish(tmp_path, env('102'), 'failure') == 'not-owned'
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    with pytest.raises(RuntimeError, match='ownership'):
        guard.finish(tmp_path, env('102'), 'success')


@pytest.mark.parametrize('outcome', ['failure', 'cancelled'])
def test_never_claimed_finish_without_active_is_noop(tmp_path, outcome):
    assert load_guard().finish(tmp_path, env(), outcome) == 'not-owned'
    assert not (tmp_path / '101.json').exists()


@pytest.mark.parametrize('key,value', [('GITHUB_SHA', 'other'), ('GITHUB_WORKFLOW', 'Intraday Detector')])
def test_finish_rejects_wrong_exact_identity(tmp_path, key, value):
    guard = load_guard()
    guard.start(tmp_path, env())
    workspace = tmp_path / 'checkout'; workspace.mkdir()
    with pytest.raises(RuntimeError, match='ownership'):
        guard.finish(tmp_path, {**env(), key: value, 'GITHUB_WORKSPACE': str(workspace)}, 'success')
    assert (tmp_path / 'active.json').exists()


@pytest.mark.parametrize('outcome', ['success', 'failure', 'cancelled'])
def test_terminal_claim_cannot_be_finalized_again(tmp_path, outcome):
    guard = load_guard()
    workspace = tmp_path / 'checkout'; workspace.mkdir()
    (workspace / 'portfolio.json').write_text('original')
    root = tmp_path / 'journal'
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace)}
    guard.start(root, context)
    guard.finish(root, context, 'failure')
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    (workspace / 'portfolio.json').write_text('different later data')
    with pytest.raises(RuntimeError, match='already finalized'):
        guard.finish(root, context, outcome)
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


@pytest.mark.parametrize('outcome', ['success', 'failure', 'cancelled'])
def test_terminal_claim_cannot_be_finished_again(tmp_path, outcome):
    guard = load_guard()
    workspace = tmp_path / 'checkout'; workspace.mkdir()
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace)}
    guard.start(tmp_path / 'journal', context)
    guard.finish(tmp_path / 'journal', context, 'failure')
    root = tmp_path / 'journal'
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    with pytest.raises(RuntimeError, match='already finalized'):
        guard.finish(root, context, outcome)
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


@pytest.mark.parametrize('checkout', ['failure', 'cancelled', 'unknown'])
def test_failed_checkout_snapshot_is_explicitly_unverified(tmp_path, checkout):
    import json
    guard = load_guard()
    workspace = tmp_path / 'checkout'; workspace.mkdir()
    (workspace / 'portfolio.json').write_text('prior checkout data')
    root = tmp_path / 'journal'
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace), 'LOCAL_RUNNER_CHECKOUT_OUTCOME': checkout}
    guard.start(root, context)
    guard.finish(root, context, 'failure')
    receipt = json.loads((root / '101.json').read_text())
    assert receipt['checkout_outcome'] == checkout
    assert receipt['workspace_provenance'] == 'unverified-checkout'
    assert receipt['archive'] == '101-unverified-workspace.tar.gz'
    assert (root / receipt['archive']).exists()
    assert not (root / '101-artifacts.tar.gz').exists()


@pytest.mark.parametrize('interrupted', ['receipt', 'archive'])
def test_interrupted_finalization_never_overwrites_existing_evidence(tmp_path, interrupted):
    import json
    guard = load_guard()
    root = tmp_path / 'journal'; workspace = tmp_path / 'checkout'; workspace.mkdir()
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace)}
    guard.start(root, context)
    if interrupted == 'receipt':
        record = json.loads((root / '101.json').read_text()); record['status'] = 'success'
        (root / '101.json').write_text(json.dumps(record))
    else:
        (root / '101-artifacts.tar.gz').write_bytes(b'original evidence')
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    with pytest.raises(RuntimeError, match='reconciliation'):
        guard.finish(root, context, 'success')
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


def test_success_release_syncs_directory_after_unlink(tmp_path, monkeypatch):
    import os
    import stat
    guard = load_guard()
    root = tmp_path / 'journal'; workspace = tmp_path / 'checkout'; workspace.mkdir()
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace)}
    guard.start(root, context)
    real_sync = guard.os.fsync
    synced = []
    def sync(fd):
        if not (root / 'active.json').exists() and stat.S_ISDIR(os.fstat(fd).st_mode):
            synced.append(True)
        real_sync(fd)
    monkeypatch.setattr(guard.os, 'fsync', sync)
    guard.finish(root, context, 'success')
    assert synced == [True]


def test_success_requires_verified_checkout(tmp_path):
    guard = load_guard()
    workspace = tmp_path / 'checkout'; workspace.mkdir()
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace), 'LOCAL_RUNNER_CHECKOUT_OUTCOME': 'failure'}
    guard.start(tmp_path / 'journal', context)
    with pytest.raises(RuntimeError, match='checkout'):
        guard.finish(tmp_path / 'journal', context, 'success')
    assert (tmp_path / 'journal/active.json').exists()


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
