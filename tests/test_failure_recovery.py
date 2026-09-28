"""Regression tests for failed news checks, audit failures and Telegram fallback."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import detector
import notify_failure
import reviewers


class NewsRecoveryTest(unittest.TestCase):
    def check(self, response):
        seen = {}
        news = [{'title': 'headline', 'publishedDate': '2026-09-28T12:00:00Z'}]
        with patch.object(detector, 'check_news_shock', return_value=response) as check:
            report = detector.run(
                {'MU': {'thesis_summary': 'test', 'claims': []}},
                {'MU': {'recent_news': news}}, {}, {}, {},
                datetime(2026, 9, 28, 15, tzinfo=timezone.utc),
                last_news={}, new_last_news=seen)
        return report, seen

    def test_failed_assessment_stays_pending(self):
        report, seen = self.check((None, 'timeout'))
        self.assertEqual(seen, {})
        self.assertEqual(report['news_errors'][0]['symbol'], 'MU')
        self.assertEqual(report['code'], 0)

    def test_no_shock_is_persisted_even_without_price_changes(self):
        report, seen = self.check((False, ''))
        self.assertIn('MU', seen)
        self.assertTrue(report['state_changed'])
        self.assertEqual(report['news_errors'], [])

    def test_shock_triggers_thesis_reassessment(self):
        report, seen = self.check((True, 'News Shock: headline'))
        self.assertEqual(report['code'], 20)
        self.assertIn('MU', seen)

    def test_timeout_is_not_a_negative_assessment(self):
        with patch.object(detector, 'env', return_value='test'), patch(
                'urllib.request.urlopen', side_effect=TimeoutError('outage')):
            status, _ = detector.check_news_shock('MU', 'test', [{'title': 'test'}])
        self.assertIsNone(status)

    def test_ambiguous_answer_is_retried(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {'choices': [{'message': {'content': 'YES OR NO?'}}]}).encode()
        with patch.object(detector, 'env', return_value='test'), patch(
                'urllib.request.urlopen', return_value=response):
            status, _ = detector.check_news_shock('MU', 'test', [{'title': 'test'}])
        self.assertIsNone(status)

    def test_dry_measurement_does_not_call_news_model(self):
        with patch.object(detector, 'check_news_shock') as check:
            detector.run({'MU': {'claims': []}}, {'MU': {'recent_news': [
                {'publishedDate': '2026-09-28', 'title': 'test'}]}}, {}, {}, {},
                datetime(2026, 9, 28, tzinfo=timezone.utc),
                last_news={}, new_last_news={}, assess_news=False)
        check.assert_not_called()


class ReviewFailureTest(unittest.TestCase):
    def test_missing_key_fails_explicit_review(self):
        with patch.object(reviewers, 'env', return_value=''):
            with self.assertRaisesRegex(RuntimeError, 'required'):
                reviewers.review({}, '/unused')

    def test_unusable_auditor_cannot_pass_as_empty_consensus(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
                reviewers, 'env', return_value='test'), patch.object(
                reviewers, 'build_prompt', return_value='test'), patch.object(
                reviewers, 'run_auditor', side_effect=[None, []]), patch.object(
                reviewers, 'AUDIT_LOG_PATH', str(Path(directory)/'audit.md')):
            with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                reviewers.review({}, directory)
            self.assertIn('no consensus possible', (Path(directory)/'audit.md').read_text())


class TelegramFailureTest(unittest.TestCase):
    ENV = {'TELEGRAM_BOT_TOKEN': 'secret-test-token', 'TELEGRAM_CHAT_ID': 'group',
           'TELEGRAM_CHAT_ID_DM': 'dm', 'SOURCE_WORKFLOW': 'Intraday Detector',
           'SOURCE_RUN_URL': 'https://github.com/owner/repo/actions/runs/123'}

    def response(self, ok=True):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        response.__enter__.return_value.read.return_value = json.dumps({'ok': ok}).encode()
        return response

    def test_primary_success_does_not_duplicate_to_dm(self):
        opener = MagicMock(return_value=self.response())
        notify_failure.notify(self.ENV, opener)
        self.assertEqual(opener.call_count, 1)
        from urllib.parse import parse_qs
        payload = parse_qs(opener.call_args.args[0].data.decode())
        self.assertEqual(payload['chat_id'], ['group'])
        self.assertIn(self.ENV['SOURCE_RUN_URL'], payload['text'][0])

    def test_primary_failure_falls_back_to_dm(self):
        opener = MagicMock(side_effect=[TimeoutError(), TimeoutError(), self.response()])
        notify_failure.notify(self.ENV, opener)
        self.assertEqual(opener.call_count, 3)
        self.assertIn(b'chat_id=dm', opener.call_args.args[0].data)

    def test_api_ok_false_is_not_delivery(self):
        with self.assertRaisesRegex(RuntimeError, 'no destination'):
            notify_failure.notify(self.ENV, MagicMock(return_value=self.response(False)))

    def test_failures_do_not_leak_token_in_exception_urls(self):
        opener = MagicMock(side_effect=RuntimeError('https://api.telegram.org/botsecret-test-token'))
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaisesRegex(RuntimeError, 'no destination') as error:
            notify_failure.notify(self.ENV, opener)
        self.assertNotIn('secret-test-token', output.getvalue() + str(error.exception))

    def test_missing_configuration_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'missing'):
            notify_failure.notify({}, MagicMock())

    def test_missing_step_details_do_not_block_alert(self):
        opener = MagicMock(return_value=self.response())
        notify_failure.notify(dict(self.ENV, FAILED_STEPS_FILE='/nonexistent/steps'), opener)
        self.assertEqual(opener.call_count, 1)
