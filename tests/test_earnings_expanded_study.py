import unittest
from datetime import date
import pandas as pd
import pandas_market_calendars as calendars
from earnings_expanded_study import (
    CAP_MAX, CAP_MIN, _valid_us_profile, event_features, returns,
    safe_rows, sequential_features, windows,
)


class ExpandedEarningsStudyTests(unittest.TestCase):
    def setUp(self):
        self.eventday=date(2025,5,5)

    def test_only_pre_event_filed_statements_are_used(self):
        rows=[
            {'symbol':'X','period':'Q1','fiscalYear':2024,'acceptedDate':'2024-05-01','revenue':100,'grossProfit':30,'operatingCashFlow':4},
            {'symbol':'X','period':'Q1','fiscalYear':2025,'acceptedDate':'2025-05-06','revenue':150,'grossProfit':60,'operatingCashFlow':8},
        ]
        result=sequential_features({'period':'Q1','fiscalYear':2025},rows,self.eventday)
        self.assertEqual(result['status'],'prior_year_comparison_unavailable')

    def test_same_quarter_yoy_features_keep_mixed_operating_signals(self):
        rows=[
            {'period':'Q1','fiscalYear':2024,'acceptedDate':'2024-05-01','revenue':100,'grossProfit':30,'operatingIncome':9,'operatingCashFlow':15},
            {'period':'Q1','fiscalYear':2025,'acceptedDate':'2025-05-01','revenue':130,'grossProfit':30,'operatingIncome':8,'operatingCashFlow':7},
        ]
        event={'date':'2025-05-05','symbol':'X','period':'Q1','fiscalYear':2025,
               'epsActual':1.01,'epsEstimated':0.99,'revenueActual':130,'revenueEstimated':125}
        group,change=event_features(event,rows)
        self.assertEqual(group,'eps_and_revenue_beat')
        self.assertEqual(change['operating_indicators']['revenue_positive_yoy'],True)
        self.assertEqual(change['operating_indicators']['gross_margin_expanding'],False)
        self.assertEqual(change['operating_indicators']['operating_cash_flow_improving'],False)
        self.assertEqual(change['operating_improvement_group'],'mixed_or_incomplete')

    def test_entry_and_horizons_count_entry_session_as_day_one(self):
        schedule=calendars.get_calendar('NYSE').schedule('2025-04-01','2025-09-30')
        days=schedule.index.tz_localize(None)
        entry,h=windows(date(2025,5,5),days,days[-1])
        self.assertEqual(entry.date(),date(2025,5,6))
        self.assertEqual((h['20']-entry).days<30,True)
        self.assertEqual(h['60']>h['20'],True)

    def test_returns_use_real_exchange_sessions_and_cost_scenarios(self):
        schedule=calendars.get_calendar('NYSE').schedule('2025-01-01','2025-03-31')
        days=schedule.index.tz_localize(None)
        entry=days[2];end=days[21]
        stocks=pd.DataFrame({'price':[100.0]*len(days)},index=days)
        benchmark=pd.DataFrame({'price':[100.0]*len(days)},index=days)
        result=returns(stocks,benchmark,days,entry,end,(0,100,500))
        self.assertEqual(result['gross_pct'],0)
        self.assertEqual(result['excess_benchmark_pp'],0)
        self.assertEqual(result['net_pct_by_assumed_roundtrip_bps']['500'],-5)
        self.assertIsNone(returns(stocks.drop(entry),benchmark,days,entry,end,(0,)))
        stock_snapshot={d.date().isoformat():{'price':100} for d in days}
        self.assertEqual(returns(stock_snapshot,stock_snapshot,days,entry,end,(0,))['gross_pct'],0)

    def test_issuer_balancing_prevents_event_count_from_dominating_summary(self):
        from earnings_expanded_study import summarize
        def outcome(excess):
            return {'gross_pct':excess,'excess_benchmark_pp':excess,'max_close_drawdown_pct':-2,
                    'net_pct_by_assumed_roundtrip_bps':{'0':excess,'100':excess-1}}
        events=[]
        for symbol, values in {'A':[10,10,10,10],'B':[-2]}.items():
            for value in values:
                events.append({'symbol':symbol,'status':'exploratory_only',
                    'operating_change':{'operating_improvement_group':'improving'},
                    'outcomes':{'IWM':{'20':outcome(value)}}})
        report=summarize({'events':[],'filing_events':events})
        row=report['filing_issuer_balanced_summary']['improving:20:IWM']
        self.assertEqual(row['issuer_n'],2)
        self.assertEqual(row['median_issuer_mean_excess_pp'],4)
        self.assertEqual(row['leave_one_issuer_out_mean_excess_pp_range'],[-2,10])

    def test_event_market_cap_requires_historical_point(self):
        caps={'marketCap':3_000_000_000}
        self.assertTrue(CAP_MIN<=caps['marketCap']<=CAP_MAX)
        profile={'symbol':'X','country':'US','currency':'USD','marketCap':500_000_000,
                 'sector':'Technology','isEtf':False,'isFund':False,'isAdr':False}
        self.assertIsNotNone(_valid_us_profile('X',[profile]))
        self.assertIsNone(_valid_us_profile('X',[{**profile,'country':'GB'}]))
        self.assertIsNone(_valid_us_profile('X',[{**profile,'isEtf':True}]))

    def test_wrong_issuer_and_invalid_dates_are_excluded(self):
        rows=[{'symbol':'Y','date':'2025-05-05','epsActual':1},
              {'symbol':'X','date':'not-a-date','epsActual':1}]
        self.assertEqual(safe_rows(rows,'X'),[])
