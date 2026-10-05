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
