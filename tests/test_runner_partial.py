"""Completed, persisted no-trade partial assessments must not freeze future runs."""
import json
import subprocess
from pathlib import Path
import pytest
from tests.test_local_runner import load_guard, env

# Explicit contract: adding/removing a workflow step requires safety review.
STEP_IDS = set('checkout baseline dependencies mode session corporate corporate_commit corporate_notify weekly_execution weekly_commit weekly_notify weekly_evidence detector reassess intraday_evidence trade refresh prompt_adapt research_metrics commit decision_notify daily_notify assessment_summary reassessment_health news_health prompt_health provider_health provider_evidence'.split())


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def fixture(tmp_path, event_sha=None, workflow='Intraday Detector'):
    workspace = tmp_path / 'checkout'; workspace.mkdir()
    remote = tmp_path / 'remote.git'
    subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    git(workspace, 'init', '-b', 'main')
    git(workspace, 'config', 'user.name', 'Test')
    git(workspace, 'config', 'user.email', 'test@example.invalid')
    (workspace / 'portfolio.json').write_text('{}')
    (workspace / 'state').mkdir()
    (workspace / 'state/violations.json').write_text('{}')
    git(workspace, 'add', '.'); git(workspace, 'commit', '-m', 'initial')
    sha = git(workspace, 'rev-parse', 'HEAD')
    git(workspace, 'remote', 'add', 'origin', str(remote))
    guard, root = load_guard(), tmp_path / 'journal'
    context = {**env(), 'GITHUB_WORKFLOW': workflow, 'GITHUB_SHA': event_sha or sha,
               'GITHUB_WORKSPACE': str(workspace)}
    guard.start(root, context)
    guard.checkpoint_checkout(root, context)
    (workspace / 'state/violations.json').write_text('{"news_errors":[{"symbol":"AMD","error":"source unavailable"}]}')
    git(workspace, 'add', '.'); git(workspace, 'commit', '-m', 'persist partial evidence')
    git(workspace, 'push', 'origin', 'main')
    steps = {key: {'outcome': 'success', 'conclusion': 'success', 'outputs': {}} for key in STEP_IDS}
    steps['news_health'].update(outcome='failure', conclusion='failure')
    steps['reassessment_health'].update(outcome='skipped', conclusion='skipped')
    steps['prompt_health'].update(outcome='skipped', conclusion='skipped')
    steps['checkout']['outputs'] = {'commit': sha}
    steps['session']['outputs'] = {'run': 'true'}
    steps['detector']['outputs'] = {'code': '20', 'news_error_count': '1', 'measurement_error_count': '0'}
    steps['corporate']['outputs'] = {'changed': 'false'}
    steps['weekly_execution']['outputs'] = {'executed': 'false'}
    steps['trade']['outputs'] = {'trade_count': '0'}
    steps['commit']['outputs'] = {'changed': 'true'}
    context['LOCAL_RUNNER_STEPS'] = json.dumps(steps)
    return guard, root, context, steps, workspace


def test_persisted_no_trade_partial_releases_only_future_runs(tmp_path):
    guard, root, context, steps, workspace = fixture(tmp_path)
    guard.finish(root, context, 'failure')
    receipt = json.loads((root / '101.json').read_text())
    assert receipt['status'] == 'failure'
    assert receipt['release_reason'] == 'persisted-no-trade-partial'
    assert receipt['partial_evidence']['head'] == git(workspace, 'rev-parse', 'HEAD')
    assert receipt['partial_evidence']['steps'] == steps
    assert (root / '101-artifacts.tar.gz').exists()
    assert not (root / 'active.json').exists()
    with pytest.raises(RuntimeError, match='already'):
        guard.start(root, {**context, 'GITHUB_RUN_ATTEMPT': '2'})
    guard.start(root, {**context, 'GITHUB_RUN_ID': '102'})


def test_no_pending_weekly_plan_emits_no_execution_output(tmp_path):
    guard, root, context, steps, workspace = fixture(tmp_path)
    steps['weekly_execution']['outputs'] = {}
    context['LOCAL_RUNNER_STEPS'] = json.dumps(steps)
    guard.finish(root, context, 'failure')
    assert not (root / 'active.json').exists()


@pytest.mark.parametrize('mutation', ['missing_steps', 'unknown_step', 'notification_failure',
    'commit_failure', 'detector_failure', 'artifact_failure', 'cancelled_step',
    'continue_on_error', 'trade', 'corporate', 'weekly', 'dirty', 'untracked',
    'unpushed', 'portfolio_changed', 'remote_unavailable', 'wrong_workflow', 'cancelled_job'])
