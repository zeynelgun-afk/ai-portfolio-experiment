"""Research/execution boundary, provenance and forward-only attribution regressions."""
import copy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

import weekly_round as wr
import fundamentals as fund
import market_data
import discovery
import research_metrics as metrics
import evidence
from tests.test_resilience import BOOK, DATA, SAT, proposal, thesis

OPEN=datetime(2026,10,5,15,tzinfo=timezone.utc)


def quotes(moment=OPEN):
    return {s:{'price':price,'price_at':moment.isoformat(),'price_provider':'FMP',
                'data_source':'intraday_5m'} for s,price in [('AMD',110),('MU',60),('SPY',600),('SMH',300)]}


class SessionExecution(unittest.TestCase):
    def test_weekend_cannot_execute_even_with_fresh_prices(self):
        with self.assertRaisesRegex(ValueError,'open NYSE'):
            wr.prepare(proposal(),BOOK,{'_meta':{}},DATA,SAT,'',quotes=quotes(SAT))

    def test_holiday_and_after_close_rejected(self):
        for moment in (datetime(2026,12,25,16,tzinfo=timezone.utc),OPEN.replace(hour=21)):
            with self.assertRaisesRegex(ValueError,'open NYSE'):
                wr.prepare(proposal(),BOOK,{'_meta':{}},DATA,moment,'',quotes=quotes(moment))

    def test_session_buy_uses_current_price_not_friday_close(self):
        p=proposal();p['decisions'][0].update(action='BUY',amount_usd=60)
        result,_,_=wr.prepare(p,BOOK,{'_meta':{}},DATA,OPEN,'',quotes=quotes())
        self.assertEqual(result['trade_history'][-1]['price'],110)
        self.assertEqual(result['cash_usd'],40)
        self.assertEqual(BOOK['cash_usd'],100)

    def test_old_future_and_offsession_quotes_fail_closed(self):
        for stamp in (OPEN-timedelta(minutes=16),OPEN+timedelta(seconds=1),SAT):
            q=quotes();q['AMD']['price_at']=stamp.isoformat()
            with self.assertRaisesRegex(ValueError,'stale or out-of-session'):
                wr.prepare(proposal(),BOOK,{'_meta':{}},DATA,OPEN,'',quotes=q)

    def test_prior_intraday_fill_prevents_duplicate_weekly_direction(self):
        book=copy.deepcopy(BOOK)
        book['trade_history']=[{'date':OPEN.date().isoformat(),'symbol':'AMD','action':'BUY','source':'intraday_autonomous'}]
        p=proposal();p['decisions'][0].update(action='BUY',amount_usd=60)
        with self.assertRaisesRegex(ValueError,'same direction'):
            wr.prepare(p,book,{'_meta':{}},DATA,OPEN,'',quotes=quotes())

    def test_full_pending_entrypoint_reassesses_and_executes_once(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir()
            (root/'portfolio.json').write_text(json.dumps(BOOK))
            (root/'theses.json').write_text('{"_meta":{}}')
            (root/'DECISION_LOG.md').write_text('# Historic log\n')
            (root/'state/pending_notes.md').write_text('Review')
            (root/'state/weekly_plan.json').write_text(json.dumps({'round_id':'2026-10-03','status':'pending','proposal':proposal()}))
            data=copy.deepcopy(DATA);data['_meta']={'date':'2026-10-05'}
            (root/'weekly_data.json').write_text(json.dumps(data))
            p=proposal();p['decisions'][0].update(action='BUY',amount_usd=60)
            p['watchlist']=[{'symbol':s,'action':'KEEP','reasoning':'Monitor'} for s in DATA]
            class Clock(datetime):
                @classmethod
                def now(cls,tz=None):return OPEN
            with patch.object(wr,'BASE',root),patch.object(wr,'datetime',Clock),patch.object(wr,'live_quotes',side_effect=lambda syms,m:{s:quotes()[s] for s in syms}),patch('weekly_data.main') as refresh,patch.object(wr,'call_llm',return_value=(p,'ok')) as model,patch.dict(os.environ,{'OPENROUTER_API_KEY':'test'}),patch('sys.argv',['weekly_round.py','--execute-pending']):
                wr.main();wr.main()
                self.assertEqual(refresh.call_count,1);self.assertEqual(model.call_count,1)
            book=json.loads((root/'portfolio.json').read_text())
            self.assertEqual(book['trade_history'][0]['price'],110)
            self.assertEqual(json.loads((root/'state/weekly_plan.json').read_text())['status'],'executed')
            self.assertIn('2026-10-03',json.loads((root/'state/research_observations.json').read_text()))
            self.assertEqual((root/'state/pending_notes.md').read_text(),'')

    def test_closed_session_never_calls_model_or_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir();(root/'portfolio.json').write_text(json.dumps(BOOK));(root/'DECISION_LOG.md').write_text('')
            with patch.object(wr,'BASE',root),patch.object(wr,'market_open',return_value=False),patch.object(wr,'call_llm') as model,patch('weekly_data.main') as refresh,patch('sys.argv',['weekly_round.py','--execute-pending']):
                wr.main();model.assert_not_called();refresh.assert_not_called()


class StatementEvidence(unittest.TestCase):
    def rows(self):
        return [{'symbol':'AMD','date':'2026-06-30','period':'Q2','reportedCurrency':'USD','revenue':200,'grossProfit':80,'operatingIncome':40,'netIncome':20,'filingDate':'2026-08-01'},
                {'symbol':'AMD','date':'2025-06-30','period':'Q2','reportedCurrency':'USD','revenue':100,'grossProfit':30,'operatingIncome':10,'netIncome':5,'filingDate':'2025-08-01'}]
    def test_wrong_issuer_future_period_and_duplicate_rejected(self):
        rows=self.rows();rows[0]['symbol']='MU'
        with self.assertRaises(market_data.ProviderError):fund.validate(rows,'AMD','income',OPEN)
        rows=self.rows();rows[0]['date']='2027-01-01';rows[1]['date']='2027-02-01'
        with self.assertRaises(market_data.ProviderError):fund.validate(rows,'AMD','income',OPEN)
        with self.assertRaises(market_data.ProviderError):fund.validate(self.rows()*2,'AMD','income',OPEN)
    def test_primary_success_does_not_query_yahoo_and_preserves_period(self):
        with patch.object(market_data,'fmp',return_value=self.rows()),patch('yfinance.Ticker') as yahoo:
            rows,provider=fund.statements('AMD','income',OPEN)
        yahoo.assert_not_called();self.assertEqual(provider,'FMP');self.assertEqual(rows[0]['date'],'2026-06-30')
    def test_derived_growth_and_evidence_currency_are_explicit(self):
        rows=fund.validate(self.rows(),'AMD','income',OPEN)
        def get(symbol,kind,now):
            if kind!='income':raise market_data.ProviderError('missing')
            return rows,'FMP'
        with patch.object(fund,'statements',side_effect=get):packet=fund.collect('AMD',OPEN)
        self.assertEqual(packet['facts']['revenue_yoy_pct']['value'],100)
        self.assertEqual(packet['facts']['operating_margin_pct']['value'],20)
        facts=evidence.ledger({'AMD':{'fundamental_research':packet}},OPEN.isoformat(),'test')
        self.assertEqual(facts['AMD.quarter_revenue']['as_of'],'2026-06-30')
        self.assertEqual(facts['AMD.quarter_revenue']['unit'],'USD')
        self.assertIn('balance statements unavailable',packet['gaps'])
    def test_future_filing_never_becomes_current_evidence(self):
        rows=self.rows();rows[0]['filingDate']='2026-12-01'
        with self.assertRaises(market_data.ProviderError):fund.validate(rows,'AMD','income',OPEN)


class Attribution(unittest.TestCase):
    def test_unmatured_data_has_no_success_label(self):
        cohort={'round_id':'r','observed_at':OPEN.isoformat(),'candidates':{'AMD':{'entry_price':100,'decision':'BUY','channels':['dislocation']}},'benchmarks':{'SPY':{'price':100},'SMH':{'price':100}}}
        dates=metrics._session_days(OPEN.date(),121)
        histories={s:pd.DataFrame({'Close':[price+(i+1)*step for i in range(len(dates))]},index=pd.to_datetime(dates))
                   for s,price,step in [('AMD',100,2),('SPY',100,1),('SMH',100,1.5)]}
        result=metrics.score(cohort,histories)
        twenty=next(row for row in result['results'] if row['horizon_sessions']==20)
        self.assertAlmostEqual(twenty['return_pct'],40)
        self.assertAlmostEqual(twenty['excess_spy_pp'],20)
        self.assertAlmostEqual(twenty['net_return_scenarios_pct']['100'],39)
        self.assertIn('maximum_drawdown_pct',twenty)
    def test_missing_symbol_endpoint_not_dropped_from_denominator_silently(self):
        cohort={'round_id':'r','observed_at':OPEN.isoformat(),'candidates':{'AMD':{'entry_price':100,'decision':'WATCH','channels':['structural_universe']}},'benchmarks':{'SPY':{'price':100},'SMH':{'price':100}}}
        dates=metrics._session_days(OPEN.date(),121)
        frame=pd.DataFrame({'Close':[105]*len(dates)},index=pd.to_datetime(dates))
        result=metrics.score(cohort,{'SPY':frame,'SMH':frame})
        self.assertEqual(result['results'],[]);self.assertEqual(len(result['pending']),3)
    def test_exposure_reports_loss_scenarios_without_changing_book(self):
        before=copy.deepcopy(BOOK);report=metrics.exposure(BOOK,quotes())
        self.assertLess(report['all_positions_down_20pct_equity_impact_pct'],0)
        self.assertEqual(BOOK,before)


class DiscoveryChannels(unittest.TestCase):
    def test_channel_membership_is_measured_and_partial_failure_is_explicit(self):
        def select(symbol,dataset,primary,backup,validator):
            if dataset.endswith('insider_purchase'):raise market_data.ProviderError('unavailable')
            name=dataset.split(':')[1]
            return [{'symbol':'AMD' if name!='dislocation' else 'MU'}],'FMP'
        with patch.object(market_data,'select',side_effect=select):result=discovery.collect(OPEN)
        self.assertEqual(result['membership']['AMD'],['momentum','structural_universe'])
        self.assertEqual(result['membership']['MU'],['dislocation'])
        self.assertEqual(result['unavailable_channels'],['insider_purchase'])
    def test_all_failed_stops_scout(self):
        with patch.object(market_data,'select',side_effect=market_data.ProviderError('missing')):
            with self.assertRaises(market_data.ProviderError):discovery.collect(OPEN)



class AuditObjections(unittest.TestCase):
    def test_unilateral_objection_survives_next_round_and_does_not_duplicate(self):
        import reviewers
        from tests.test_reviewers import finding
        with tempfile.TemporaryDirectory() as tmp:
            first=reviewers.persist_disagreements(tmp,[finding('wish_as_thesis','A')],[],[])
            self.assertEqual(first['new_count'],1)
            second=reviewers.persist_disagreements(tmp,[finding('wish_as_thesis','A')],[],[])
            self.assertEqual(second['new_count'],0)
            third=reviewers.persist_disagreements(tmp,[],[],[])
            self.assertEqual(len(third['findings']),1)
            self.assertEqual(third['findings'][0]['status'],'open')

class BackupStatementCoverage(unittest.TestCase):
    def test_yahoo_empty_old_column_does_not_discard_current_statement(self):
        from unittest.mock import MagicMock
        ticker=MagicMock();ticker.info={'financialCurrency':'USD'}
        ticker.quarterly_income_stmt=pd.DataFrame(
            {pd.Timestamp('2026-06-30'):[100,30,20,10],pd.Timestamp('2025-06-30'):[float('nan')]*4},
            index=['Total Revenue','Gross Profit','Operating Income','Net Income'])
        with patch.object(market_data,'fmp',side_effect=market_data.ProviderError('outage')),patch('yfinance.Ticker',return_value=ticker):
            rows,provider=fund.statements('AMD','income',OPEN)
        self.assertEqual(provider,'yfinance');self.assertEqual(len(rows),1)
        self.assertIsNone(rows[0]['published_at'])

class CalendarAttribution(unittest.TestCase):
    def test_missing_benchmark_session_is_not_replaced_with_later_day(self):
        cohort={'round_id':'r','observed_at':OPEN.isoformat(),'candidates':{'AMD':{'entry_price':100,'decision':'BUY','channels':['momentum']}},'benchmarks':{'SPY':{'price':100},'SMH':{'price':100}}}
        dates=metrics._session_days(OPEN.date(),121)
        target=dates[19]
        frame=pd.DataFrame({'Close':[105]*len(dates)},index=pd.to_datetime(dates))
        spy=frame.drop(pd.Timestamp(target))
        scored=metrics.score(cohort,{'AMD':frame,'SPY':spy,'SMH':frame})
        self.assertTrue(any('20:missing endpoint' in p for p in scored['pending']))
        self.assertFalse(any(r['horizon_sessions']==20 for r in scored['results']))

class MacroCoverage(unittest.TestCase):
    def test_sector_snapshot_uses_measured_average_change_and_all_sectors(self):
        from weekly_data import sector_snapshot
        rows=[{'sector':s,'exchange':'NASDAQ','date':'2026-09-25','averageChange':1.5} for s in ('Technology','Energy','Industrials','Utilities','Healthcare','Financials')]
        result=sector_snapshot(rows,'2026-09-25')
        self.assertEqual(len(result),6)
        self.assertEqual(result['Technology / NASDAQ']['change_pct'],1.5)
        self.assertIsNone(sector_snapshot(rows,'2026-09-24'))

class ScoutUniqueness(unittest.TestCase):
    def test_duplicate_tickers_cannot_fake_candidate_count(self):
        import scout
        with self.assertRaises(ValueError):scout.validate_symbols(['AMD']*15)




# Existing flow fixtures isolate the new independent review service; its rejection
# and citation semantics are exercised separately in test_evidence_depth.py.
def setUpModule():
    from unittest.mock import patch
    global semantic_fixture
    semantic_fixture = patch('claim_evidence.semantic_review', return_value={'verdict':'supported'})
    semantic_fixture.start()


def tearDownModule():
    semantic_fixture.stop()

if __name__=='__main__':unittest.main()
