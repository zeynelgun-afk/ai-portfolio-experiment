"""Behavioral tests for typed evidence, atomic weekly execution and bounded repair."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import evidence
import reassess
import watchdog as wd
import weekly_round as wr

SAT = datetime(2026, 10, 3, 8, tzinfo=timezone.utc)
MON = datetime(2026, 9, 28, 16, tzinfo=timezone.utc)
DATA = {'AMD': {'last_price': 100, 'sma50': 80, 'price_date': '2026-10-02', 'earnings_date': None},
        'MU': {'last_price': 50, 'sma50': 45, 'price_date': '2026-10-02'}}
BOOK = {'cash_usd': 100, 'positions': [{'symbol': 'AMD', 'shares': 2, 'cost_usd': 160,
        'entry_price': 80, 'stop_weekly_close': 60}], 'trade_history': []}


def thesis(symbol):
    return {'thesis_summary': 'Demand supports the thesis.', 'claims': [
        {'id': symbol+'-demand', 'text': 'Demand remains sound.', 'status': 'valid',
         'conditions': [{'type': 'price_below', 'value': 60, 'severity': 'thesis'}]}]}


def proposal():
    return {'sections': {k: 'Qualitative explanation.' for k in 'ABCDEF'},
            'decisions': [{'symbol': 'AMD', 'action': 'HOLD', 'new_stop': 70,
                           'reasoning': 'Demand remains strong.', 'falsifier': 'Demand contracts.'}],
            'theses': {'AMD': thesis('AMD')}, 'watchlist': [], 'pending_notes_addressed': True}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.facts = evidence.ledger(DATA, SAT.isoformat(), 'test-measurement')

    def test_renderer_binds_company_metric_date_and_source(self):
        text = evidence.render('Observed {{AMD.last_price}}.', self.facts)
        for term in ('AMD', 'last_price', '100 USD', '2026-10-02', 'test-measurement', 'snapshot'):
            self.assertIn(term, text)

    def test_same_value_cannot_supply_a_different_metric(self):
        with self.assertRaises(ValueError):
            evidence.render('Revenue {{AMD.revenue}}.', self.facts)

    def test_raw_copied_number_is_rejected_even_if_in_sources(self):
        with self.assertRaises(ValueError):
            evidence.render('Revenue is 100.', self.facts)

    def test_old_prose_is_not_a_new_source(self):
        with patch.object(reassess, '_single_call', return_value=(json.dumps({'text':'Market share is 80%.', 'status':'valid'}), False)):
            result, status = reassess.call_llm('test', 'system', 'old claim market share 80%', 'key',
                audit_sources=('market share 80%',), source_ledger=self.facts)
        self.assertIsNone(result)
        self.assertEqual(status, 'invalid_evidence')

    def test_derived_ratio_names_its_exact_operands(self):
        fact = self.facts['AMD.above_sma50_pct']
        self.assertEqual(fact['value'], 25)
        self.assertEqual(fact['operands'], ['AMD.last_price', 'AMD.sma50'])

    def test_no_cross_issuer_reference_in_intraday_scope(self):
        facts = reassess.evidence_for(DATA, {'checked_at':SAT.isoformat()}, 'AMD')
        with self.assertRaises(ValueError):
            evidence.render('{{MU.last_price}}', facts)

    def test_numeric_choices_remain_free(self):
        result = evidence.render_payload({'decision': {'new_stop': 12.345, 'amount_usd':99,
            'reasoning':'Qualitative rationale.'}}, self.facts)
        self.assertEqual(result['decision']['new_stop'],12.345)

    def test_identity_tampering_rejected(self):
        self.facts['AMD.last_price']['symbol'] = 'MU'
        with self.assertRaises(ValueError):
            evidence.render('{{AMD.last_price}}', self.facts)

    def test_missing_timestamp_not_registered(self):
        self.assertEqual(evidence.ledger({'AMD':{'last_price':100}}, None, 'test'), {})


class WeeklyTests(unittest.TestCase):
    def prepare(self, p=None, data=None):
        return wr.prepare(p or proposal(), BOOK, {'_meta':{}}, data or DATA, SAT, '# Log\n')

    def test_hold_records_and_updates_stop_without_trade(self):
        result, theses, log = self.prepare()
        self.assertEqual(result['positions'][0]['stop_weekly_close'],70)
        self.assertEqual(result['trade_history'],[])
        self.assertIn('2026-10-03',result['completed_weekly_rounds'])
        self.assertIn('WEEKLY ROUND',log)
        self.assertEqual(BOOK['positions'][0]['stop_weekly_close'],60)

    def test_sell_then_buy_uses_measured_price_and_proceeds(self):
        p=proposal()
        p['decisions']=[dict(p['decisions'][0],action='SELL'),
            dict(p['decisions'][0],symbol='MU',action='BUY',amount_usd=300)]
        p['theses']={'MU':thesis('MU')}
        result,_,_=self.prepare(p)
        self.assertEqual(result['cash_usd'],0)
        self.assertEqual(result['positions'][0]['shares'],6)
        self.assertTrue(all(r['source']=='weekly_autonomous' for r in result['trade_history']))
        self.assertEqual(result['trade_history'][1]['price'],50)

    def test_overspend_rejects_whole_batch(self):
        p=proposal();p['decisions'][0].update(action='BUY',amount_usd=101)
        with self.assertRaises(ValueError):self.prepare(p)
        self.assertEqual(BOOK['cash_usd'],100)

    def test_stale_close_cannot_fill(self):
        p=proposal();p['decisions'][0].update(action='SELL')
        data=copy.deepcopy(DATA);data['AMD']['price_date']='2026-10-01'
        with self.assertRaises(ValueError):self.prepare(p,data)

    def test_missing_accountability_rejected(self):
        p=proposal();del p['sections']['F']
        with self.assertRaises(ValueError):self.prepare(p)

    def test_duplicate_decision_rejected(self):
        p=proposal();p['decisions']*=2
        with self.assertRaises(ValueError):self.prepare(p)

    def test_missing_thesis_rejected(self):
        p=proposal();p['theses']={}
        with self.assertRaises(ValueError):self.prepare(p)

    def test_unsupported_condition_rejected(self):
        p=proposal();p['theses']['AMD']['claims'][0]['conditions'][0]['type']='do_anything'
        with self.assertRaises(ValueError):self.prepare(p)

    def test_nonfinite_hold_stop_rejected(self):
        p=proposal();p['decisions'][0]['new_stop']=float('nan')
        with self.assertRaises(ValueError):self.prepare(p)

    def test_existing_historical_round_prevents_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'DECISION_LOG.md').write_text('## #11 — 2026-10-03 · WEEKLY ROUND\n')
            self.assertTrue(wr.already_done(root,BOOK,SAT))

    def test_interrupted_transaction_rolls_forward_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'portfolio.json').write_text('old');(root/'theses.json').write_text('old')
            real=wr.atomic_text
            calls=[]
            def crash(path,text):
                calls.append(str(path))
                if len(calls)==2:raise OSError('simulated crash')
                real(path,text)
            with patch.object(wr,'atomic_text',side_effect=crash):
                with self.assertRaises(OSError):wr.commit_bundle(root,{'portfolio.json':'new','theses.json':'new'})
            self.assertTrue(wr.recover(root))
            self.assertEqual((root/'portfolio.json').read_text(),'new')
            self.assertEqual((root/'theses.json').read_text(),'new')
            self.assertFalse(wr.recover(root))

    def test_recovery_refuses_to_overwrite_newer_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'portfolio.json').write_text('old')
            with patch.object(wr,'atomic_text',side_effect=OSError):
                with self.assertRaises(OSError):wr.commit_bundle(root,{'portfolio.json':'new'})
            (root/'portfolio.json').write_text('external edit')
            with self.assertRaises(ValueError):wr.recover(root)
            self.assertEqual((root/'portfolio.json').read_text(),'external edit')

    def test_complete_weekly_entrypoint_persists_once_and_preserves_log(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir()
            (root/'portfolio.json').write_text(json.dumps(BOOK))
            (root/'theses.json').write_text('{"_meta":{}}')
            (root/'DECISION_LOG.md').write_text('# Historical record, preserved.\n')
            (root/'state/pending_notes.md').write_text('Review previous trigger.')
            data=copy.deepcopy(DATA);data['_meta']={'date':SAT.date().isoformat()}
            (root/'weekly_data.json').write_text(json.dumps(data))
            p=proposal();p['watchlist']=[{'symbol':sym,'action':'KEEP','reasoning':'Keep under review.'} for sym in DATA]
            with patch.object(wr,'BASE',root), patch.object(wr,'datetime') as clock, patch.object(wr,'call_llm',return_value=(p,'ok')) as model, patch.dict(os.environ,{'OPENROUTER_API_KEY':'test'}), patch('sys.argv',['weekly_round.py']):
                clock.now.return_value=SAT
                wr.main();wr.main()
                self.assertEqual(model.call_count,1)
            self.assertEqual((root/'state/pending_notes.md').read_text(),'')
            self.assertTrue((root/'DECISION_LOG.md').read_text().startswith('# Historical record, preserved.'))
            self.assertEqual((root/'DECISION_LOG.md').read_text().count('WEEKLY ROUND'),1)
            self.assertTrue((root/'output/weekly_evidence.json').exists())

    def test_new_numeric_fields_cannot_bypass_prose_gate(self):
        p=proposal();p['decisions'][0]['fabricated_revenue']=999
        with self.assertRaises(ValueError):self.prepare(p)

    def test_holiday_friday_uses_last_actual_session(self):
        # Good Friday: weekly round still uses Thursday's completed session.
        self.assertEqual(wr.closing_day(datetime(2026,4,4,6,tzinfo=timezone.utc)),'2026-04-02')


class WatchdogTests(unittest.TestCase):
    def test_holiday_has_no_intraday_deadline(self):
        self.assertNotIn('detector.yml',wd.due_windows(datetime(2026,12,25,18,tzinfo=timezone.utc)))

    def test_saturday_weekly_still_expected(self):
        self.assertIn('weekly.yml',wd.due_windows(SAT))

    def test_monday_never_dispatches_weekly_catchup(self):
        self.assertNotIn('weekly.yml',wd.due_windows(MON))

    def test_stuck_active_run_never_becomes_missing(self):
        run={'head_branch':'main','created_at':(MON-timedelta(hours=3)).isoformat(),'status':'in_progress','event':'schedule'}
        kind,_=wd.diagnose([run],MON-timedelta(minutes=90),MON)
        self.assertEqual(kind,'stuck')
        self.assertIsNone(wd.repair_plan(kind,run,[]))

    def test_only_bootstrap_failure_can_rerun(self):
        run={'conclusion':'failure'}
        for name,expected in [('Dependencies','rerun-failed-jobs'),('Execute trades',None),('Telegram report',None),('Validate evidence',None)]:
            self.assertEqual(wd.repair_plan('failed',run,[{'steps':[{'name':name,'conclusion':'failure'}]}]),expected)

    def test_dispatch_is_bounded_and_recovery_not_assumed(self):
        state={};calls=[];messages=[]
        def fetch(endpoint,method='GET',payload=None):
            calls.append((endpoint,method,payload))
            return {'workflow_runs':[]} if method=='GET' else {}
        for offset in (0,1,121,242,500):
            wd.monitor(SAT+timedelta(minutes=offset),state,fetch,lambda **kw:messages.append(kw),True)
        self.assertEqual(len([c for c in calls if c[1]=='POST']),2)
        self.assertNotIn('resolved',state['incidents']['weekly.yml'])
        self.assertTrue(any('Henüz başarı doğrulanmadı' in m['message'] for m in messages))

    def test_actual_success_emits_one_recovery_message(self):
        state={'incidents':{'weekly.yml':{'since':SAT.isoformat(),'attempts':1}}};messages=[]
        def fetch(*args):
            if args[0].endswith('/jobs'):return {'jobs':[{'steps':[{'name':'3b) Structured decision and deterministic execution','conclusion':'success'}]}]}
            return {'workflow_runs':[{'id':123,'head_branch':'main','event':'workflow_dispatch','status':'completed','conclusion':'success','created_at':SAT.isoformat()}]}
        wd.monitor(SAT,state,fetch,lambda **kw:messages.append(kw),True)
        wd.monitor(SAT,state,fetch,lambda **kw:messages.append(kw),True)
        self.assertEqual(len(messages),1)
        self.assertIn('toparlanma doğrulandı',messages[0]['message'])

    def test_green_skipped_detector_does_not_count_as_heartbeat(self):
        calls=[]
        def fetch(endpoint,method='GET',payload=None):
            calls.append((endpoint,method))
            if endpoint.endswith('/jobs'):
                return {'jobs':[{'steps':[{'name':'1) Detector — measure conditions and assess news','conclusion':'skipped'}]}]}
            return {'workflow_runs':[{'id':42,'head_branch':'main','event':'schedule','created_at':MON.isoformat(),'status':'completed','conclusion':'success'}]}
        result=wd.monitor(MON,{},fetch,apply=False)
        self.assertEqual(result[0]['status'],'missing')

    def test_close_review_has_separate_deadline(self):
        now=MON.replace(hour=23)
        self.assertEqual(wd.due_windows(now)['detector.yml'],now.replace(hour=21,minute=15))

    def test_dry_run_neither_dispatches_nor_notifies(self):
        calls=[]
        def fetch(*args):calls.append(args);return {'workflow_runs':[]}
        with patch.object(wd,'notify') as send:
            wd.monitor(SAT,{},fetch,send,False)
            send.assert_not_called()
        self.assertTrue(all(len(c)==1 for c in calls))




class CloudWatchdogTests(unittest.TestCase):
    def test_delayed_daily_run_checks_previous_deadline(self):
        now=MON.replace(hour=1)+timedelta(days=1)
        self.assertEqual(wd.daily_anchor(now), MON.replace(hour=23))
        self.assertIn('detector.yml',wd.due_windows(wd.daily_anchor(now)))

    def test_remote_checkpoint_updates_sha_and_omits_callback(self):
        import base64
        calls=[]
        def fetch(endpoint,method='GET',payload=None):
            calls.append((endpoint,method,payload))
            if method=='GET':return {'sha':'old','content':base64.b64encode(b'{"incidents": {}}').decode()}
            return {'content':{'sha':'new'}}
        store=wd.RemoteState(fetch)
        store.save({'attempts':1,'_persist':lambda:None})
        self.assertEqual(calls[-1][2]['sha'],'old')
        self.assertEqual(json.loads(base64.b64decode(calls[-1][2]['content'])),{'attempts':1})
        store.save({'attempts':2})
        self.assertEqual(calls[-1][2]['sha'],'new')

    def test_failed_checkpoint_prevents_dispatch(self):
        def fail():raise RuntimeError('state write failed')
        calls=[]
        def fetch(endpoint,method='GET',payload=None):
            calls.append(method)
            return {'workflow_runs':[]}
        with self.assertRaises(RuntimeError):
            wd.monitor(SAT,{'_persist':fail},fetch,lambda **kw:None,True)
        self.assertNotIn('POST',calls)

    def test_migration_does_not_alert_for_predeployment_runs(self):
        state={'monitoring_started_at':MON.isoformat()}
        def fetch(*args):raise AssertionError('Must not inspect predeployment window')
        self.assertEqual(wd.monitor(MON,state,fetch,apply=False,daily=True),[])


if __name__=='__main__':unittest.main()
