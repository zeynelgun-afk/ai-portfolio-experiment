"""Behavioral regressions for source gates, economic triggers and corporate accounting."""
import copy
from datetime import date, datetime, timezone, timedelta
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import pandas as pd

import claim_evidence as ce
import corporate_actions as ca
import detector
import fundamentals
import market_data
import reassess
import research_metrics
import weekly_round

NOW=datetime(2026,9,28,15,tzinfo=timezone.utc)
TEXT='The company reported lower operating margins as raw material costs increased during the quarter.'
NEWS=[{'symbol':'MU','url':'https://example.org/report','publishedDate':NOW.isoformat(),'text':TEXT,'title':'Quarterly results'}]
COND={'type':'fundamental_below','metric':'operating_margin_pct','value':20,'unit':'%','severity':'thesis'}

def row():
    return {'price':100,'previous_close':100,'price_at':NOW.isoformat(),'data_source':'intraday_5m',
            'fundamental_research':{'collected_at':NOW.isoformat(),'facts':{'operating_margin_pct':
                {'value':15,'unit':'%','as_of':'2026-06-30','source':'FMP/income'}}}}

def thesis():
    return {'MU':{'thesis_summary':'Margins should remain resilient.', 'claims':[{'id':'MU-1','text':'Original thesis',
        'status':'valid','conditions':[copy.deepcopy(COND)]}]}}

class FundamentalMonitoring(unittest.TestCase):
    def test_fresh_breach_and_missing_or_mismatched_evidence(self):
        self.assertEqual(detector.measure(COND,'MU',{'MU':row()},None,NOW.date())[:3],(15,20.0,'below'))
        for change in ('stale','unit','nan','missing'):
            data=row()
            if change=='stale':data['fundamental_research']['collected_at']='2026-09-27T15:00:00+00:00'
            if change=='unit':data['fundamental_research']['facts']['operating_margin_pct']['unit']='USD'
            if change=='nan':data['fundamental_research']['facts']['operating_margin_pct']['value']=float('nan')
            if change=='missing':data.pop('fundamental_research')
            self.assertIsNone(detector.measure(COND,'MU',{'MU':data},None,NOW.date()))

    def test_report_dedup_and_new_report_retriggers(self):
        data={'MU':row()}; previous={}
        for _ in range(3):
            report=detector.run(thesis(),data,{},previous,{},NOW,assess_news=False)
            previous=report['conditions']
        hit=report['triggered'][0];lock=hit['cooldown_key']
        self.assertTrue(lock.startswith('fundamental:'))
        repeat=detector.run(thesis(),data,{},previous,{lock:NOW.isoformat()},NOW,assess_news=False)
        self.assertEqual(repeat['triggered'],[])
        data['MU']['fundamental_research']['facts']['operating_margin_pct']['as_of']='2026-09-01'
        renewed=detector.run(thesis(),data,{},previous,{lock:NOW.isoformat()},NOW,assess_news=False)
        self.assertEqual(len(renewed['triggered']),1)
        self.assertNotEqual(renewed['triggered'][0]['cooldown_key'],lock)

    def test_missing_measurement_blocks_thesis_trade(self):
        theses=thesis(); data={'MU':{}}
        report=detector.run(theses,data,{}, {},{},NOW,assess_news=False)
        self.assertEqual(len(report['measurement_errors']),1)
        report['triggered']=[{'symbol':'MU','claim_id':'MU-1','severity':'thesis'}]
        with tempfile.TemporaryDirectory() as tmp, patch.object(reassess,'call_llm') as model:
            decisions,_=reassess.thesis_flow(theses,report,{'positions':[]},NOW,'model','key',{'calls':0},False,tmp+'/notes',tmp+'/decisions')
            self.assertEqual(decisions,[]);model.assert_not_called()

    def test_weekly_thesis_requires_economic_condition_and_matching_units(self):
        book={'positions':[{'symbol':'MU'}]}
        weekly_round.validate_theses(thesis(),book,NOW,{'MU':row()})
        invalid=thesis();invalid['MU']['claims'][0]['conditions']=[{'type':'price_below','value':90,'severity':'claim'}]
        with self.assertRaisesRegex(ValueError,'economic thesis condition'):
            weekly_round.validate_theses(invalid,book,NOW,{'MU':row()})
        invalid=thesis();invalid['MU']['claims'][0]['conditions'][0]['unit']='USD'
        with self.assertRaisesRegex(ValueError,'matching metric/unit'):
            weekly_round.validate_theses(invalid,book,NOW,{'MU':row()})

    def test_claim_budget_reserves_review_call(self):
        report={'data':{'MU':row()},'triggered':[{'symbol':'MU','claim_id':'MU-1','severity':'claim'}]}
        with patch.object(reassess,'call_llm') as model:
            reassess.claim_flow(thesis(),report,{'positions':[]},NOW,'model','key',{'calls':59},60,False,False)
            model.assert_not_called()

