"""Decision state transitions, source-bound monitor updates and event replay protection."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import decision_lifecycle as dl
import detector
import evidence
import execute_trade as et
import reassess
from tests.test_execute_trade import portfolio, live, decision

NOW=datetime(2026,9,28,15,tzinfo=timezone.utc)
NEWS={'news:test':{'symbol':'MU','text':'The company revised its operating outlook following a confirmed reduction in customer demand and margins.','published_at':NOW.isoformat(),'url':'https://example.org/result'}}

def thesis():
    return {'thesis_summary':'Demand supports the position.','claims':[{'id':'MU-1','text':'Demand supports the position.','status':'valid',
        'conditions':[{'type':'price_below','value':900,'severity':'thesis'}]}]}

def data():
    result=live();result['MU']['source_documents']=copy.deepcopy(NEWS)
    return result

def monitor(old=None):
    old=old or thesis()
    claims=[{k:copy.deepcopy(c[k]) for k in ('id','text','status','conditions')} for c in old['claims']]
    return {'claims':claims,'next_review_at':(NOW+timedelta(days=1)).isoformat(),
        'falsifier_condition':{'claim_id':'MU-1','condition_index':0},
        'change_reason':'Preserve the current conditions; new evidence will be checked at the next review.',
        'evidence_ids':['MU.price']}

class MonitorContract(unittest.TestCase):
    def validate(self,m,old=None,**kwargs):
        return dl.validate_monitoring(m,'MU',old or thesis(),data(),evidence.ledger(data(),NOW.isoformat(),'test'),NOW,**kwargs)

    def test_valid_contract_keeps_threshold_and_revision(self):
        result=self.validate(monitor())
        self.assertTrue(result['revision']);self.assertEqual(result['claims'],thesis()['claims'])
        self.assertIn('MU.price',result['evidence_fingerprints'])

    def test_missing_executable_falsifier_and_past_or_naive_deadlines_fail(self):
        for change in ({'falsifier_condition':{'claim_id':'OTHER','condition_index':0}},
                       {'next_review_at':NOW.isoformat()}, {'next_review_at':'2026-09-29T15:00:00'},
                       {'next_review_at':(NOW+timedelta(days=8)).isoformat()}, {'evidence_ids':['MU.fabricated']}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.validate(dict(monitor(),**change))

    def test_price_only_cannot_loosen_threshold_or_stop(self):
        m=monitor();m['claims'][0]['conditions'][0]['value']=800
        with self.assertRaisesRegex(ValueError,'non-price'):self.validate(m)
        with self.assertRaisesRegex(ValueError,'non-price'):self.validate(monitor(),stop_before=900,stop_after=800)

    def test_new_nonprice_evidence_allows_explained_change_but_not_its_reuse(self):
        m=monitor();m['claims'][0]['conditions'][0]['value']=850;m['evidence_ids']=['news:test']
        approved=self.validate(m)
        old=thesis();old['claims']=approved['claims'];old['monitoring']=approved
        m=monitor(old);m['evidence_ids']=['news:test'];m['claims'][0]['conditions'][0]['value']=800
        with self.assertRaisesRegex(ValueError,'non-price'):self.validate(m,old)

    def test_numeric_dates_are_valid_parameters_but_numeric_prose_is_rejected(self):
        facts=evidence.ledger(data(),NOW.isoformat(),'test')
        self.assertEqual(evidence.render_payload({'monitoring':monitor()},facts)['monitoring']['next_review_at'],monitor()['next_review_at'])
        m=monitor();m['change_reason']='Revenue increased 123456 percent.'
        with self.assertRaises(ValueError):evidence.render_payload({'monitoring':m},facts)

    def test_claim_ids_in_prose_are_labels_but_unbound_numbers_are_not(self):
        facts=evidence.ledger(data(),NOW.isoformat(),'test')
        m=monitor();m['change_reason']='MU-1 retains its conditions.'
        self.assertIn('MU-1',evidence.render_payload({'monitoring':m},facts)['monitoring']['change_reason'])
        m['change_reason']='MU-1 now uses price_below_sma50_pct.'
        evidence.render_payload({'monitoring':m},facts)
        for text in ('MU-1 revenue is 123456.', 'MU-999 proves growth.'):
            m['change_reason']=text
            with self.assertRaises(ValueError):evidence.render_payload({'monitoring':m},facts)

    def test_history_preserves_old_and_new_once(self):
        change={'before':thesis(),'after':dict(thesis(),monitoring=monitor())}
        history=dl.history_update({},[change,change]);self.assertEqual(len(history),1)
        self.assertNotIn('monitoring',next(iter(history.values()))['before'])

class TriggerTransitions(unittest.TestCase):
    def test_single_weak_claim_does_not_escalate_but_invalid_does(self):
        old=thesis();old['claims'][0]['status']='weakened'
        self.assertIsNone(dl.escalation('MU',old,{'MU-1':'valid'}))
        old['claims'][0]['status']='invalid'
        self.assertEqual(dl.escalation('MU',old,{'MU-1':'valid'})['severity'],'thesis')
        self.assertIsNone(dl.escalation('MU',old,{'MU-1':'invalid'}))

    def test_two_weak_claims_open_whole_thesis_review(self):
        old=thesis();old['claims'][0]['status']='weakened'
        other=copy.deepcopy(old['claims'][0]);other['id']='MU-2';old['claims'].append(other)
        self.assertIsNotNone(dl.escalation('MU',old,{'MU-1':'weakened','MU-2':'valid'}))

    def test_due_hold_review_ignores_price_cooldown_and_does_not_trade(self):
        old=thesis();old['monitoring']=dict(monitor(),next_review_at=NOW.isoformat())
        report=detector.run({'MU':old},data(),{}, {},{'thesis:MU':NOW.isoformat()},NOW,assess_news=False)
        self.assertEqual(report['code'],20)
        self.assertEqual(report['triggered'][0]['condition_type'],'review_deadline')
        self.assertNotIn('decisions',report)

    def test_legacy_migration_requests_review_without_inventing_conditions(self):
        old=thesis();before=copy.deepcopy(old)
        report=detector.run({'MU':old},data(),{}, {},{},NOW,assess_news=False,initialize_monitors=True)
        self.assertEqual(report['code'],20);self.assertEqual(old,before)

    def test_failed_legacy_migration_is_deduplicated_and_retried_daily(self):
        migration={'symbol':'MU','claim_id':'monitoring_migration','severity':'thesis',
                   'condition_type':'monitoring_migration','cooldown_key':'migration:MU',
                   'trigger':'Legacy decision needs an executable review.'}
        old=thesis();old['pending_review']=copy.deepcopy(migration)
        initial=detector.run({'MU':old},data(),{}, {},{},NOW,assess_news=False,initialize_monitors=True)
        self.assertEqual([item['condition_type'] for item in initial['triggered']],['monitoring_migration'])

        cooldown=reassess.record_failed_migration_retries({},
            {'assessment_errors':['MU'],'triggered':[migration]},NOW)
        retry=detector.run({'MU':old},data(),{}, {},cooldown,NOW+timedelta(hours=12),
                           assess_news=False,initialize_monitors=True)
        self.assertEqual(retry['triggered'],[])
        daily=detector.run({'MU':old},data(),{}, {},cooldown,NOW+timedelta(hours=24),
                           assess_news=False,initialize_monitors=True)
        self.assertEqual([item['condition_type'] for item in daily['triggered']],['monitoring_migration'])

    def test_positive_price_signal_needs_confirmation(self):
        old=thesis();old['claims'][0]['conditions']=[{'type':'price_above','value':800,'severity':'thesis'}]
        first=detector.run({'MU':old},data(),{}, {},{},NOW,assess_news=False)
        second=detector.run({'MU':old},data(),{},first['conditions'],{},NOW,assess_news=False)
        self.assertEqual(first['code'],0);self.assertEqual(second['code'],20)

    def test_moving_average_updates_without_rewriting_threshold(self):
        condition={'type':'price_below_sma50_pct','value':0,'severity':'thesis'}
        rows={'MU':{'price':100,'sma50':90}}
        first=detector.measure(condition,'MU',rows,None,NOW.date())
        rows['MU']['sma50']=110
        second=detector.measure(condition,'MU',rows,None,NOW.date())
        self.assertGreater(first[0],0);self.assertLess(second[0],0)
        self.assertEqual(first[1],second[1])

    def test_positive_news_is_a_review_trigger_not_a_buy(self):
        from claim_evidence import documents
        news=[{'symbol':'MU','title':'Report','text':NEWS['news:test']['text'],'publishedDate':NOW.isoformat(),'url':'https://example.org/report'}]
        sources=documents('MU',news)
        report={'impact':'supports','claim_ids':['thesis_summary'],'citations':[{'source_id':'N1'}],
                'reasoning':'Evidence supports the thesis.','counterevidence':'Persistence remains uncertain.','uncertainty':'Future outcomes are unknown.'}
        def response(*args,**kwargs):kwargs['response_validator'](report);return report,'ok'
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':'test'}),patch.object(reassess,'call_llm',side_effect=response):
            triggered,result=detector.check_news_shock('MU','Thesis',news)
        self.assertTrue(triggered);self.assertNotIn('action',result)

class EventExecution(unittest.TestCase):
    def test_new_verified_event_can_follow_trim_but_same_event_cannot_replay(self):
        book=portfolio();rows=live();trade=decision('TRIM',shares=2);trade['event_ids']=['news-a']
        locks={'2026-09-28:MU:SELL':NOW.isoformat()}
        self.assertTrue(et.validate(trade,book,rows,True,locks,NOW.date(),authorized_events=['news-a'])[0])
        locks['event:MU:news-a']=NOW.isoformat()
        self.assertFalse(et.validate(trade,book,rows,True,locks,NOW.date(),authorized_events=['news-a'])[0])
        trade['event_ids']=['news-b']
        self.assertTrue(et.validate(trade,book,rows,True,locks,NOW.date(),authorized_events=['news-b'])[0])

    def test_unverified_event_and_closed_session_never_bypass_guards(self):
        trade=decision('TRIM',shares=2);trade['event_ids']=['invented']
        self.assertFalse(et.validate(trade,portfolio(),live(),True,{},NOW.date())[0])
        self.assertFalse(et.validate(trade,portfolio(),live(),False,{},NOW.date(),authorized_events=['invented'])[0])

    def test_news_regrouping_and_republication_cannot_create_another_event(self):
        trigger={'symbol':'MU','news_evidence':{'source_documents':copy.deepcopy(NEWS),'citations':[{'source_id':'news:test','quote':'excerpt'}]}}
        before=dl.material_events(trigger,{})
        trigger['news_evidence']['source_documents']['news:unrelated']={'text':'A different uncited article.'}
        self.assertEqual(before,dl.material_events(trigger,{}))
        trigger['news_evidence']['source_documents']['news:republished']=trigger['news_evidence']['source_documents'].pop('news:test')
        trigger['news_evidence']['citations'][0]['source_id']='news:republished'
        self.assertEqual(before,dl.material_events(trigger,{}))

    def test_changed_threshold_does_not_create_new_report_identity(self):
        rows={'MU':{'fundamental_research':{'facts':{'operating_margin_pct':{'as_of':'2026-06-30','value':15,'unit':'%'}}}}}
        trigger={'symbol':'MU','condition_type':'fundamental_below','metric':'operating_margin_pct','threshold':20}
        before=dl.material_event(trigger,rows);trigger['threshold']=25
        self.assertEqual(before,dl.material_event(trigger,rows))
        rows['MU']['fundamental_research']['facts']['operating_margin_pct']['as_of']='2026-09-30'
        self.assertNotEqual(before,dl.material_event(trigger,rows))

    def test_fill_ledger_retains_identity_for_crash_recovery(self):
        book=portfolio();trade=decision('TRIM',shares=2);trade['event_ids']=['news-a']
        ok,_,details=et.validate(trade,book,live(),True,{},NOW.date(),authorized_events=['news-a'])
        self.assertTrue(ok)
        self.assertEqual(et.execute(trade,book,details,NOW)['event_ids'],['news-a'])

class CascadeEndToEnd(unittest.TestCase):
    def invoke(self,fail_review=False):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        root=Path(temp.name);state=root/'state';state.mkdir()
        old=thesis();old['claims'][0]['conditions'][0]['severity']='claim'
        (root/'theses.json').write_text(json.dumps({'MU':old}));(root/'portfolio.json').write_text(json.dumps(portfolio()))
        report={'lifecycle_version':1,'checked_at':NOW.isoformat(),'market_open':True,'data':data(),
                'triggered':[{'symbol':'MU','claim_id':'MU-1','severity':'claim','condition_type':'price_below','measured':905.4,'threshold':950,'trigger':'Claim evidence changed'}]}
        (state/'violations.json').write_text(json.dumps(report))
        m=monitor();m['evidence_ids']=['news:test'];m['claims'][0]['status']='invalid'
        responses=[{'text':'Demand no longer supports the position.','status':'invalid'},
                   {'thesis_assessment':'The supporting claim failed; review the position.','new_thesis_summary':'The original claim is invalid.',
                    'claim_statuses':{'MU-1':'invalid'},'monitoring':m,
                    'decision':{'action':'HOLD','reasoning':'Wait for fresh confirmation while monitoring the invalid thesis.','falsifier':'A breach of the monitored price condition requires review.'}}]
        reviews=[{'verdict':'supported'}] + [ValueError('Insufficient evidence')]*reassess.MAX_ATTEMPTS if fail_review else [{'verdict':'supported'}]*2
        if fail_review:
            responses += [responses[-1]] * (reassess.MAX_ATTEMPTS - 1)
        with patch.object(reassess,'BASE',str(root)),patch.object(reassess,'THESES_PATH',str(root/'theses.json')),patch.object(reassess,'PORTFOLIO_PATH',str(root/'portfolio.json')),patch.object(reassess,'now_utc',return_value=NOW),patch.dict(os.environ,{'OPENROUTER_API_KEY':'test'}),patch('sys.argv',['reassess','--code','10','--state-dir',str(state)]),patch.object(reassess,'_single_call',side_effect=[(json.dumps(r),False) for r in responses]),patch('claim_evidence.semantic_review',side_effect=reviews):
            self.assertEqual(reassess.main(),0)
        return root,state

    def test_claim_only_run_opens_decision_and_records_before_after(self):
        root,state=self.invoke()
        bundle=json.loads((state/'pending_decision.json').read_text())
        self.assertEqual(bundle['decisions'][0]['action'],'HOLD')
        final=json.loads((root/'theses.json').read_text())['MU']
        self.assertIn('monitoring',final);self.assertNotIn('pending_review',final)
        self.assertEqual(len(json.loads((state/'decision_history.json').read_text())),1)

    def test_failed_deep_review_stays_pending_for_retry_without_trade(self):
        root,state=self.invoke(True)
        self.assertFalse((state/'pending_decision.json').exists())
        final=json.loads((root/'theses.json').read_text())['MU']
        self.assertIn('pending_review',final)
        next_report=detector.run({'MU':final},data(),{}, {},{},NOW,assess_news=False)
        self.assertEqual(next_report['code'],20)

if __name__=='__main__':unittest.main()
