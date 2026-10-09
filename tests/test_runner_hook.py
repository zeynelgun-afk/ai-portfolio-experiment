"""Runner 2.337.0 pre-job hooks have a random step context, not a YAML id."""
import json
from pathlib import Path
import pytest
from tests.test_runner_partial import fixture

HOOK = 'a26c83da3a754645a5cf6f506cd1caa3'
PRODUCTION = Path(__file__).parent / 'fixtures/runner-37868689813-steps.json'


@pytest.mark.parametrize('bound', [False, True])
def test_exact_production_step_contract_offline(tmp_path, bound):
    # Captured 37868689813/1 steps, including full=true, market_open=false,
    # missing weekly executed output and skipped downstream health gates.
    # Only the future hook binding is added; git/journal remain isolated.
    guard, root, context, _, workspace = fixture(tmp_path, hook=bound)
    steps = json.loads(PRODUCTION.read_text())
    if bound:
        claim = json.loads((root / '101.json').read_text())['hook_claim']
        steps[HOOK]['outputs'] = {'local_runner_claim': claim}
    context['LOCAL_RUNNER_STEPS'] = json.dumps(steps)
    guard.finish(root, context, 'failure')
    assert (root / 'active.json').exists() is not bound
    receipt = json.loads((root / '101.json').read_text())
    assert receipt['status'] == 'failure'
    assert ('release_reason' in receipt) is bound


@pytest.mark.parametrize('mutation', [
    'empty', 'wrong_claim', 'missing', 'duplicate', 'unknown_hex', 'unknown_named',
    'failed_hook', 'continued_hook', 'skipped_hook', 'extra_output', 'named_hook',
    'missing_core', 'notification_failure', 'trade', 'unbound_claim',
])
def test_untrusted_or_ambiguous_extra_step_keeps_claim(tmp_path, mutation):
    guard, root, context, _, workspace = fixture(tmp_path, hook=mutation != 'unbound_claim')
    steps = json.loads(PRODUCTION.read_text())
    claim = json.loads((root / '101.json').read_text()).get('hook_claim', 'a' * 64)
    steps[HOOK]['outputs'] = {'local_runner_claim': claim}
    if mutation == 'empty': steps[HOOK]['outputs'] = {}
    elif mutation == 'wrong_claim': steps[HOOK]['outputs']['local_runner_claim'] = 'b' * 64
    elif mutation == 'missing': steps.pop(HOOK)
    elif mutation == 'duplicate': steps['c' * 32] = steps[HOOK].copy()
    elif mutation.startswith('unknown_'):
        key = 'c' * 32 if mutation == 'unknown_hex' else 'unknown_effect'
        steps[key] = {'outputs': {}, 'outcome': 'success', 'conclusion': 'success'}
    elif mutation == 'failed_hook': steps[HOOK].update(outcome='failure', conclusion='failure')
    elif mutation == 'continued_hook': steps[HOOK]['outcome'] = 'failure'
    elif mutation == 'skipped_hook': steps[HOOK].update(outcome='skipped', conclusion='skipped')
    elif mutation == 'extra_output': steps[HOOK]['outputs']['unexpected'] = 'value'
    elif mutation == 'named_hook': steps['not_a_runner_guid'] = steps.pop(HOOK)
    elif mutation == 'missing_core': steps.pop('decision_notify')
    elif mutation == 'notification_failure': steps['decision_notify'].update(outcome='failure', conclusion='failure')
    elif mutation == 'trade': steps['trade']['outputs']['trade_count'] = '1'
    context['LOCAL_RUNNER_STEPS'] = json.dumps(steps)
    guard.finish(root, context, 'failure')
    assert (root / 'active.json').exists()
    assert 'release_reason' not in json.loads((root / '101.json').read_text())


@pytest.mark.parametrize('binding', ['absent', None, '', 'a' * 63, 'G' * 64, 123])
def test_missing_or_malformed_journal_binding_never_releases_core_only(tmp_path, binding):
    guard, root, context, steps, workspace = fixture(tmp_path, hook=False)
    if binding != 'absent':
        attempt = json.loads((root / 'active.json').read_text())
        attempt['hook_claim'] = binding
        guard.atomic_json(root / 'active.json', attempt)
        guard.atomic_json(root / '101.json', attempt)
    guard.finish(root, context, 'failure')
    assert (root / 'active.json').exists()
    assert 'release_reason' not in json.loads((root / '101.json').read_text())


def test_hook_output_failure_keeps_durable_unresolved_claim(tmp_path):
    from tests.test_local_runner import load_guard, env
    guard, root = load_guard(), tmp_path / 'journal'
    context = {**env(), 'GITHUB_OUTPUT': str(tmp_path / 'missing' / 'output')}
    with pytest.raises(OSError):
        guard.start(root, context)
    assert json.loads((root / 'active.json').read_text()) == json.loads((root / '101.json').read_text())
    with pytest.raises(RuntimeError, match='Unresolved'):
        guard.start(root, {**context, 'GITHUB_RUN_ID': '102'})


@pytest.mark.parametrize('binding', ['absent', None, '', 'g' * 64, 'a' * 63])
def test_core_only_context_without_binding_cannot_release(tmp_path, binding):
    guard, root, context, steps, workspace = fixture(tmp_path, hook=False)
    receipt = json.loads((root / '101.json').read_text())
    if binding != 'absent':
        receipt['hook_claim'] = binding
        for name in ('101.json', 'active.json'):
            (root / name).write_text(json.dumps(receipt))
    guard.finish(root, context, 'failure')
    assert (root / 'active.json').exists()
    assert 'release_reason' not in json.loads((root / '101.json').read_text())


def test_bound_pre_job_hook_releases_persisted_partial(tmp_path):
    guard, root, context, steps, workspace = fixture(tmp_path, hook=True)
    output = Path(context['GITHUB_OUTPUT']).read_text()
    assert output.startswith('local_runner_claim=')
    claim = output.strip().split('=', 1)[1]
    assert json.loads((root / '101.json').read_text())['hook_claim'] == claim
    steps[HOOK] = {'outputs': {'local_runner_claim': claim},
                   'outcome': 'success', 'conclusion': 'success'}
    context['LOCAL_RUNNER_STEPS'] = json.dumps(steps)
    guard.finish(root, context, 'failure')
    receipt = json.loads((root / '101.json').read_text())
    assert receipt['status'] == 'failure'
    assert receipt['release_reason'] == 'persisted-no-trade-partial'
    assert receipt['partial_evidence']['steps'] == steps
    assert not (root / 'active.json').exists()
    with pytest.raises(RuntimeError, match='already'):
        guard.start(root, {**context, 'GITHUB_RUN_ATTEMPT': '2'})
