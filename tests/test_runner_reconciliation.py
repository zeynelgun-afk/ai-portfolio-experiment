"""Operator reconciliation never rewrites failure receipts or permits replay."""
import hashlib
import json
from pathlib import Path
from tests.test_local_runner import load_guard, env
import pytest


def fixture(tmp_path):
    guard = load_guard()
    workspace = tmp_path / 'checkout'; workspace.mkdir()
    (workspace / 'portfolio.json').write_text('{}')
    root = tmp_path / 'journal'
    context = {**env(), 'GITHUB_WORKSPACE': str(workspace)}
    guard.start(root, context)
    guard.finish(root, context, 'failure')
    expected = json.loads((root / 'active.json').read_text())
    evidence = tmp_path / 'investigation.json'
    evidence.write_text('{"commit":"verified","trades":"none","pending":"none","notifications":"delivered"}')
    audit = {
        'resolution': 'persisted-no-replay',
        'reason': 'All effects accounted for; provider failure remains a failure.',
        'archive_sha256': hashlib.sha256((root / '101-artifacts.tar.gz').read_bytes()).hexdigest(),
        'receipt_sha256': hashlib.sha256((root / '101.json').read_bytes()).hexdigest(),
        'evidence': [{'path': str(evidence), 'sha256': hashlib.sha256(evidence.read_bytes()).hexdigest()}],
        'checks': {key: 'verified in investigation.json' for key in ('commit', 'trades', 'pending', 'notifications')},
    }
    return guard, root, expected, audit


def test_reconcile_preserves_receipt_archive_failure_and_replay_ban(tmp_path):
    guard, root, expected, audit = fixture(tmp_path)
    before = {p.name: p.read_bytes() for p in root.iterdir() if p.name != 'active.json'}
    guard.reconcile(root, expected, audit)
    assert not (root / 'active.json').exists()
    for name, data in before.items():
        assert (root / name).read_bytes() == data
    record = json.loads((root / '101-reconciliation.json').read_text())
    assert record['attempt'] == expected
    assert record['audit'] == audit
    with pytest.raises(RuntimeError, match='already'):
        guard.start(root, {**env(), 'GITHUB_RUN_ATTEMPT': '2'})
    guard.start(root, env('102'))


@pytest.mark.parametrize('mutation', ['identity', 'unfinished', 'receipt', 'archive', 'evidence', 'checks', 'resolution', 'existing_audit'])
def test_reconcile_refuses_ambiguous_or_changed_evidence(tmp_path, mutation):
    guard, root, expected, audit = fixture(tmp_path)
    if mutation == 'identity':
        expected['sha'] = 'wrong'
    elif mutation == 'unfinished':
        expected['status'] = 'started'
        for name in ('active.json', '101.json'):
            (root / name).write_text(json.dumps(expected))
    elif mutation == 'receipt':
        (root / '101.json').write_text('{}')
    elif mutation == 'archive':
        (root / '101-artifacts.tar.gz').write_bytes(b'changed')
    elif mutation == 'evidence':
        Path(audit['evidence'][0]['path']).write_text('changed')
    elif mutation == 'checks':
        audit['checks'].pop('notifications')
    elif mutation == 'resolution':
        audit['resolution'] = 'success'
    elif mutation == 'existing_audit':
        (root / '101-reconciliation.json').write_text('{}')
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    with pytest.raises(RuntimeError):
        guard.reconcile(root, expected, audit)
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


def test_reconcile_cli_uses_explicit_expected_and_audit_files(tmp_path):
    import subprocess
    import sys
    guard, root, expected, audit = fixture(tmp_path)
    expected_file = tmp_path / 'expected.json'; expected_file.write_text(json.dumps(expected))
    audit_file = tmp_path / 'audit.json'; audit_file.write_text(json.dumps(audit))
    result = subprocess.run([sys.executable, guard.__file__, 'reconcile', '--state', str(root),
                             '--expected', str(expected_file), '--audit', str(audit_file)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not (root / 'active.json').exists()


def test_reconcile_uses_recorded_unverified_archive(tmp_path):
    guard, root, expected, audit = fixture(tmp_path)
    original = root / '101-artifacts.tar.gz'
    original.rename(root / '101-unverified-workspace.tar.gz')
    expected.update(archive='101-unverified-workspace.tar.gz', checkout_outcome='failure', workspace_provenance='unverified-checkout')
    for name in ('active.json', '101.json'):
        (root / name).write_text(json.dumps(expected))
    audit['receipt_sha256'] = hashlib.sha256((root / '101.json').read_bytes()).hexdigest()
    guard.reconcile(root, expected, audit)
    assert not (root / 'active.json').exists()


@pytest.mark.parametrize('field,value', [('reason', '  '), ('reason', True), ('evidence', {'unexpected': True}), ('evidence', [None])])
def test_reconcile_rejects_malformed_attestation(tmp_path, field, value):
    guard, root, expected, audit = fixture(tmp_path)
    audit[field] = value
    with pytest.raises(RuntimeError, match='evidence review'):
        guard.reconcile(root, expected, audit)
    assert (root / 'active.json').exists()


def test_reconcile_audit_sync_failure_keeps_active(tmp_path, monkeypatch):
    guard, root, expected, audit = fixture(tmp_path)
    def fail(fd):
        raise OSError('disk failure')
    monkeypatch.setattr(guard.os, 'fsync', fail)
    with pytest.raises(OSError):
        guard.reconcile(root, expected, audit)
    assert (root / 'active.json').exists()
