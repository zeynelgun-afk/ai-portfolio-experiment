"""Offline adapter contracts; no inference is made by the test suite."""
import json
import subprocess
from unittest.mock import patch
import pytest


def test_transport_uses_isolated_subscription_and_validates_schema():
    import llm_transport as llm
    schema = {'name': 'claim', 'schema': {'type': 'object', 'properties': {'status': {'const': 'valid'}}, 'required': ['status'], 'additionalProperties': False}}
    events = '\n'.join(json.dumps(x) for x in [
        {'type': 'system', 'subtype': 'init', 'model': 'gpt-6-astra'},
        {'type': 'result', 'exit_code': 0, 'text': '{"status":"valid"}', 'session_id': 'fresh'}])
    with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, events, '')) as run:
        text = llm.complete([{'role': 'user', 'content': 'supplied evidence'}], response_schema=schema)
    assert json.loads(text) == {'status': 'valid'}
    argv = run.call_args.args[0]
    for flag in ('--safe-mode', '--oneshot', '--query-file', '--run-budget'):
        assert flag in argv
    assert argv[argv.index('--provider') + 1] == 'openai-codex'
    assert argv[argv.index('--toolsets') + 1] == 'none'
    assert '--resume' not in argv
    assert run.call_args.kwargs['timeout'] <= 210
    assert 'supplied evidence' in run.call_args.kwargs['input']
    assert 'OPENROUTER_API_KEY' not in run.call_args.kwargs['env']


@pytest.mark.parametrize('events,code', [
    ([None], 0),
    ([[]], 0),
    ([123], 0),
    ([{'type': 'result', 'exit_code': 1}], 0),
    ([{'type': 'tool_use', 'name': 'terminal'}], 0),
    ([], 1),
    ([{'type': 'system', 'subtype': 'init', 'model': 'gpt-6-astra'},
      {'type': 'result', 'exit_code': 0, 'session_id': 'x', 'text': '```json\n{}\n```'}], 0),
])
def test_no_fallback_on_failure(events, code):
    import llm_transport as llm
    with patch('subprocess.run', return_value=subprocess.CompletedProcess([], code, '\n'.join(map(json.dumps, events)), 'PRIVATE')) as run:
        with pytest.raises(llm.InferenceError):
            llm.complete([])
    assert run.call_count == 1


def test_reassess_routes_locally_without_http_or_secret():
    import reassess
    with patch('llm_transport.complete', return_value='{"status":"valid"}') as local, patch('urllib.request.urlopen', side_effect=AssertionError('paid network forbidden')):
        assert reassess._single_call('gpt-6-astra', [], '') == ('{"status":"valid"}', False)
    local.assert_called_once()


def test_all_inference_entrypoints_are_subscription_only():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for file in root.glob('*.py'):
        if file.name == 'llm_transport.py':
            continue
        text = file.read_text()
        assert 'openrouter.ai' not in text, file.name
        assert 'OPENROUTER_API_KEY' not in text, file.name
        assert 'OPENROUTER_MODEL_' not in text, file.name


def test_schema_rejection_never_returns_unvalidated_text():
    import llm_transport as llm
    events = [ {'type': 'system', 'subtype': 'init', 'model': 'gpt-6-astra'},
               {'type': 'result', 'exit_code': 0, 'session_id': 'x', 'text': '{"status":"invented"}'}]
    with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, '\n'.join(map(json.dumps, events)), '')):
        with pytest.raises(llm.InferenceError):
            llm.complete([], {'name': 'x', 'schema': {'type': 'object', 'properties': {'status': {'const': 'valid'}}}})
