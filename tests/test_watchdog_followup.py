from datetime import datetime, timedelta, timezone

import watchdog as wd
from tests.test_watchdog_incidents import harness, run, state, NOW


def test_ordinary_running_work_is_not_a_failure_alert(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    messages = []
    result = wd.monitor(NOW, state(), harness([run(3, 0, None, 'in_progress')]),
                        lambda **kw: messages.append(kw), apply=True)
    assert result[0]['status'] == 'running'
    assert messages == []


def test_historical_message_explains_window_and_links_exact_run(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    messages = []
    wd.monitor(NOW, state(), harness([run(2)]),
               lambda **kw: messages.append(kw['message']), apply=True)
    assert 'Geçmiş olay açık' in messages[0]
    assert 'planlı üretim çalışması bekleniyor' in messages[0]
    assert 'penceresi dışında' in messages[0]
    assert '/actions/runs/2/attempts/1' in messages[0]
    assert 'deneme sayısı: 0' in messages[0]


def test_past_recovery_cannot_hide_current_missing_deadline(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {'detector.yml': NOW})
    s = state()
    s['incidents']['detector.yml']['attempts'] = 2
    messages = []
    result = wd.monitor(NOW, s, harness([run(3, 1, 'success'), run(2, 2)]),
                        lambda **kw: messages.append(kw['message']), apply=True)
    assert result[0]['status'] == 'missing'
    assert result[0]['verification'] == 'pending_production'
    assert not s['incidents']['detector.yml'].get('resolved')
    assert not any('toparlanma doğrulandı' in message for message in messages)


def test_recovery_records_exact_successful_attempt(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state()
    success = run(3, 0, 'success')
    success['head_sha'] = 'verified-test-sha'
    messages = []
    result = wd.monitor(NOW, s, harness([success, run(2)]),
                        lambda **kw: messages.append(kw['message']), apply=True)
    receipt = s['incidents']['detector.yml']['recovery']
    assert receipt['run_id'] == 3 and receipt['run_attempt'] == 1
    assert receipt['head_sha'] == 'verified-test-sha'
    assert receipt['verification'] == 'verified_production'
    assert '/actions/runs/3/attempts/1' in messages[0]
    assert result[0]['run_id'] == 3


def test_older_failed_response_cannot_replace_latest_observed_failure(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state()
    messages = []
    wd.monitor(NOW, s, harness([run(30, 1)]),
               lambda **kw: messages.append(kw), apply=True)
    result = wd.monitor(NOW, s, harness([run(10, 3)]),
                        lambda **kw: messages.append(kw), apply=True)
    assert result[0]['run_id'] == 30
    assert len(messages) == 1


def test_stuck_set_selection_scope_changes_and_resumed_recovery(monkeypatch):
    import json
    import pytest

    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state()
    messages = []
    send = lambda **kw: messages.append(kw['message'])
    oldest = run(10, 3, None, 'in_progress')
    fresh = run(20, 0, None, 'in_progress')
    first = wd.monitor(NOW, s, harness([fresh, oldest]), send, apply=True)[0]
    # Actual review reproduction: fresh run 20 must never own stuck run 10.
    assert first['status'] == 'stuck' and first['run_id'] == 10
    assert first['overdue_runs'] == [{'run_id': 10, 'run_attempt': 1}]
    with pytest.raises(ValueError):
        wd.acknowledge(s, 'detector.yml', first['observation_id'],
                       'run:20:attempt:1; inspected fresh run', 'reviewer', NOW)
    wd.acknowledge(s, 'detector.yml', first['observation_id'],
                   'run:10:attempt:1; inspected oldest run', 'reviewer', NOW)
    wd.monitor(NOW, s, harness([oldest, fresh]), send, apply=True)
    assert len(messages) == 1

    later = NOW + timedelta(hours=3)
    second = wd.monitor(later, s, harness([fresh, oldest]), send, apply=True)[0]
    identities = [{'run_id': 10, 'run_attempt': 1}, {'run_id': 20, 'run_attempt': 1}]
    assert second['run_id'] == 10 and second['overdue_runs'] == identities
    assert second['observation_id'] != first['observation_id']
    assert len(messages) == 2
    for identity in identities:
        token = f"run:{identity['run_id']}:attempt:{identity['run_attempt']}"
        assert token in messages[-1]
        assert f"/actions/runs/{identity['run_id']}/attempts/{identity['run_attempt']}" in messages[-1]
    for evidence in ('run:10:attempt:1; only oldest inspected',
                     'run:10:attempt:1; run:20:attempt:1 appears only in prose',
                     'run:10:attempt:1 run:20:attempt:10; wrong attempt'):
        with pytest.raises(ValueError):
            wd.acknowledge(s, 'detector.yml', second['observation_id'], evidence, 'reviewer', later)
    wd.acknowledge(s, 'detector.yml', second['observation_id'],
                   'run:10:attempt:1 run:20:attempt:1; both execution logs inspected', 'reviewer', later)
    assert s['incidents']['detector.yml']['acknowledgement']['overdue_runs'] == identities
    # Resume from serialized durable state; ordering must not change the fingerprint.
    s = json.loads(json.dumps(s))
    repeated = wd.monitor(later, s, harness([oldest, fresh]), send, apply=True)[0]
    assert repeated['observation_id'] == second['observation_id'] and len(messages) == 2
    fresh['run_attempt'] = 2
    changed = wd.monitor(later, s, harness([fresh, oldest]), send, apply=True)[0]
    assert changed['observation_id'] != second['observation_id'] and len(messages) == 3
    remaining = wd.monitor(later, s, harness([oldest]), send, apply=True)[0]
    assert remaining['observation_id'] != changed['observation_id'] and len(messages) == 4
    recovery = dict(run(30, 0, 'success'), run_started_at=later.isoformat())
    wd.monitor(later, s, harness([recovery]), send, apply=True)
    assert s['incidents']['detector.yml']['resolved']
    assert s['incidents']['detector.yml']['recovery']['run_id'] == 30
    assert len(messages) == 5
