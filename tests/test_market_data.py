import copy
from datetime import datetime, timezone
import unittest
from unittest.mock import patch, Mock

import pandas as pd
import market_data as md
from provider_health import summary

NOW=datetime(2026,9,28,15,tzinfo=timezone.utc)
ROWS=[{'symbol':'AMD','date':'2026-09-25','close':100,'volume':1000},
      {'symbol':'AMD','date':'2026-09-24','close':99,'volume':900}]


class ProviderTests(unittest.TestCase):
    def setUp(self):md.EVENTS.clear()

    def test_primary_success_never_calls_backup(self):
        backup=Mock(side_effect=AssertionError('Backup must remain idle'))
        self.assertEqual(md.select('AMD','test',lambda:42,backup),(42,'FMP'))
        backup.assert_not_called()

    def test_primary_failure_calls_backup_once(self):
        primary=Mock(side_effect=md.ProviderError('FMP HTTP 403'));backup=Mock(return_value=42)
        self.assertEqual(md.select('AMD','test',primary,backup),(42,'yfinance'))
        backup.assert_called_once()
        self.assertEqual(md.EVENTS[-1]['reason'],'FMP HTTP 403')

    def test_primary_is_retried_on_next_request_after_outage(self):
        backup=Mock(return_value=42)
        md.select('AMD','test',Mock(side_effect=md.ProviderError('outage')),backup)
        self.assertEqual(md.select('AMD','test',lambda:43,backup),(43,'FMP'))
        backup.assert_called_once()

    def test_both_fail_closed_and_do_not_print_secret_url(self):
        with self.assertRaises(md.ProviderError) as caught:
            md.select('AMD','test',Mock(side_effect=RuntimeError('https://host?apikey=secret')),Mock(side_effect=ValueError('secret')))
        self.assertNotIn('secret',str(caught.exception))
        self.assertNotIn('secret',str(md.EVENTS))

    def test_primary_history_is_normalized_without_yahoo(self):
        with patch.object(md,'fmp',return_value=copy.deepcopy(ROWS)), patch('yfinance.Ticker') as yahoo:
            frame=md.history('AMD',now=NOW)
        yahoo.assert_not_called()
        self.assertEqual(frame.attrs['provider'],'FMP')
        self.assertEqual(frame.index[-1].date().isoformat(),'2026-09-25')
        self.assertEqual(frame['Close'].iloc[-1],100)

    def test_stale_primary_history_uses_whole_backup_series(self):
        stale=[dict(ROWS[1])]
        backup=pd.DataFrame({'Close':[99,101],'Volume':[900,1000]},index=pd.to_datetime(['2026-09-24','2026-09-25']))
        with patch.object(md,'fmp',return_value=stale), patch('yfinance.Ticker') as yahoo:
            yahoo.return_value.history.return_value=backup
            frame=md.history('AMD',now=NOW)
        self.assertEqual(frame.attrs['provider'],'yfinance')
        self.assertEqual(frame['Close'].iloc[-1],101)
        yahoo.assert_called_once_with('AMD')

    def test_wrong_issuer_is_not_accepted(self):
        with patch.object(md,'fmp',return_value=[dict(ROWS[0],symbol='MU')]),patch('yfinance.Ticker') as yahoo:
            yahoo.return_value.history.side_effect=ValueError()
            with self.assertRaises(md.ProviderError):md.history('AMD',now=NOW)
        self.assertEqual(md.EVENTS[-1]['provider'],'unavailable')

    def test_bad_numeric_data_and_duplicate_dates_rejected(self):
        for rows in ([dict(ROWS[0],close=float('nan'))], [ROWS[0],ROWS[0]], [dict(ROWS[0],close=-1)]):
            with self.subTest(rows=rows),patch.object(md,'fmp',return_value=rows),patch('yfinance.Ticker') as yahoo:
                yahoo.return_value.history.side_effect=ValueError()
                with self.assertRaises(md.ProviderError):md.history('AMD',now=NOW)

    def test_intraday_timezone_session_filter_and_single_day_volume(self):
        rows=[{'date':'2026-09-28 10:55:00','close':100,'volume':5},
              {'date':'2026-09-28 09:00:00','close':99,'volume':100},
              {'date':'2026-09-25 15:55:00','close':99,'volume':200}]
        with patch.object(md,'fmp',return_value=rows),patch('yfinance.Ticker') as yahoo:
            frame=md.history('AMD','1d','5m',now=NOW)
        self.assertEqual(frame['Volume'].sum(),5)
        self.assertEqual(frame.index[-1].hour,14)
        yahoo.assert_not_called()

    def test_stale_backup_intraday_also_rejected(self):
        old=pd.DataFrame({'Close':[100],'Volume':[5]},index=pd.to_datetime(['2026-09-28T13:30Z']))
        with patch.object(md,'fmp',side_effect=md.ProviderError('failed')),patch('yfinance.Ticker') as yahoo:
            yahoo.return_value.history.return_value=old
            with self.assertRaises(md.ProviderError):md.history('AMD','1d','5m',now=NOW)

    def test_fundamentals_do_not_fetch_yahoo_for_optional_forward_pe(self):
        def fmp(endpoint,**kwargs):
            return [{'symbol':'AMD','priceToEarningsRatioTTM':22}] if endpoint=='ratios-ttm' else [{'symbol':'AMD','marketCap':1000}]
        with patch.object(md,'fmp',side_effect=fmp),patch('yfinance.Ticker') as yahoo:
            ticker=md.Ticker('AMD');info=ticker.info
        self.assertIsNone(info['forwardPE'])
        self.assertEqual(info['trailingPE'],22)
        self.assertEqual(ticker.providers['fundamentals'],'FMP')
        yahoo.assert_not_called()

    def test_news_primary_success_does_not_fetch_yahoo(self):
        with patch.object(md,'fmp',return_value=[{'symbol':'AMD','title':'Headline','publishedDate':'2026-09-28 12:00:00'}]),patch('yfinance.Ticker') as yahoo:
            rows,provider=md.news('AMD')
        self.assertEqual(provider,'FMP');yahoo.assert_not_called()

    def test_news_failover_normalizes_yahoo_schema(self):
        with patch.object(md,'fmp',side_effect=md.ProviderError('failed')),patch('yfinance.Ticker') as yahoo:
            yahoo.return_value.news=[{'content':{'title':'Headline','pubDate':'2026-09-28T12:00:00Z','canonicalUrl':{'url':'https://example.org'}}}]
            rows,provider=md.news('AMD')
        self.assertEqual(provider,'yfinance')
        self.assertEqual(rows[0]['symbol'],'AMD')
        self.assertEqual(rows[0]['title'],'Headline')

    def test_no_fallback_alert_when_primary_healthy(self):
        self.assertIsNone(summary([{'symbol':'AMD','dataset':'prices','provider':'FMP'}]))

    def test_one_summary_identifies_fallback_and_unavailable_fields(self):
        self.assertIn('yfinance',summary([{'symbol':'AMD','dataset':'prices','provider':'yfinance'}]))
        self.assertIn('unavailable',summary([{'symbol':'AMD','dataset':'prices','provider':'unavailable'}]))


if __name__=='__main__':unittest.main()
