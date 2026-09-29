import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scout
from watchlist_telegram import change_message, delivered_state


class WatchlistTelegramTests(unittest.TestCase):
    def test_first_message_contains_full_pool_and_disclaimer(self):
        message=change_message(['AMD','MU','AMD'],None,'2026-09-29')
        self.assertIn('AMD · MU',message)
        self.assertIn('İlk havuz bildirimi',message)
        self.assertIn('araştırma havuzudur',message)

    def test_change_message_contains_additions_removals_and_new_full_pool(self):
        message=change_message(['AMD','NVDA'],['AMD','MU'],'2026-09-29')
        self.assertIn('Yeni: NVDA',message)
        self.assertIn('Çıkan: MU',message)
        self.assertIn('AMD · NVDA',message)
        self.assertIsNone(change_message(['AMD'],['AMD']))

    def test_scout_delivers_only_changes_and_persists_only_after_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir()
            with patch.object(scout,'BASE_DIR',str(root)),patch('notify_failure.notify') as notify:
                self.assertTrue(scout.deliver_watchlist_if_changed(['AMD','MU']))
                self.assertFalse(scout.deliver_watchlist_if_changed(['MU','AMD']))
                self.assertTrue(scout.deliver_watchlist_if_changed(['AMD','NVDA']))
            self.assertEqual(notify.call_count,2)
            self.assertIn('Yeni: NVDA',notify.call_args.args[0] if notify.call_args.args else notify.call_args.kwargs['message'])
            state=json.loads((root/'state/telegram_watchlist_state.json').read_text())
            self.assertEqual(state['symbols'],['AMD','NVDA'])
            self.assertEqual(state['delivery_status'],'delivered')

    def test_failed_delivery_does_not_advance_last_delivered_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir()
            with patch.object(scout,'BASE_DIR',str(root)),patch('notify_failure.notify',side_effect=RuntimeError('offline')):
                with self.assertRaises(RuntimeError):scout.deliver_watchlist_if_changed(['AMD'])
            self.assertFalse((root/'state/telegram_watchlist_state.json').exists())


if __name__=='__main__':
    unittest.main()
