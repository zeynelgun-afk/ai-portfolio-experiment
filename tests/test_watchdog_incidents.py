from datetime import datetime, timedelta, timezone
from pathlib import Path
import watchdog as wd

NOW = datetime(2026, 10, 5, 10, tzinfo=timezone.utc)
SINCE = NOW - timedelta(days=7)

def run(identity, age=1, conclusion='failure', status='completed', event='schedule'):
    return dict(id=identity, run_attempt=1, head_branch='main', event=event,
                created_at=(NOW-timedelta(hours=age)).isoformat(), status=status, conclusion=conclusion)

def harness(runs, core='success'):
    def fetch(endpoint, method='GET', payload=None):
        assert method == 'GET'
        if endpoint.endswith('/jobs'):
            return {'jobs': [{'steps': [{'name': '1) Detector', 'conclusion': core}]}]}
        return {'workflow_runs': runs}
    return fetch

def state():
    return {'incidents': {'detector.yml': {'since': SINCE.isoformat(), 'attempts': 0}}}

def test_latest_failure_beats_older_success():
    assert wd.diagnose([run(1, 5, 'success'), run(2)], SINCE, NOW)[0] == 'failed'

def test_weekly_workflow_has_required_heartbeat_prefix():
    assert '- name: 3b) Structured decision' in Path('.github/workflows/weekly.yml').read_text()

