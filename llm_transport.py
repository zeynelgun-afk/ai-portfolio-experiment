"""Subscription-only Hermes CLI transport. No HTTP endpoint or paid fallback.

Each request is a fresh, tool-free context. Structured output is checked locally;
CLI prompting is NOT provider-enforced structured decoding. Domain evidence and
paper-trade validation remain the caller's responsibility.
"""
import json
import os
import subprocess
import tempfile

from jsonschema import validate, ValidationError

MODEL = 'gpt-6-astra'
TIMEOUT = 180


class InferenceError(RuntimeError):
    """Sanitized failure: raw provider diagnostics may contain sensitive data."""


def credential():
    """Compatibility truth value for callers; never an API credential."""
    return 'local-hermes-subscription'


def complete(messages, response_schema=None):
    prompt = ('You are a tool-free inference component for a PAPER portfolio experiment. '
              'Use only supplied evidence. Follow the system instructions in the message envelope. '
              'Return ONLY valid JSON, no markdown. Do not execute actions.\nMESSAGES:\n'
              + json.dumps(messages, ensure_ascii=False))
    if response_schema:
        prompt += '\nREQUIRED JSON SCHEMA:\n' + json.dumps(response_schema['schema'])
    command = [os.environ.get('HERMES_BIN', 'hermes'), 'chat', '--query-file', '-',
               '--oneshot', '--format', 'stream-json', '--safe-mode',
               '--provider', 'openai-codex', '--model', MODEL,
               '--toolsets', 'none', '--max-turns', '1',
               '--run-budget', str(TIMEOUT), '--source', 'tool']
    # Do not pass data/Telegram/GitHub keys to the inference subprocess. Hermes
    # resolves the existing local OAuth connection itself. Safe mode ignores
    # config, fallback chains, rules, memory, plugins and MCP.
    child_env = {k: v for k, v in os.environ.items() if k in
                 ('HOME', 'PATH', 'LANG', 'LC_ALL', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME',
                  'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'HERMES_HOME')}
    try:
        with tempfile.TemporaryDirectory(prefix='portfolio-inference-') as cwd:
            result = subprocess.run(command, input=prompt, text=True, capture_output=True,
                                    timeout=TIMEOUT + 15, cwd=cwd, env=child_env)
        if result.returncode:
            raise InferenceError('Hermes process failed')
        events = []
        for line in result.stdout.splitlines():
            if line == 'Warning: Unknown toolsets: none':
                continue  # installed CLI warns, resolver returns zero tools
            event = json.loads(line)
            if not isinstance(event, dict):
                raise InferenceError('Invalid Hermes protocol')
            events.append(event)
        if any(e.get('type') in ('tool_use', 'tool_result') for e in events):
            raise InferenceError('Unexpected tool activity')
        initial = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
        finals = [e for e in events if e.get('type') == 'result']
        if len(initial) != 1 or initial[0].get('model') != MODEL or len(finals) != 1:
            raise InferenceError('Invalid Hermes protocol')
        final = finals[0]
        if final.get('exit_code') != 0 or final.get('error') or not final.get('session_id'):
            raise InferenceError('Hermes inference failed')
        payload = json.loads(final['text'])
        if response_schema:
            validate(payload, response_schema['schema'])
        return json.dumps(payload, ensure_ascii=False)
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError, ValidationError):
        raise InferenceError('Hermes unavailable or invalid structured output') from None