def test_ambiguous_or_financial_failure_still_requires_reconciliation(tmp_path, mutation):
    guard, root, context, steps, workspace = fixture(tmp_path,
        workflow='Weekly Portfolio Round' if mutation == 'wrong_workflow' else 'Intraday Detector')
    outcome = 'failure'
    if mutation == 'missing_steps': steps.pop('decision_notify')
    elif mutation == 'unknown_step': steps['new_effect'] = steps['commit'].copy()
    elif mutation.endswith('_failure'):
        key = {'notification_failure': 'decision_notify', 'commit_failure': 'commit',
               'detector_failure': 'detector', 'artifact_failure': 'provider_evidence'}[mutation]
        steps[key].update(outcome='failure', conclusion='failure')
    elif mutation == 'cancelled_step': steps['decision_notify'].update(outcome='cancelled', conclusion='cancelled')
    elif mutation == 'continue_on_error': steps['decision_notify']['outcome'] = 'failure'
    elif mutation == 'trade': steps['trade']['outputs']['trade_count'] = '1'
    elif mutation == 'corporate': steps['corporate']['outputs']['changed'] = 'true'
    elif mutation == 'weekly': steps['weekly_execution']['outputs']['executed'] = 'true'
    elif mutation in {'dirty', 'portfolio_changed'}:
        (workspace / 'portfolio.json').write_text('{"cash":123}')
        if mutation == 'portfolio_changed':
            git(workspace, 'add', '.'); git(workspace, 'commit', '-m', 'trade')
            git(workspace, 'push', 'origin', 'main')
    elif mutation == 'untracked': (workspace / 'unsaved.json').write_text('{}')
    elif mutation == 'unpushed':
        (workspace / 'state/violations.json').write_text('{}')
        git(workspace, 'add', '.'); git(workspace, 'commit', '-m', 'unpublished')
    elif mutation == 'remote_unavailable': git(workspace, 'remote', 'set-url', 'origin', str(tmp_path / 'missing'))
    elif mutation == 'wrong_workflow': context['GITHUB_WORKFLOW'] = 'Weekly Portfolio Round'
    elif mutation == 'cancelled_job': outcome = 'cancelled'
    context['LOCAL_RUNNER_STEPS'] = json.dumps(steps)
    guard.finish(root, context, outcome)
    assert (root / 'active.json').exists()
    assert 'release_reason' not in json.loads((root / '101.json').read_text())
    with pytest.raises(RuntimeError, match='Unresolved'):
        guard.start(root, {**context, 'GITHUB_RUN_ID': '102'})


def test_pending_execution_or_missing_health_evidence_is_not_released(tmp_path):
    guard, root, context, steps, workspace = fixture(tmp_path)
    (workspace / 'state/pending_decision.json').write_text('{"decisions":[{"action":"BUY","symbol":"AMD"}]}')
    git(workspace, 'add', '.'); git(workspace, 'commit', '-m', 'pending')
    git(workspace, 'push', 'origin', 'main')
    guard.finish(root, context, 'failure')
    assert (root / 'active.json').exists()


def test_empty_health_evidence_is_not_released(tmp_path):
    guard, root, context, steps, workspace = fixture(tmp_path)
    (workspace / 'state/violations.json').write_text('{}')
    git(workspace, 'add', '.'); git(workspace, 'commit', '-m', 'empty health')
    git(workspace, 'push', 'origin', 'main')
    guard.finish(root, context, 'failure')
    assert (root / 'active.json').exists()


def test_checkout_baseline_is_bound_before_financial_work(tmp_path):
    guard, root, context, steps, workspace = fixture(tmp_path, event_sha='a' * 40)
    baseline = json.loads((root / '101.json').read_text())
    assert baseline['checkout_sha'] == steps['checkout']['outputs']['commit']
    guard.finish(root, context, 'failure')
    assert not (root / 'active.json').exists()


@pytest.mark.parametrize('mutation', ['ignored_evidence', 'symlink_evidence', 'symlink_state'])
def test_uncommitted_or_symlinked_evidence_cannot_release(tmp_path, mutation):
    guard, root, context, steps, workspace = fixture(tmp_path)
    state = workspace / 'state'; evidence = state / 'violations.json'
    if mutation == 'ignored_evidence':
        git(workspace, 'rm', '--cached', 'state/violations.json')
        (workspace / '.gitignore').write_text('state/violations.json\n')
    elif mutation == 'symlink_evidence':
        saved = tmp_path / 'evidence.json'; saved.write_bytes(evidence.read_bytes())
        evidence.unlink(); evidence.symlink_to(saved)
    else:
        moved = tmp_path / 'external-state'; state.rename(moved); state.symlink_to(moved, target_is_directory=True)
    git(workspace, 'add', '-A'); git(workspace, 'commit', '-m', 'unsafe evidence')
    git(workspace, 'push', 'origin', 'main')
    guard.finish(root, context, 'failure')
    assert (root / 'active.json').exists()


def test_checkout_baseline_not_event_sha(tmp_path):
    guard, root, context, steps, workspace = fixture(tmp_path, event_sha='a' * 40)
    # Event revision may not even be in a shallow checkout of newer main.
    guard.finish(root, context, 'failure')
    assert not (root / 'active.json').exists()
    receipt = json.loads((root / '101.json').read_text())
    assert receipt['checkout_sha'] == steps['checkout']['outputs']['commit']


@pytest.mark.parametrize('kind', ['ignored', 'symlink', 'state_symlink'])
def test_health_evidence_must_be_regular_tracked_and_exact(tmp_path, kind):
    guard, root, context, steps, workspace = fixture(tmp_path)
    health = workspace / 'state/violations.json'
    if kind == 'ignored':
        git(workspace, 'rm', '--cached', 'state/violations.json')
        (workspace / '.gitignore').write_text('state/violations.json\n')
    elif kind == 'symlink':
        external = tmp_path / 'external.json'; external.write_bytes(health.read_bytes())
        health.unlink(); health.symlink_to(external)
    else:
        state = workspace / 'state'; state.rename(tmp_path / 'external-state')
        state.symlink_to(tmp_path / 'external-state', target_is_directory=True)
    git(workspace, 'add', '-A'); git(workspace, 'commit', '-m', 'untrusted evidence')
    git(workspace, 'push', 'origin', 'main')
    guard.finish(root, context, 'failure')
    assert (root / 'active.json').exists()


def test_workflow_covers_every_step_with_explicit_identity():
    import yaml
    workflow = yaml.safe_load((Path(__file__).resolve().parents[1] / '.github/workflows/detector.yml').read_text())
    steps = workflow['jobs']['detect']['steps']
    assert all('id' in step for step in steps[:-1])
    assert {step['id'] for step in steps[:-1]} == STEP_IDS == load_guard().PARTIAL_STEP_IDS
    assert steps[-1]['env']['LOCAL_RUNNER_STEPS'] == '${{ toJSON(steps) }}'