def test_unchanged_historical_incident_is_deduplicated_and_zero_attempt_reason(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s=state(); messages=[]
    for moment in (NOW, NOW+timedelta(days=1)):
        result=wd.monitor(moment,s,harness([run(2)]),lambda **kw: messages.append(kw['message']),True)
    assert len(messages)==1
    assert 'deneme sınır' not in messages[0]
    assert result[0]['reason']=='outside_due_window'
    assert not s['incidents']['detector.yml'].get('resolved')

def test_changed_due_window_keeps_historical_failure_and_alerts_transition(monkeypatch):
    s=state(); messages=[]
    monkeypatch.setattr(wd,'due_windows',lambda now: {})
    wd.monitor(NOW,s,harness([run(2)]),lambda **kw:messages.append(kw),True)
    monkeypatch.setattr(wd,'due_windows',lambda now: {'detector.yml':NOW})
    result=wd.monitor(NOW,s,harness([run(2)]),lambda **kw:messages.append(kw),True)
    assert result[0]['status']=='failed'
    assert result[0]['current_status']=='missing'
    assert result[0]['verification']=='pending_production'
    assert len(messages)==2
    assert not s['incidents']['detector.yml'].get('resolved')

def test_skipped_and_smoke_do_not_recover_but_later_core_success_does(monkeypatch):
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    for candidate,core in [(run(3,0,'success'),'skipped'),(run(3,0,'success',event='push'),'success')]:
        s=state()
        wd.monitor(NOW,s,harness([candidate,run(2)],core),lambda **kw:None,True)
        assert not s['incidents']['detector.yml'].get('resolved')
    s=state();messages=[]
    wd.monitor(NOW,s,harness([run(3,0,'success'),run(2)]),lambda **kw:messages.append(kw),True)
    assert s['incidents']['detector.yml']['resolved']
    assert len(messages)==1

def test_waiting_becomes_stuck_and_delivery_error_retries(monkeypatch):
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    s=state(); r=run(3,1,None,'waiting'); messages=[]
    result=wd.monitor(NOW,s,harness([r,run(2)]),lambda **kw:messages.append(kw),True)
    assert result[0]['status']=='running'
    assert not s['incidents']['detector.yml'].get('resolved')
    def fail(**kw): raise RuntimeError('delivery failed')
    import pytest
    with pytest.raises(RuntimeError): wd.monitor(NOW+timedelta(hours=2),s,harness([r,run(2)]),fail,True)
    wd.monitor(NOW+timedelta(hours=2),s,harness([r,run(2)]),lambda **kw:messages.append(kw),True)
    assert len(messages)==1

def test_acknowledgement_is_identity_scoped_and_new_failure_alerts(monkeypatch):
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    s=state();messages=[]
    result=wd.monitor(NOW,s,harness([run(2)]),lambda **kw:messages.append(kw),True)
    import pytest
    with pytest.raises(ValueError): wd.acknowledge(s,'detector.yml','wrong','logs/run-2','operator',NOW)
    with pytest.raises(ValueError): wd.acknowledge(s,'detector.yml',result[0]['observation_id'],'','operator',NOW)
    wd.acknowledge(s,'detector.yml',result[0]['observation_id'],'run:2:attempt:1; reviewed failed core step','operator',NOW)
    assert not s['incidents']['detector.yml'].get('resolved')
    wd.monitor(NOW,s,harness([run(2)]),lambda **kw:messages.append(kw),True)
    wd.monitor(NOW,s,harness([run(3,0)]),lambda **kw:messages.append(kw),True)
    assert len(messages)==2

def test_ack_rejects_incidental_id_and_requires_exact_attempt(monkeypatch):
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    s=state(); observation=wd.monitor(NOW,s,harness([run(2)]),apply=False)[0]
    import pytest
    with pytest.raises(ValueError):
        wd.acknowledge(s,'detector.yml',observation['observation_id'],'reviewed 2026 issue','operator',NOW)
    wd.acknowledge(s,'detector.yml',observation['observation_id'],'run:2:attempt:1; log reviewed','operator',NOW)

def test_rerun_attempt_change_alerts(monkeypatch):
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    s=state();messages=[];r=run(2)
    wd.monitor(NOW,s,harness([r]),lambda **kw:messages.append(kw),True)
    r['run_attempt']=2
    wd.monitor(NOW,s,harness([r]),lambda **kw:messages.append(kw),True)
    assert len(messages)==2

def test_older_success_cannot_resolve_observed_failure_when_run_list_changes(monkeypatch):
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    s=state()
    wd.monitor(NOW,s,harness([run(2)]),lambda **kw:None,True)
    wd.monitor(NOW,s,harness([run(1,5,'success')]),lambda **kw:None,True)
    assert not s['incidents']['detector.yml'].get('resolved')

def test_failure_watermark_survives_running_observation(monkeypatch):
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    s=state()
    for runs in ([run(2)], [run(3,0,None,'waiting'),run(2)], [run(1,5,'success')]):
        wd.monitor(NOW,s,harness(runs),lambda **kw:None,True)
    assert not s['incidents']['detector.yml'].get('resolved')

def test_ack_cli_only_updates_explicit_local_state(tmp_path,monkeypatch):
    import json
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    s=state();obs=wd.monitor(NOW,s,harness([run(2)]),apply=False)[0]
    path=tmp_path/'watchdog.json';path.write_text(json.dumps(s))
    monkeypatch.setattr('sys.argv',['watchdog','--state',str(path),'--ack-workflow','detector.yml',
        '--ack-observation',obs['observation_id'],'--ack-evidence','run:2:attempt:1; reviewed log file','--ack-operator','reviewer'])
    monkeypatch.setattr(wd,'monitor',lambda *a,**kw: (_ for _ in ()).throw(AssertionError('monitor forbidden')))
    wd.main()
    saved=json.loads(path.read_text())
    assert saved['incidents']['detector.yml']['acknowledgement']['run_id']==2
    assert not saved['incidents']['detector.yml'].get('resolved')

def test_sliding_intraday_deadline_does_not_repeat_same_failure(monkeypatch):
    s=state();messages=[]
    monkeypatch.setattr(wd,'due_windows',lambda now:{'detector.yml':now-timedelta(minutes=90)})
    for now in (NOW,NOW+timedelta(minutes=5)):
        wd.monitor(now,s,harness([run(2)]),lambda **kw:messages.append(kw),True)
    assert len(messages)==1
    wd.monitor(NOW+timedelta(days=1),s,harness([run(2)]),lambda **kw:messages.append(kw),True)
    assert len(messages)==2

def test_ack_accepts_exact_attempt_url_and_rejects_other_attempt(monkeypatch):
    monkeypatch.setattr(wd,'due_windows',lambda now:{})
    s=state();obs=wd.monitor(NOW,s,harness([run(2)]),apply=False)[0]
    import pytest
    with pytest.raises(ValueError):
        wd.acknowledge(s,'detector.yml',obs['observation_id'],'https://github.com/owner/repo/actions/runs/2/attempts/10; logs','operator',NOW)
    wd.acknowledge(s,'detector.yml',obs['observation_id'],'https://github.com/owner/repo/actions/runs/2/attempts/1; log reviewed','operator',NOW)
    messages=[]
    wd.monitor(NOW,s,harness([run(2)]),lambda **kw:messages.append(kw),True)
    assert messages==[]
    wd.monitor(NOW,s,harness([run(3,0,'success'),run(2)]),lambda **kw:messages.append(kw),True)
    assert len(messages)==1 and s['incidents']['detector.yml']['resolved']


def test_failure_watermark_never_regresses(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state()
    for runs in ([run(30, 1)], [run(10, 5)], [run(20, 3, 'success')]):
        wd.monitor(NOW, s, harness(runs), apply=False)
    assert s['incidents']['detector.yml']['last_failure']['id'] == 30
    assert s['incidents']['detector.yml']['observation']['status'] == 'failed'


def test_records_failure_alongside_first_active_observation(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state()
    result = wd.monitor(NOW, s, harness([run(40, 0, None, 'in_progress'), run(30, 1)]), apply=False)
    assert result[0]['status'] == 'running'
    assert s['incidents']['detector.yml']['last_failure']['id'] == 30
    result = wd.monitor(NOW, s, harness([run(20, 3, 'success')]), apply=False)
    assert result[0]['status'] == 'failed'


def test_actual_attempt_timing_controls_selection_watermark_and_recovery(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    failure = dict(run(10, 5), run_attempt=2, run_started_at=run(0, 1)['created_at'])
    success = dict(run(20, 3, 'success'), updated_at=NOW.isoformat())
    assert wd.diagnose([success, failure], SINCE, NOW) == ('failed', failure)
    assert wd.diagnose([failure], NOW-timedelta(hours=2), NOW) == ('failed', failure)
    active = dict(failure, status='in_progress', conclusion=None)
    assert wd.diagnose([active], SINCE, NOW)[0] == 'running'
    s = state()
    wd.monitor(NOW, s, harness([failure, success]), apply=False)
    wd.monitor(NOW, s, harness([run(30, 2)]), apply=False)
    assert s['incidents']['detector.yml']['last_failure']['run_attempt'] == 2
    assert wd.monitor(NOW, s, harness([success]), apply=False)[0]['status'] == 'failed'
    recovered = dict(failure, run_attempt=3, conclusion='success', run_started_at=NOW.isoformat())
    assert wd.monitor(NOW, s, harness([recovered]), apply=False)[0]['status'] == 'healthy'


def test_failure_observation_and_alert_separate_incident_from_attempt(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state(); messages = []
    failure = dict(run(10, 100), run_attempt=2, run_started_at=run(0, 1)['created_at'])
    obs = wd.monitor(NOW, s, harness([failure]), lambda **kw: messages.append(kw['message']), True)[0]
    assert obs['attempt_started_at'] == failure['run_started_at']
    assert obs['incident_started_at'] == SINCE.isoformat()
    assert 'Geçmiş olay başlangıcı: '+SINCE.isoformat() in messages[0]
    assert 'Çalışma denemesi başlangıcı: '+failure['run_started_at'] in messages[0]


def test_intervening_verified_success_archives_old_episode_once(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state(); messages = []
    s['daily_repairs'] = {NOW.date().isoformat(): 4}
    wd.monitor(NOW, s, harness([run(10, 5)]), lambda **kw: messages.append(kw), True)
    old = s['incidents']['detector.yml']
    old['attempts'] = 2
    wd.acknowledge(s, 'detector.yml', old['observation']['observation_id'],
                   'run:10:attempt:1; reviewed logs', 'operator', NOW)
    result = wd.monitor(NOW, s, harness([run(30), run(20, 3, 'success'), run(10, 5)]),
                        lambda **kw: messages.append(kw), True)
    archived = s['incident_history']['detector.yml'][0]
    assert archived['resolved'] and archived['recovery']['run_id'] == 20
    assert archived['last_failure']['id'] == 10 and archived['attempts'] == 2
    assert archived['acknowledgement']['run_id'] == 10
    fresh = s['incidents']['detector.yml']
    assert fresh['since'] == run(30)['created_at']
    assert fresh['attempts'] == 0 and fresh['last_failure']['id'] == 30
    assert 'acknowledgement' not in fresh
    assert result[0]['status'] == 'failed' and result[0]['verification'] == 'pending_production'
    assert s['daily_repairs'][NOW.date().isoformat()] == 4
    assert len(messages) == 2  # no present-tense recovery alert
    wd.monitor(NOW, s, harness([run(30), run(20, 3, 'success'), run(10, 5)]),
               lambda **kw: messages.append(kw), True)
    assert len(s['incident_history']['detector.yml']) == 1 and len(messages) == 2


def test_episode_split_requires_complete_window_and_no_concurrent_attempt(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    import copy
    baseline = state()
    wd.monitor(NOW, baseline, harness([run(10, 5)]), apply=False)
    for scenario in ('skipped', 'older', 'omitted', 'truncated', 'active', 'equal_time'):
        s = copy.deepcopy(baseline)
        success = run(20, 3, 'success')
        runs = [run(30), success, run(10, 5)]
        if scenario == 'older': success['created_at'] = run(0, 6)['created_at']
        if scenario == 'equal_time': success['created_at'] = run(30)['created_at']
        if scenario == 'omitted': runs.pop()
        if scenario == 'active': runs.append(run(40, 4, None, 'in_progress'))
        base_fetch = harness(runs, 'skipped' if scenario == 'skipped' else 'success')
        def fetch(endpoint, method='GET', payload=None):
            result = base_fetch(endpoint, method, payload)
            if scenario == 'truncated' and 'workflow_runs' in result: result['total_count'] = 101
            return result
        wd.monitor(NOW, s, fetch, apply=False)
        assert not s.get('incident_history'), scenario
        assert s['incidents']['detector.yml']['since'] == SINCE.isoformat(), scenario


def test_episode_reruns_use_attempt_time_and_attempt_specific_core(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state()
    failure = dict(run(10, 100), run_attempt=2, run_started_at=run(0, 5)['created_at'])
    success = dict(run(10, 100, 'success'), run_attempt=3, run_started_at=run(0, 3)['created_at'])
    new_failure = dict(run(30, 200), run_started_at=run(0, 1)['created_at'])
    wd.monitor(NOW, s, harness([failure]), apply=False)
    endpoints = []
    base_fetch = harness([new_failure, success, failure])
    def fetch(endpoint, method='GET', payload=None):
        endpoints.append(endpoint)
        return base_fetch(endpoint, method, payload)
    wd.monitor(NOW, s, fetch, apply=False)
    assert 'actions/runs/10/attempts/3/jobs' in endpoints
    assert s['incidents']['detector.yml']['since'] == new_failure['run_started_at']
    assert s['incident_history']['detector.yml'][0]['recovery']['run_attempt'] == 3


def test_resolved_episode_audit_survives_later_new_failure(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {'detector.yml': SINCE})
    s = state(); messages = []
    wd.monitor(NOW, s, harness([run(10, 5)]), lambda **kw: messages.append(kw), True)
    old = s['incidents']['detector.yml']; old['attempts'] = 2
    wd.acknowledge(s, 'detector.yml', old['observation']['observation_id'],
                   'run:10:attempt:1; reviewed logs', 'operator', NOW)
    wd.monitor(NOW, s, harness([run(20, 3, 'success'), run(10, 5)]), lambda **kw: messages.append(kw), True)
    wd.monitor(NOW, s, harness([run(30), run(20, 3, 'success'), run(10, 5)]), lambda **kw: messages.append(kw), True)
    archived = s['incident_history']['detector.yml'][0]
    assert archived['attempts'] == 2 and archived['acknowledgement']['run_id'] == 10
    assert archived['recovery']['run_id'] == 20
    assert s['incidents']['detector.yml']['since'] == run(30)['created_at']
    wd.monitor(NOW, s, harness([run(30)]), lambda **kw: messages.append(kw), True)
    assert len(s['incident_history']['detector.yml']) == 1


def test_observed_four_green_skips_retain_september_incident(monkeypatch):
    import json
    import copy
    records = json.loads(Path(__file__).with_name('watchdog_skipped_records.json').read_text())
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    failure = json.loads(Path(__file__).with_name('watchdog_failed_record.json').read_text())
    s = state(); s['incidents']['detector.yml']['since'] = '2026-09-28T21:15:00+00:00'
    original = copy.deepcopy(s['incidents']['detector.yml'])
    def fetch(endpoint, method='GET', payload=None):
        assert method == 'GET'
        if endpoint.endswith('/jobs'):
            ident = int(endpoint.split('/')[2])
            steps = next((r['core'] for r in records if r['run']['id'] == ident), [])
            return {'jobs': [{'steps': steps}]}
        return {'workflow_runs': [failure]+[r['run'] for r in records]}
    result = wd.monitor(datetime(2026, 10, 6, 3, tzinfo=timezone.utc), s, fetch, apply=False)
    assert result[0]['status'] == 'failed' and result[0]['run_id'] == failure['id']
    assert result[0]['incident_started_at'] == original['since']
    assert not s.get('incident_history') and not s['incidents']['detector.yml'].get('resolved')


def test_multiple_intervening_recoveries_archive_each_bounded_episode(monkeypatch):
    import copy
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state(); messages = []
    f1, s1, f2, s2, f3 = (dict(run(identity, age, outcome), head_sha=f'sha-{identity}')
                          for identity, age, outcome in (
                              (10, 5, 'failure'), (20, 4, 'success'),
                              (30, 3, 'failure'), (40, 2, 'success'), (50, 1, 'failure')))
    wd.monitor(NOW, s, harness([f1]), lambda **kw: messages.append(kw), True)
    original = s['incidents']['detector.yml']
    original.update(attempts=2, last_attempt=(NOW-timedelta(minutes=30)).isoformat(),
                    repair_requested=(NOW-timedelta(minutes=30)).isoformat())
    wd.acknowledge(s, 'detector.yml', original['observation']['observation_id'],
                   'run:10:attempt:1; reviewed logs', 'operator', NOW)
    original = copy.deepcopy(original)
    s['daily_repairs'] = {NOW.date().isoformat(): 4}
    runs = [f3, s2, f2, s1, f1]
    result = wd.monitor(NOW, s, harness(runs), lambda **kw: messages.append(kw), True)
    history = s['incident_history']['detector.yml']
    assert len(history) == 2
    for archived, failure, success, since in (
            (history[0], f1, s1, SINCE.isoformat()),
            (history[1], f2, s2, f2['created_at'])):
        assert archived['since'] == since
        assert archived['last_failure'] == failure
        assert archived['resolved'] == NOW.isoformat()
        assert archived['recovery'] == {
            'workflow': 'detector.yml', 'status': 'healthy',
            'verification': 'verified_production', 'run_id': success['id'],
            'run_attempt': 1, 'head_sha': success['head_sha'],
            'attempt_started_at': success['created_at'],
            'verified_at': NOW.isoformat(), 'historical': True}
    assert {key: history[0][key] for key in original} == original
    assert history[1]['attempts'] == 0
    for key in ('acknowledgement', 'observation', 'last_attempt', 'repair_requested', 'alerted'):
        assert key not in history[1]  # no invented monitoring or repair history
    current = s['incidents']['detector.yml']
    assert current['since'] == f3['created_at'] and current['last_failure'] == f3
    assert current['attempts'] == 0
    assert not {'resolved', 'recovery', 'acknowledgement', 'last_attempt', 'repair_requested'} & current.keys()
    assert result[0]['status'] == 'failed' and result[0]['verification'] == 'pending_production'
    assert len(messages) == 2 and all('✅' not in m['message'] for m in messages)
    snapshot = copy.deepcopy(s)
    wd.monitor(NOW, s, harness(runs), lambda **kw: messages.append(kw), True)
    assert s == snapshot and len(messages) == 2
    monkeypatch.setattr(wd, 'due_windows', lambda now: {'detector.yml': SINCE})
    monkeypatch.setattr(wd, 'repair_plan', lambda *args: 'rerun')
    result = wd.monitor(NOW, s, harness(runs), apply=False)
    assert result[0]['reason'] == 'daily_attempt_limit' and not result[0]['repair_eligible']
    assert s['daily_repairs'] == {NOW.date().isoformat(): 4}
    s['daily_repairs'][NOW.date().isoformat()] = 3
    current['last_attempt'] = (NOW-timedelta(minutes=30)).isoformat()
    result = wd.monitor(NOW, s, harness(runs), apply=False)
    assert result[0]['reason'] == 'repair_cooldown' and not result[0]['repair_eligible']
    assert len(s['incident_history']['detector.yml']) == 2


def test_multiple_verified_recoveries_archive_each_episode_and_deduplicate(monkeypatch):
    import copy
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state(); messages = []; endpoints = []
    s['daily_repairs'] = {NOW.date().isoformat(): 4}
    f1, s1, f2, s2, f3 = (run(10, 5), run(20, 4, 'success'), run(30, 3),
                           run(40, 2, 'success'), run(50, 1))
    wd.monitor(NOW, s, harness([f1]), lambda **kw: messages.append(kw), True)
    old = s['incidents']['detector.yml']
    old['attempts'] = 2
    old['last_attempt'] = (NOW-timedelta(hours=6)).isoformat()
    wd.acknowledge(s, 'detector.yml', old['observation']['observation_id'],
                   'run:10:attempt:1; reviewed logs', 'operator', NOW)
    original = copy.deepcopy(old)
    base_fetch = harness([f3, s2, f2, s1, f1])
    def fetch(endpoint, method='GET', payload=None):
        endpoints.append(endpoint)
        return base_fetch(endpoint, method, payload)
    result = wd.monitor(NOW, s, fetch, lambda **kw: messages.append(kw), True)
    assert 'actions/runs/20/attempts/1/jobs' in endpoints
    assert 'actions/runs/40/attempts/1/jobs' in endpoints
    history = s['incident_history']['detector.yml']
    assert len(history) == 2
    first, second = history
    assert first['since'] == SINCE.isoformat()
    assert first['last_failure'] == f1 and first['recovery']['run_id'] == s1['id']
    for key in ('attempts', 'last_attempt', 'acknowledgement', 'observation', 'alerted'):
        assert first[key] == original[key]
    assert second['since'] == f2['created_at']
    assert second['last_failure'] == f2 and second['recovery']['run_id'] == s2['id']
    assert second['attempts'] == 0 and 'acknowledgement' not in second
    for episode, success in ((first, s1), (second, s2)):
        assert episode['resolved'] == NOW.isoformat()
        assert episode['recovery']['verification'] == 'verified_production'
        assert episode['recovery']['attempt_started_at'] == success['created_at']
        assert episode['recovery']['historical'] is True
    fresh = s['incidents']['detector.yml']
    assert fresh['since'] == f3['created_at'] and fresh['last_failure'] == f3
    assert fresh['attempts'] == 0 and 'acknowledgement' not in fresh
    assert not fresh.get('resolved')
    assert result[0]['incident_started_at'] == f3['created_at']
    assert result[0]['status'] == 'failed' and result[0]['verification'] == 'pending_production'
    assert s['daily_repairs'] == {NOW.date().isoformat(): 4}
    assert len(messages) == 2
    snapshot = copy.deepcopy(s)
    wd.monitor(NOW, s, fetch, lambda **kw: messages.append(kw), True)
    assert s == snapshot and len(messages) == 2


def resolved_chronology(monkeypatch):
    monkeypatch.setattr(wd, 'due_windows', lambda now: {'detector.yml': SINCE})
    s = state()
    s['daily_repairs'] = {NOW.date().isoformat(): 4}
    f1 = dict(run(10, 8), run_attempt=2)
    s1 = dict(run(20, 6, 'success'), run_attempt=3)
    wd.monitor(NOW, s, harness([f1]), apply=True, send=lambda **kw: None)
    old = s['incidents']['detector.yml']
    old['attempts'] = 2
    wd.acknowledge(s, 'detector.yml', old['observation']['observation_id'],
                   'run:10:attempt:2; reviewed logs', 'operator', NOW)
    wd.monitor(NOW, s, harness([s1, f1]), apply=True, send=lambda **kw: None)
    return s, f1, s1


def test_resolved_chronology_first_new_failure_and_dedup(monkeypatch):
    s, f1, s1 = resolved_chronology(monkeypatch)
    f2, f3 = run(30, 4), run(50, 1)
    messages = []
    for _ in range(2):
        wd.monitor(NOW, s, harness([f3, f2, s1, f1]),
                   send=lambda **kw: messages.append(kw), apply=True)
    assert s['incidents']['detector.yml']['since'] == f2['created_at']
    assert s['incidents']['detector.yml']['last_failure']['id'] == 50
    assert s['incidents']['detector.yml']['attempts'] == 0
    assert 'acknowledgement' not in s['incidents']['detector.yml']
    history = s['incident_history']['detector.yml']
    assert len(history) == 1 and history[0]['attempts'] == 2
    assert history[0]['acknowledgement']['run_attempt'] == 2
    assert history[0]['recovery']['run_attempt'] == 3
    assert s['daily_repairs'][NOW.date().isoformat()] == 4
    assert len(messages) == 1


def test_resolved_chronology_intervening_episode_and_consecutive_successes(monkeypatch):
    s, f1, s1 = resolved_chronology(monkeypatch)
    f2, s2, f3 = run(30, 4), run(40, 3, 'success'), run(50, 1)
    runs = [f3, run(45, 2, 'success'), s2, f2, run(25, 5, 'success'), s1, f1]
    for _ in range(2):
        wd.monitor(NOW, s, harness(runs), apply=False)
    history = s['incident_history']['detector.yml']
    assert [(h['last_failure']['id'], h['recovery']['run_id']) for h in history] == [(10, 20), (30, 40)]
    assert history[1]['since'] == f2['created_at']
    assert s['incidents']['detector.yml']['since'] == f3['created_at']


def test_resolved_chronology_requires_present_complete_recovery_boundary(monkeypatch):
    import copy
    baseline, f1, s1 = resolved_chronology(monkeypatch)
    for scenario in ('omitted', 'truncated', 'skipped', 'wrong_attempt', 'active'):
        s = copy.deepcopy(baseline)
        boundary = dict(s1)
        if scenario == 'wrong_attempt': boundary['run_attempt'] = 4
        runs = [run(50, 1), run(40, 2, 'success'), run(30, 4), boundary, f1]
        if scenario == 'omitted': runs.remove(boundary)
        if scenario == 'active': runs.append(run(60, 0, None, 'in_progress'))
        base = harness(runs, 'skipped' if scenario == 'skipped' else 'success')
        def fetch(endpoint, method='GET', payload=None):
            result = base(endpoint, method, payload)
            if scenario == 'truncated' and 'workflow_runs' in result:
                result['total_count'] = 101
            return result
        wd.monitor(NOW, s, fetch, apply=False)
        assert len(s['incident_history']['detector.yml']) == 1, scenario
        assert s['incident_history']['detector.yml'][0]['recovery']['run_id'] == 20


def test_resolved_chronology_ambiguous_intermediate_success_keeps_failures(monkeypatch):
    s, f1, s1 = resolved_chronology(monkeypatch)
    f2, f3 = run(30, 4), run(50, 1)
    ambiguous_failure = run(41, 3)
    wd.monitor(NOW, s, harness([f3, ambiguous_failure, run(40, 3, 'success'), f2, s1, f1]), apply=False)
    assert len(s['incident_history']['detector.yml']) == 1
    assert s['incidents']['detector.yml']['since'] == f2['created_at']


def test_intermediate_equal_time_recovery_fails_closed(monkeypatch):
    import copy
    monkeypatch.setattr(wd, 'due_windows', lambda now: {})
    s = state()
    f1, tied_failure, success, f3 = run(10, 5), run(30, 3), run(20, 3, 'success'), run(40, 1)
    wd.monitor(NOW, s, harness([f1]), apply=False)
    s['incidents']['detector.yml']['attempts'] = 2
    original = copy.deepcopy(s['incidents']['detector.yml'])
    wd.monitor(NOW, s, harness([f3, tied_failure, success, f1]), apply=False)
    assert not s.get('incident_history')
    assert s['incidents']['detector.yml']['attempts'] == 2
    assert s['incidents']['detector.yml']['since'] == original['since']
    assert s['incidents']['detector.yml']['last_failure'] == f3