class EvidenceGates(unittest.TestCase):
    def news_report(self, impact='invalidates'):
        source=next(iter(ce.documents('MU',NEWS)))
        return {'impact':impact,'claim_ids':['MU-1'],'citations':[{'source_id':source,'quote':TEXT}],
            'reasoning':'Reported margin pressure challenges the margin thesis.',
            'counterevidence':'The excerpt does not establish permanence.','uncertainty':'One reporting period only.'}

    def test_headlines_wrong_issuer_and_short_excerpts_are_not_sources(self):
        for item in ({'title':'Headline only'},dict(NEWS[0],symbol='AMD'),dict(NEWS[0],text='Too short')):
            self.assertEqual(ce.documents('MU',[item]),{})

    def test_invented_quote_and_source_rejected(self):
        sources=ce.documents('MU',NEWS);key=next(iter(sources))
        for cite in ({'source_id':key,'quote':'An invented factual assertion'}, {'source_id':'unknown','quote':TEXT},'bad'):
            with self.assertRaises(ValueError):ce.validate_citations([cite],sources)

    def test_news_requires_known_claim_and_preserves_uncertainty(self):
        def mock(*args,**kwargs):
            payload=self.news_report('uncertain');kwargs['response_validator'](payload);return payload,'ok'
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test'}),patch.object(reassess,'call_llm',side_effect=mock):
            verdict,report=detector.check_news_shock('MU','Thesis',NEWS,[{'id':'MU-1'}])
            self.assertIsNone(verdict);self.assertIn('source_documents',report)
            with self.assertRaises(ValueError):detector.check_news_shock('MU','Thesis',NEWS,[{'id':'OTHER'}])

    def test_partial_news_packet_is_not_marked_complete(self):
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test'}),patch.object(reassess,'call_llm') as model:
            self.assertIsNone(detector.check_news_shock('MU','Thesis',NEWS+[{'title':'missing body'}])[0])
            model.assert_not_called()

    def test_semantic_reviewer_rejects_unsupported_or_unresolved_claims(self):
        source=next(iter(ce.documents('MU',NEWS)))
        for verdict,issues in [('unsupported',['Causal claim not established']),('supported',['Contradiction'])]:
            payload={'verdict':verdict,'issues':issues,'counterargument':'Persistence is not known.',
                     'citations':[{'source_id':source,'quote':TEXT}]}
            def mock(*args,**kwargs):kwargs['response_validator'](payload);return payload,'ok'
            with patch.object(reassess,'call_llm',side_effect=mock),self.assertRaises(ValueError):
                ce.semantic_review({'thesis':'Permanent deterioration'}, {'MU':{'source_documents':ce.documents('MU',NEWS)}},{},'test','review')

    def test_semantic_failure_preserves_old_claim_text(self):
        theses=thesis();report={'data':{'MU':row()},'triggered':[{'symbol':'MU','claim_id':'MU-1','severity':'claim','trigger':'Margin breach'}]}
        with patch.object(reassess,'call_llm',return_value=({'text':'New unsupported thesis','status':'invalid'},'ok')),patch.object(ce,'semantic_review',side_effect=ValueError('unsupported')):
            reassess.claim_flow(theses,report,{'positions':[]},NOW,'model','key',{'calls':0},60,False,False)
        self.assertEqual(theses['MU']['claims'][0]['text'],'Original thesis')
        self.assertEqual(theses['MU']['claims'][0]['status'],'unassessed')
        self.assertIn('error',report['semantic_reviews'][0])

