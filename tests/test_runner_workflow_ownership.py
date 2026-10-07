"""Workflow regression: rejected setup must not consume the pinned old checkout."""
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_offline_smoke_explicitly_skips_inference():
    data = yaml.safe_load((ROOT / '.github/workflows/local-hermes-smoke.yml').read_text())
    # PyYAML 1.1 resolves the Actions `on` key to True.
    inputs = data[True]['workflow_dispatch']['inputs'] or {}
    assert inputs['offline_only']['type'] == 'boolean'
    assert inputs['offline_only']['default'] is True
    infer = next(s for s in data['jobs']['smoke']['steps'] if s.get('run') == 'python smoke_llm.py')
    assert infer['if'] == '!inputs.offline_only'


@pytest.mark.parametrize('workflow', ['detector.yml', 'weekly.yml', 'local-hermes-smoke.yml'])
def test_failed_setup_skips_workspace_consumers(workflow):
    data = yaml.safe_load((ROOT / '.github/workflows' / workflow).read_text())
    for job in data['jobs'].values():
        steps = job['steps']
        checkout = next(s for s in steps if s.get('uses', '').startswith('actions/checkout@'))
        assert checkout.get('id') == 'checkout'
        for step in steps:
            if step.get('uses', '').startswith('actions/upload-artifact@') or step.get('name') == 'Report provider failover':
                assert step['if'] == "always() && steps.checkout.outcome == 'success'", step
        finish = next(s for s in steps if 'local_runner_guard.py' in s.get('run', ''))
        assert finish.get('env', {}).get('LOCAL_RUNNER_CHECKOUT_OUTCOME') == '${{ steps.checkout.outcome }}'
        # Failed checkout still needs an owned failure archive; rejected setup does not.
        assert finish['if'] == "always() && contains(fromJSON('[\"success\",\"failure\",\"cancelled\"]'), steps.checkout.outcome)"
