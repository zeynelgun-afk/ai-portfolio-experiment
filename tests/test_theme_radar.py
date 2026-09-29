import unittest
from datetime import datetime, timezone, date
from unittest.mock import patch
import pandas as pd

import theme_radar
import scout


class ThemeRadarTests(unittest.TestCase):
    def test_industry_return_requires_full_window_and_compounds(self):
        rows=[{'date':f'2025-01-{i:02}', 'averageChange':1.0} for i in range(1,21)]
        self.assertAlmostEqual(theme_radar.compound_change(rows,20),22.019,places=2)
        self.assertIsNone(theme_radar.compound_change(rows[:19],20))

    def test_industry_sample_keeps_gainers_and_losers_and_ranks_each_horizon(self):
        rows=[{'industry':'Semiconductors','exchange':'NASDAQ','return_5_sessions_pct':5,
               'return_21_sessions_pct':8},
              {'industry':'Genomics','exchange':'NYSE','return_5_sessions_pct':2,
               'return_21_sessions_pct':10}]
        ranks=theme_radar.rank_industry_momentum(rows,{'5_sessions':1,'21_sessions':3})
        self.assertEqual(ranks['5_sessions'][0]['industry'],'Semiconductors')
        self.assertEqual(ranks['21_sessions'][0]['industry'],'Genomics')
        self.assertEqual(ranks['5_sessions'][0]['excess_spy_pp'],4)
        sample=theme_radar._industry_sample([
            {'industry':'Same','exchange':'NYSE','averageChange':2},
            {'industry':'Same','exchange':'NASDAQ','averageChange':-3},
            {'industry':'Up','exchange':'NYSE','averageChange':1},
            {'industry':'Down','exchange':'NASDAQ','averageChange':-1}])
        self.assertEqual({row['industry'] for row in sample},{'Same','Up','Down'})
        self.assertEqual(len(sample),3)

    def test_theme_proxy_momentum_ranks_one_week_and_one_month_separately(self):
        now=datetime(2026,9,29,12,tzinfo=timezone.utc)
        dates=pd.bdate_range(end='2026-09-25',periods=30)
        bitcoin=pd.DataFrame({'total_close':[100+i*1.5 for i in range(30)]},index=dates)
        semis=pd.DataFrame({'total_close':[100+i*.5 for i in range(30)]},index=dates)
        bitcoin.attrs['provider']='FMP';semis.attrs['provider']='yfinance'
        def history(symbol, _now):
            if symbol=='IBIT': return bitcoin
            if symbol=='SMH': return semis
            raise theme_radar.market_data.ProviderError('not available in fixture')
        with patch.object(theme_radar,'_theme_proxy_history',side_effect=history), \
             patch.object(theme_radar.market_data,'last_closed',return_value=date(2026,9,25)):
            result=theme_radar.theme_proxy_momentum(now,{'5_sessions':0,'21_sessions':0})
        self.assertEqual(result['rankings']['5_sessions'][0]['theme'],'Bitcoin')
        self.assertEqual(result['rankings']['21_sessions'][0]['proxy_symbol'],'IBIT')
        self.assertEqual(result['rankings']['5_sessions'][0]['provider'],'FMP')
        self.assertEqual(result['rankings']['21_sessions'][1]['provider'],'yfinance')
        self.assertEqual(len(result['failures']),len(theme_radar.THEME_PROXIES)-2)

    def test_news_requires_recent_dated_headline_and_source_link(self):
        now=datetime(2026,9,29,12,tzinfo=timezone.utc)
        result=theme_radar.validate_news([
            {'title':'Current sector story','publishedDate':'2026-09-29 10:00:00','url':'https://source.test/a','publisher':'A'},
            {'title':'Old story','publishedDate':'2026-09-01 10:00:00','url':'https://source.test/b'},
            {'title':'No source link','publishedDate':'2026-09-29 10:00:00'},
            {'title':'Future story','publishedDate':'2026-09-30 10:00:00','url':'https://source.test/c'},
        ],now)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['title'],'Current sector story')

    def test_stock_and_benchmark_use_same_trading_session_endpoints(self):
        dates=pd.bdate_range('2026-06-01',periods=70)
        stock=pd.DataFrame({'total_close':range(100,170)},index=dates)
        benchmark=pd.DataFrame({'total_close':range(100,170)},index=dates)
        now=datetime(2026,9,29,12,tzinfo=timezone.utc)
        with patch.object(theme_radar.market_data,'last_closed',return_value=date(2026,9,29)):
            result=theme_radar.relative_strength(stock,benchmark,now)
        self.assertAlmostEqual(result['20']['excess_spy_pp'],0)
        self.assertAlmostEqual(result['60']['excess_spy_pp'],0)
        with patch.object(theme_radar.market_data,'last_closed',return_value=date(2026,9,29)):
            self.assertIsNone(theme_radar.relative_strength(stock.iloc[:50],benchmark.iloc[:50],now))

    def test_inbox_tracks_new_continued_and_no_longer_confirmed_candidates(self):
        first=theme_radar.merge_snapshot({'as_of':'2026-09-26','observed_at':'t1',
            'candidates':[{'symbol':'AAA'}]})
        second=theme_radar.merge_snapshot({'as_of':'2026-10-03','observed_at':'t2',
            'candidates':[{'symbol':'AAA'},{'symbol':'BBB'}]},first)
        self.assertEqual([r['pool_status'] for r in second['latest']['candidates']],['continued','new'])
        third=theme_radar.merge_snapshot({'as_of':'2026-10-10','observed_at':'t3','candidates':[]},second)
        self.assertEqual(third['latest']['no_longer_confirmed'],['AAA','BBB'])
        self.assertEqual(len(third['observations']),3)

    def test_story_links_must_cite_supplied_article_and_leading_industry(self):
        radar={'news':[{'id':'a1'}],'leading_industries':[{'industry':'Semiconductors'}],
               'candidates':[{'symbol':'AAA','industry':'Semiconductors'}]}
        themes=theme_radar.validate_theme_analysis({'themes':[
            {'name':'AI compute','stance':'tailwind','article_ids':['a1','invented'],
             'industries':['Semiconductors','Invented'], 'counterevidence_article_ids':['bad']},
            {'name':'Unsupported','stance':'tailwind','article_ids':['bad'],
             'industries':['Semiconductors']} ]},radar)
        result=theme_radar.attach_theme_links(radar,themes)
        self.assertEqual(themes[0]['article_ids'],['a1'])
        self.assertEqual(themes[0]['industries'],['Semiconductors'])
        self.assertEqual(themes[0]['counterevidence_article_ids'],[])
        self.assertEqual(result['candidates'][0]['theme_links'],['AI compute'])
        self.assertEqual(len(themes),1)

    def test_telegram_summary_cites_new_candidates_and_disclaims_flow_and_buy_signal(self):
        radar={'news':[{'id':'a1','title':'Power demand rises','url':'https://source.test/a'}],
            'themes':[{'name':'AI power','article_ids':['a1']}],
            'candidates':[{'symbol':'AAA','pool_status':'new','industry':'Electric Utilities',
                'theme_links':['AI power'],'relative_strength':{
                    '20':{'excess_spy_pp':3.2},'60':{'excess_spy_pp':7.1}}}]}
        text=scout.theme_telegram_section(radar)
        self.assertIn('AAA',text);self.assertIn('https://source.test/a',text)
        self.assertIn('alım sinyali değildir',text);self.assertIn('doğrudan fon akışı ölçümü değildir',text)

    def test_telegram_summary_shows_separate_week_and_month_theme_leaders(self):
        radar={'theme_proxy_momentum':{'rankings':{
            '5_sessions':[{'theme':'Semiconductors','proxy_symbol':'SMH',
                'return_5_sessions_pct':7,'excess_spy_pp':3}],
            '21_sessions':[{'theme':'Genomics','proxy_symbol':'ARKG',
                'return_21_sessions_pct':9,'excess_spy_pp':5}]}},
            'theme_momentum':{'rankings':{'5_sessions':[
                {'industry':'Semiconductors','weekly_vs_monthly_pace_pp':2.5}]}}}
        text=scout.theme_telegram_section(radar)
        self.assertIn('1 hafta: Semiconductors (SMH) +7.0%',text)
        self.assertIn('1 ay: Genomics (ARKG) +9.0%',text)
        self.assertIn('Aylık tempoya göre haftalık ivmelenen sektörler',text)
        quiet=scout.theme_telegram_section({'theme_momentum':{'rankings':{'5_sessions':[
            {'industry':'Semiconductors','weekly_vs_monthly_pace_pp':-1.2}]}}})
        self.assertIn('aylık tempoyu aşan haftalık getiri yok',quiet)

    def test_theme_collection_failure_is_separate_and_does_not_touch_watchlist(self):
        import tempfile, json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir()
            watchlist=root/'state/watchlist.json';watchlist.write_text('["AMD"]')
            with patch.object(scout,'BASE_DIR',str(root)), patch.object(scout,'collect_theme_radar',side_effect=RuntimeError('provider')), patch('notify_failure.notify') as notify:
                scout.refresh_theme_research_inbox()
            self.assertEqual(json.loads(watchlist.read_text()),['AMD'])
            inbox=json.loads((root/'state/theme_research_inbox.json').read_text())
            self.assertEqual(inbox['latest']['status'],'unavailable')
            notify.assert_called_once()

    def test_successful_theme_inbox_is_separate_and_added_to_weekly_telegram(self):
        import tempfile, json
        from pathlib import Path
        radar={'observed_at':'2026-10-03T06:00:00+00:00','as_of':'2026-10-02',
            'mode':'research_only','news':[{'id':'a1','title':'Power demand','url':'https://source.test/a'}],
            'leading_industries':[{'industry':'Electric Utilities'}],
            'candidates':[{'symbol':'AAA','industry':'Electric Utilities','relative_strength':{
                '20':{'excess_spy_pp':2.0},'60':{'excess_spy_pp':4.0}}}], 'failures':[]}
        themes=[{'name':'AI power','stance':'tailwind','article_ids':['a1'],
            'industries':['Electric Utilities'],'counterevidence_article_ids':[]}]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir()
            watchlist=root/'state/watchlist.json';watchlist.write_text('["AMD"]')
            (root/'telegram.txt').write_text('Weekly portfolio summary')
            with patch.object(scout,'BASE_DIR',str(root)),patch.object(scout,'collect_theme_radar',return_value=radar),patch.object(scout,'annotate_theme_stories',return_value=themes),patch.dict('os.environ',{'OPENROUTER_API_KEY':'test'}):
                scout.refresh_theme_research_inbox()
            self.assertEqual(json.loads(watchlist.read_text()),['AMD'])
            inbox=json.loads((root/'state/theme_research_inbox.json').read_text())
            self.assertEqual(inbox['latest']['candidates'][0]['pool_status'],'new')
            self.assertIn('AAA',(root/'telegram.txt').read_text())


if __name__=='__main__':
    unittest.main()