class CorporateAccounting(unittest.TestCase):
    def setUp(self):
        self.book={'cash_usd':100,'positions':[{'symbol':'MU','entry_date':'2026-08-01','shares':10.,'entry_price':100.,'cost_usd':1000.,'stop_weekly_close':80.}], 'trade_history':[]}
        self.theses={'MU':{'claims':[{'id':'MU-1','conditions':[{'type':'price_below','value':90}]}]}}
        self.state={'baseline_date':'2026-09-01','events':{},'receivables':{}}
        self.split={'id':'MU:split:2026-09-28','symbol':'MU','kind':'split','date':'2026-09-28','ratio':2.,'source':'FMP/splits'}
        self.div={'id':'MU:dividend:2026-09-28','symbol':'MU','kind':'dividend','date':'2026-09-28','amount_per_share':1.,'payment_date':'2026-10-02','source':'FMP/dividends'}

    def test_split_and_reverse_split_preserve_cost_and_replay_once(self):
        for ratio in (2.,0.1):
            event=dict(self.split,ratio=ratio)
            book,theses,state,_=ca.reconcile(self.book,self.theses,self.state,[event],NOW.date())
            position=book['positions'][0]
            self.assertEqual(position['cost_usd'],1000)
            self.assertAlmostEqual(position['shares']*position['entry_price'],1000)
            self.assertEqual(position['stop_weekly_close'],80/ratio)
            self.assertEqual(theses['MU']['claims'][0]['conditions'][0]['value'],90/ratio)
            again,_,_,changes=ca.reconcile(book,theses,state,[event],NOW.date())
            self.assertEqual(again,book);self.assertEqual(changes,[])

    def test_dividend_entitlement_survives_sale_and_pays_once(self):
        book,theses,state,_=ca.reconcile(self.book,self.theses,self.state,[self.div],NOW.date())
        self.assertEqual(book['cash_usd'],100);self.assertEqual(book['dividend_receivable_usd'],10)
        book['positions']=[]
        book,theses,state,_=ca.reconcile(book,theses,state,[self.div],date(2026,10,2))
        self.assertEqual(book['cash_usd'],110);self.assertEqual(book['dividend_receivable_usd'],0)
        book,_,_,_=ca.reconcile(book,theses,state,[self.div],date(2026,10,3))
        self.assertEqual(book['cash_usd'],110)

    def test_late_payment_date_can_be_completed_without_double_credit(self):
        event=dict(self.div,payment_date=None)
        book,theses,state,_=ca.reconcile(self.book,self.theses,self.state,[event],NOW.date())
        book,_,_,_=ca.reconcile(book,theses,state,[self.div],date(2026,10,2))
        self.assertEqual(book['cash_usd'],110)

    def test_revision_and_late_action_crossing_trade_are_blocked(self):
        book,theses,state,_=ca.reconcile(self.book,self.theses,self.state,[self.split],NOW.date())
        with self.assertRaises(ValueError):ca.reconcile(book,theses,state,[dict(self.split,ratio=3)],NOW.date())
        self.book['trade_history']=[{'symbol':'MU','date':'2026-09-28','action':'SELL','shares':1}]
        with self.assertRaises(ValueError):ca.reconcile(self.book,self.theses,self.state,[self.split],NOW.date())

    def test_ex_date_buyer_gets_no_prior_entitlement(self):
        self.book['positions'][0]['entry_date']='2026-09-28'
        self.book['trade_history']=[{'symbol':'MU','date':'2026-09-28','action':'BUY','shares':10}]
        book,_,state,_=ca.reconcile(self.book,self.theses,self.state,[self.div],date(2026,10,2))
        self.assertEqual(book['cash_usd'],100);self.assertEqual(state['receivables'],{})

    def test_baseline_does_not_rewrite_history(self):
        book,_,state,changes=ca.reconcile(self.book,self.theses,{},[self.split],NOW.date())
        self.assertEqual(book,self.book);self.assertEqual(changes,[])
        self.assertEqual(state['baseline_date'],'2026-09-28')

    def test_currency_and_inactive_identity_fail_closed(self):
        for extra in ({'currency':'EUR'}, {'isActivelyTrading':False}, {'isin':None}):
            row={'symbol':'MU','currency':'USD','isActivelyTrading':True,'isin':'US-test',**extra}
            with patch.object(market_data,'fmp',return_value=[row]),self.assertRaises(ValueError):ca.identity('MU')

    def test_failed_event_provider_never_means_no_events(self):
        with patch.dict('os.environ',{'FMP_API_KEY':'test'}),patch.object(ca.requests,'get',side_effect=TimeoutError('offline')):
            with self.assertRaises(market_data.ProviderError):ca.events('MU')

    def test_atomic_bundle_recovers_corporate_ledger_with_portfolio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir()
            targets={'portfolio.json':json.dumps(self.book),'state/corporate_actions.json':json.dumps(self.state),'CORPORATE_ACTIONS.md':'event log'}
            original=weekly_round.atomic_text
            def interrupted(path,text):
                if path.name=='corporate_actions.json':raise OSError('simulated interrupted write')
                original(path,text)
            with patch.object(weekly_round,'atomic_text',side_effect=interrupted),self.assertRaises(OSError):
                weekly_round.commit_bundle(root,targets)
            self.assertTrue(weekly_round.recover(root))
            self.assertEqual(json.loads((root/'portfolio.json').read_text()),self.book)
            self.assertEqual(json.loads((root/'state/corporate_actions.json').read_text()),self.state)
            self.assertFalse(weekly_round.recover(root))

