"""Persisted research with source gaps may continue next session, never replay."""
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import pytest
import yaml
from tests.test_local_runner import load_guard, env
from tests.test_runner_partial import git


def fixture(tmp_path):
    workspace=tmp_path/'checkout';workspace.mkdir();remote=tmp_path/'remote.git'
    subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
    git(workspace,'init','-b','main');git(workspace,'config','user.name','Test');git(workspace,'config','user.email','test@example.invalid')
    (workspace/'state').mkdir()
    book={'last_updated':'old','cash_usd':10,'positions':[],'trade_history':[]}
    (workspace/'portfolio.json').write_text(json.dumps(book))
    (workspace/'theses.json').write_text('{}');(workspace/'DECISION_LOG.md').write_text('# Record\n')
    git(workspace,'add','.');git(workspace,'commit','-m','initial');sha=git(workspace,'rev-parse','HEAD');git(workspace,'remote','add','origin',str(remote))
    guard=load_guard();root=tmp_path/'journal'
    context={**env(),'GITHUB_WORKFLOW':'Weekly Portfolio Round','GITHUB_SHA':sha,'GITHUB_WORKSPACE':str(workspace),'GITHUB_OUTPUT':str(tmp_path/'hook')}
    guard.start(root,context);guard.checkpoint_checkout(root,context)
    book['last_updated']='current';(workspace/'portfolio.json').write_text(json.dumps(book))
    (workspace/'weekly_data.json').write_text(json.dumps({'AMD':{'analyst_revisions':{'status':'incomplete','estimates_status':'ok'}}}))
    (workspace/'state/weekly_plan.json').write_text(json.dumps({'round_id':'research','status':'pending','created_at':datetime.now(timezone.utc).isoformat(),'proposal':{'decisions':[]}}))
    git(workspace,'add','.');git(workspace,'commit','-m','persist research');git(workspace,'push','origin','main')
    steps={key:{'outcome':'success','conclusion':'success','outputs':{}} for key in guard.WEEKLY_PARTIAL_STEP_IDS}
    for key in ('corporate_commit','corporate_notify','exit_notify','prompt_health'):
        steps[key].update(outcome='skipped',conclusion='skipped')
    steps['analyst_health'].update(outcome='failure',conclusion='failure');steps['corporate']['outputs']={'changed':'false'}
    claim=Path(context['GITHUB_OUTPUT']).read_text().strip().split('=',1)[1]
    steps['a26c83da3a754645a5cf6f506cd1caa3']={'outputs':{'local_runner_claim':claim},'outcome':'success','conclusion':'success'}
    context['LOCAL_RUNNER_STEPS']=json.dumps(steps)
    return guard,root,context,steps,workspace


def test_persisted_weekend_research_preserves_failure_and_permits_new_run(tmp_path):
    guard,root,context,steps,workspace=fixture(tmp_path)
    guard.finish(root,context,'failure')
    receipt=json.loads((root/'101.json').read_text())
    assert receipt['status']=='failure'
    assert receipt['release_reason']=='persisted-weekly-research-partial'
    assert receipt['partial_evidence']['source_gaps']==['AMD']
    assert not (root/'active.json').exists()
    assert json.loads((workspace/'state/weekly_plan.json').read_text())['status']=='pending'
    with pytest.raises(RuntimeError,match='already'):
        guard.start(root,{**context,'GITHUB_RUN_ATTEMPT':'2'})
    guard.start(root,{**context,'GITHUB_RUN_ID':'102'})


@pytest.mark.parametrize('mutation',['model','notification','unknown_step','corporate','portfolio','thesis','pending_execution','dirty','unpublished','empty_gaps','missing_baseline','missing_hook','cancelled'])
def test_ambiguous_weekly_effects_keep_lock(tmp_path,mutation):
    guard,root,context,steps,workspace=fixture(tmp_path);outcome='failure'
    if mutation in ('model','notification'):
        steps['weekly_decision' if mutation=='model' else 'report_notify'].update(outcome='failure',conclusion='failure')
    elif mutation=='unknown_step':steps['unexpected']=steps['audit'].copy()
    elif mutation=='corporate':steps['corporate']['outputs']['changed']='true'
    elif mutation=='portfolio':(workspace/'portfolio.json').write_text('{"cash_usd":11}')
    elif mutation=='thesis':(workspace/'theses.json').write_text('{"AMD":{}}')
    elif mutation=='pending_execution':(workspace/'state/pending_decision.json').write_text('{"action":"BUY"}')
    elif mutation=='dirty':(workspace/'unknown.txt').write_text('unresolved')
    elif mutation=='unpublished':git(workspace,'remote','set-url','origin',str(tmp_path/'missing'))
    elif mutation=='empty_gaps':(workspace/'weekly_data.json').write_text('{}')
    elif mutation=='missing_baseline':steps.pop('baseline')
    elif mutation=='missing_hook':steps.pop('a26c83da3a754645a5cf6f506cd1caa3')
    elif mutation=='cancelled':outcome='cancelled'
    if mutation in ('portfolio','thesis','pending_execution','empty_gaps'):
        git(workspace,'add','.');git(workspace,'commit','-m','unsafe');git(workspace,'push','origin','main')
    context['LOCAL_RUNNER_STEPS']=json.dumps(steps)
    guard.finish(root,context,outcome)
    assert (root/'active.json').exists()
    assert 'release_reason' not in json.loads((root/'101.json').read_text())


def test_weekly_workflow_explicit_step_contract_matches_guard():
    guard=load_guard();root=Path(__file__).resolve().parents[1]
    steps=yaml.safe_load((root/'.github/workflows/weekly.yml').read_text())['jobs']['round']['steps']
    assert {s['id'] for s in steps if s['id']!='finalize'}==guard.WEEKLY_PARTIAL_STEP_IDS
    assert next(s for s in steps if s['id']=='finalize')['env']['LOCAL_RUNNER_STEPS']=='${{ toJSON(steps) }}'
