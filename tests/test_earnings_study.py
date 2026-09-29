import unittest
from datetime import datetime, timezone
import pandas as pd
import pandas_market_calendars as calendars
from earnings_study import classify, evaluate, measure


class EarningsStudyTests(unittest.TestCase):
    def setUp(self):
        self.days = calendars.get_calendar('NYSE').valid_days('2025-01-01', '2025-09-30').tz_localize(None)
        self.stock = pd.DataFrame({'total_close': 100.0}, index=self.days)
        self.rows = {'TEST': [dict(symbol='TEST', date='2025-01-17', epsActual=-.1,
                                  epsEstimated=-.2, revenueActual=110, revenueEstimated=100)]}
        self.now = datetime(2025, 9, 30, 22, tzinfo=timezone.utc)

    def test_negative_eps_beat_and_missing_not_zero(self):
        r = self.rows['TEST'][0]
        self.assertEqual(classify(r), 'eps_and_revenue_beat')
        self.assertEqual(classify({**r, 'epsEstimated': None}), 'missing_consensus_or_actual')
        self.assertEqual(classify({**r, 'epsActual': float('nan')}), 'missing_consensus_or_actual')

    def test_holiday_entry_and_exact_horizon(self):
        out = evaluate(self.rows, {'TEST': self.stock, 'IWM': self.stock}, self.now)
        result = out['events'][0]['outcomes']['20']
        self.assertEqual(result['entry_date'], '2025-01-21')
        self.assertEqual(result['end_date'], '2025-02-19')
        self.assertEqual(result['net_return_pct_by_roundtrip_bps']['100'], -1)
        self.assertFalse(out['strategy_validated'])

    def test_missing_interior_bar_is_not_silently_filled(self):
        broken = self.stock.drop(self.days[6])
        self.assertEqual(measure(broken, self.stock, self.days, self.days[0], self.days[20], [25])['status'],
                         'incomplete_price_path')

    def test_drawdown_includes_entry_peak(self):
        stock = self.stock.copy()
        stock.iloc[1, 0] = 50
        out = measure(stock, self.stock, self.days, self.days[0], self.days[20], [0])
        self.assertEqual(out['gross_return_pct'], 0)
        self.assertEqual(out['max_close_drawdown_pct'], -50)

    def test_duplicate_and_issuer_mismatch_rejected(self):
        rows = {'TEST': self.rows['TEST']*2}
        result = evaluate(rows, {}, self.now)
        self.assertTrue(all(r['status'] == 'issuer_or_duplicate_event' for r in result['events']))
        self.rows['TEST'][0]['symbol'] = 'OTHER'
        self.assertEqual(evaluate(self.rows, {}, self.now)['events'][0]['status'], 'issuer_or_duplicate_event')

    def test_unfinished_horizon_pending(self):
        now = datetime(2025, 1, 22, 22, tzinfo=timezone.utc)
        result = evaluate(self.rows, {'TEST': self.stock, 'IWM': self.stock}, now)
        self.assertEqual(result['events'][0]['outcomes']['20']['status'], 'pending')

    def test_next_report_exit_precedes_report(self):
        self.rows['TEST'].append({**self.rows['TEST'][0], 'date': '2025-04-17'})
        result = evaluate(self.rows, {'TEST': self.stock, 'IWM': self.stock}, self.now)
        self.assertEqual(result['events'][0]['outcomes']['before_next_earnings']['end_date'], '2025-04-16')

    def test_offline_replay_is_reproducible_and_refuses_overwrite(self):
        import json
        import sys
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import earnings_study
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = {'observed_at': self.now.isoformat(), 'earnings': self.rows,
                      'histories': {s: {str(k.date()): v for k,v in self.stock.to_dict('index').items()}
                                    for s in ('TEST', 'IWM')}}
            snapshot = root/'inputs.json'
            snapshot.write_text(json.dumps(inputs))
            with patch.object(sys, 'argv', ['study', '--replay', str(snapshot), '--output', str(root/'result')]), \
                 patch('market_data.fmp', side_effect=AssertionError('network forbidden')), \
                 patch('market_data.return_history', side_effect=AssertionError('network forbidden')):
                earnings_study.main()
                saved = json.loads((root/'result/report.json').read_text())
                expected = evaluate(self.rows, {'TEST': self.stock, 'IWM': self.stock}, self.now)
                self.assertEqual(saved['summary'], expected['summary'])
                with self.assertRaises(FileExistsError):
                    earnings_study.main()