class AdjustedReturns(unittest.TestCase):
    def test_split_does_not_look_like_a_loss_and_dividend_adds_return(self):
        days=pd.to_datetime(['2026-09-28','2026-10-05','2026-10-26'])
        cohort={'round_id':'test','observed_at':NOW.isoformat(),'candidates':{'MU':{'entry_price':100,'decision':'HOLD','channels':['value']}},'benchmarks':{'SPY':{'price':100},'SMH':{'price':100}}}
        histories={'MU':pd.DataFrame({'raw_close':[100,50,50],'total_close':[49,50,50]},index=days)}
        for symbol in ('SPY','SMH'):histories[symbol]=pd.DataFrame({'raw_close':[100,100,100],'total_close':[100,100,100]},index=days)
        report=research_metrics.score(cohort,histories)
        self.assertEqual(len(report['results']),2)
        self.assertAlmostEqual(report['results'][0]['return_pct'],(50/49-1)*100)
        del histories['SMH']
        self.assertEqual(research_metrics.score(cohort,histories)['results'],[])

    def test_yahoo_backup_undoes_splits_and_excludes_unclosed_day(self):
        frame=pd.DataFrame({'Close':[50,50,51], 'Adj Close':[49,50,51],'Stock Splits':[0,2,0]},index=pd.to_datetime(['2026-09-24','2026-09-25','2026-09-28']))
        with patch.object(market_data,'fmp',side_effect=market_data.ProviderError('outage')),patch('yfinance.Ticker') as ticker:
            ticker.return_value.history.return_value=frame
            result=market_data.return_history('MU',NOW)
        self.assertEqual(result['raw_close'].tolist(),[100,50]);self.assertEqual(result.attrs['provider'],'yfinance')

if __name__=='__main__':unittest.main()
