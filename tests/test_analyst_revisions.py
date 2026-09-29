import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import pandas as pd
import analyst_revisions as ar
import detector
import evidence
import market_data

NOW = datetime(2026, 9, 29, 15, tzinfo=timezone.utc)


def row(firm, target, age, **extra):
    return dict(symbol='MU', analystCompany=firm, analystName='Researcher',
                adjPriceTarget=target, priceTarget=target, priceWhenPosted=90,
                publishedDate=(NOW-timedelta(days=age)).isoformat(),
                newsURL='https://example.org/target', newsTitle='Target review', **extra)


def sample():
    return [row('Alpha', 100, 40), row('Alpha', 120, 2),
            row('Beta', 100, 35), row('Beta', 110, 1)]


class Revisions(unittest.TestCase):
    def report(self, rows=None):
        return ar.analyze('MU', sample() if rows is None else rows, NOW, True)

    def test_matched_firms_and_windows(self):
        report = self.report()
        self.assertEqual(report['direction'], 'up')
        self.assertEqual(report['windows']['30']['up_firms'], 2)
        self.assertAlmostEqual(report['windows']['30']['median_revision_pct'], 15)
        self.assertEqual(len(report['windows']['7']['revisions']), 2)

    def test_same_firm_many_updates_not_many_votes(self):
        report = self.report([row('Alpha', 100, 35), row('Alpha', 110, 4), row('Alpha', 120, 1)])
        self.assertEqual(report['windows']['30']['up_firms'], 1)
        self.assertEqual(report['direction'], 'mixed_or_insufficient')

    def test_syndication_and_reiteration_do_not_create_new_revision(self):
        rows = sample()
        duplicate = dict(rows[1], newsURL='https://other.example/target')
        report = self.report(rows+[duplicate, row('Alpha', 120, 1)])
        self.assertEqual([r['id'] for r in report['windows']['30']['revisions']],
                         [r['id'] for r in self.report()['windows']['30']['revisions']])

    def test_aliases_share_one_vote(self):
        report = self.report([row('J.P. Morgan', 100, 40), row('JPMorgan', 120, 2)])
        self.assertEqual(report['windows']['30']['up_firms'], 1)

    def test_unpaired_target_never_invents_revision(self):
        report = self.report([row('Alpha', 500, 1), row('Beta', 600, 1)])
        self.assertEqual(report['windows']['30']['matched_firms'], 0)
        self.assertEqual(report['coverage']['unpaired_segments'], 2)

    def test_reinitiated_coverage_does_not_count_as_a_revision(self):
        rows = sample()
        rows[1]['newsTitle'] = 'MU initiated with an Overweight at Alpha'
        report = self.report(rows)
        self.assertEqual(report['windows']['30']['up_firms'], 1)
        self.assertEqual(report['windows']['30']['initiated_or_resumed_firms'], 1)
        self.assertIsNone(ar.review_trigger('MU', report, {}, NOW))

    def test_conflicting_firm_attribution_is_quarantined(self):
        rows = sample()
        rows[1]['newsTitle'] = 'MU target raised at Beta'
        report = self.report(rows)
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(report['windows']['30']['up_firms'], 1)
        self.assertTrue(report['attribution_conflicts'])
        self.assertIsNone(ar.review_trigger('MU', report, {}, NOW))

    def test_decreases_and_mixed_direction(self):
        self.assertEqual(self.report([row('Alpha', 120, 40), row('Alpha', 100, 1), row('Beta', 120, 40), row('Beta', 100, 1)])['direction'], 'down')
        self.assertEqual(self.report([row('Alpha', 100, 40), row('Alpha', 120, 1), row('Beta', 120, 40), row('Beta', 100, 1)])['direction'], 'mixed_or_insufficient')

    def test_conflicting_same_day_blocks_trigger(self):
        report = self.report(sample()+[row('Alpha', 125, 2)])
        self.assertEqual(report['status'], 'incomplete')
        self.assertIsNone(ar.review_trigger('MU', report, {}, NOW))

    def test_old_conflicts_do_not_block_fresh_independent_pairs(self):
        report = self.report(sample()+[row('Old firm', 100, 200), row('Old firm', 110, 200)])
        self.assertEqual(report['status'], 'ok')
        self.assertTrue(report['coverage']['conflicts'])
        self.assertFalse(report['coverage']['recent_conflicts'])
        self.assertIsNotNone(ar.review_trigger('MU', report, {}, NOW))

    def test_no_records_are_unknown_and_reiterations_are_unchanged(self):
        self.assertEqual(self.report([])['status'], 'no_records')
        report = self.report([row('Alpha', 100, 40), row('Alpha', 100, 1), row('New', 500, 1)])
        self.assertEqual(report['windows']['30']['unchanged_firms'], 1)
        self.assertEqual(report['windows']['30']['unpaired_firms'], 1)
        self.assertEqual(report['windows']['30']['up_firms'], 0)

    def test_wrong_issuer_future_and_missing_adjustment_rejected(self):
        bad = [dict(row('Other', 200, 1), symbol='AMD'), row('Future', 200, -1), dict(row('Raw', 200, 1), adjPriceTarget=None)]
        report = self.report(sample()+bad)
        self.assertEqual(report['coverage']['rejected_rows'], 3)
        self.assertIsNone(ar.review_trigger('MU', report, {}, NOW))

    def test_split_does_not_create_revision(self):
        rows = [dict(row('Alpha', 100, 40), adjPriceTarget=50), row('Alpha', 50, 1)]
        self.assertEqual(self.report(rows)['windows']['30']['matched_firms'], 0)

    def test_restatement_does_not_change_identity(self):
        original = self.report()
        rows = sample()
        for r in rows: r['adjPriceTarget'] /= 2
        self.assertEqual([r['id'] for r in original['windows']['30']['revisions']],
                         [r['id'] for r in self.report(rows)['windows']['30']['revisions']])

    def test_triggers_are_review_only_and_acknowledged_once(self):
        report = self.report()
        trigger = ar.review_trigger('MU', report, {}, NOW)
        self.assertEqual(trigger['severity'], 'thesis')
        self.assertNotIn('material_event_ids', trigger)
        locks = {key: NOW.isoformat() for key in trigger['analyst_event_keys']}
        self.assertIsNone(ar.review_trigger('MU', report, locks, NOW))
        self.assertIsNone(ar.review_trigger('MU', report, {}, NOW+timedelta(days=1)))

    def test_detector_routes_both_directions_without_execution_override(self):
        report = self.report()
        theses = {'MU': {'claims': [], 'thesis_summary': 'Demand'}}
        for direction in ('up', 'down'):
            report['direction'] = direction
            for r in report['windows']['30']['revisions']: r['revision_pct'] = 10 if direction == 'up' else -10
            output = detector.run(theses, {'MU': {'analyst_revisions': report}}, {}, {}, {}, NOW, assess_news=False)
            self.assertEqual(output['code'], 20)
            self.assertNotIn('material_event_ids', output['triggered'][0])

    def test_coverage_failure_daily_health_signal(self):
        report = self.report(); report['status'] = 'incomplete'
        output = detector.run({'MU': {'claims': []}}, {'MU': {'analyst_revisions': report, 'analyst_refreshed': True}}, {}, {}, {}, NOW, assess_news=False)
        self.assertTrue(output['news_errors'])
        self.assertEqual(output['code'], 0)

    def test_numeric_summary_has_bound_evidence(self):
        data = {'MU': {}}
        ar.attach(data['MU'], self.report())
        facts = evidence.ledger(data, NOW.isoformat(), 'test')
        self.assertEqual(facts['MU.analyst_up_firms_30d']['value'], 2)
        self.assertEqual(len(data['MU']['source_documents']), 2)


class Collection(unittest.TestCase):
    def test_pagination_and_empty_terminal_page(self):
        fetch = Mock(side_effect=[sample()*25, [], []])
        report = ar.collect('MU', NOW, fetch=fetch)
        self.assertTrue(report['coverage']['pagination_complete'])
        self.assertEqual(fetch.call_count, 3)
        self.assertTrue(fetch.call_args_list[1].kwargs['allow_empty'])

    def test_repeated_page_marks_incomplete(self):
        fetch = Mock(side_effect=[sample()*25, sample()*25, []])
        report = ar.collect('MU', NOW, fetch=fetch)
        self.assertEqual(report['status'], 'incomplete')

    def test_failure_does_not_expose_provider_secret(self):
        report = ar.collect('MU', NOW, fetch=Mock(side_effect=market_data.ProviderError('secret-url')))
        self.assertEqual(report['status'], 'unavailable')
        self.assertNotIn('secret-url', str(report))

    def test_daily_cache_is_immutable_and_no_second_request(self):
        state = {}; fetch = Mock(side_effect=[sample(), []])
        report, changed = ar.refresh('MU', NOW, state, fetch)
        self.assertTrue(changed)
        report['direction'] = 'changed'
        cached, changed = ar.refresh('MU', NOW+timedelta(hours=1), state, fetch)
        self.assertFalse(changed)
        self.assertEqual(cached['direction'], 'up')
        self.assertEqual(fetch.call_count, 2)

    def test_estimates_compare_same_period_only(self):
        prior = {'observed_at': (NOW-timedelta(days=1)).isoformat(), 'estimates': {'2027-09-30': {'epsAvg': 10, 'revenueAvg': 100}}}
        fetch = Mock(side_effect=[sample(), [{'symbol': 'MU', 'date': '2027-09-30', 'epsAvg': 11, 'revenueAvg': 120}, {'symbol': 'MU', 'date': '2028-09-30', 'epsAvg': 15}]])
        report = ar.collect('MU', NOW, prior, fetch)
        self.assertEqual(report['estimate_changes']['periods']['2027-09-30']['epsAvg']['change_pct'], 10)
        self.assertIsNone(report['estimate_changes']['periods']['2028-09-30']['epsAvg']['change_pct'])

    def test_zero_and_negative_earnings_changes(self):
        prior = {'estimates': {'2027-09-30': {'epsAvg': -2, 'revenueAvg': 0}}}
        fetch = Mock(side_effect=[sample(), [{'symbol': 'MU', 'date': '2027-09-30', 'epsAvg': -1, 'revenueAvg': 120}]])
        report = ar.collect('MU', NOW, prior, fetch)
        self.assertEqual(report['estimate_changes']['periods']['2027-09-30']['epsAvg']['change_pct'], 50)
        self.assertIsNone(report['estimate_changes']['periods']['2027-09-30']['revenueAvg']['change_pct'])

    def test_forward_measurement_starts_after_observation(self):
        days = ar.forward_days(NOW.date())
        histories = {s: pd.DataFrame({'total_close': [100+i*(2 if s=='MU' else 1) for i in range(len(days))]}, index=pd.to_datetime(days)) for s in ('MU', 'SPY')}
        results = ar.forward_score(ar.analyze('MU', sample(), NOW, True), histories)
        self.assertAlmostEqual(results[0]['return_pct'], 40)
        self.assertAlmostEqual(results[0]['excess_spy_pp'], 20)
        self.assertGreater(results[0]['baseline_date'], NOW.date().isoformat())
        self.assertTrue(all(r['status']=='pending' for r in ar.forward_score(ar.analyze('MU', sample(), NOW, True), {})))

    def test_published_cohorts_deduplicate_daily_repetitions(self):
        report = ar.collect('MU', NOW, fetch=Mock(side_effect=[sample(), []]))
        later = copy.deepcopy(report); later['observed_at'] = (NOW+timedelta(days=1)).isoformat()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'state').mkdir()
            ar.publish({'first': report, 'second': later}, root, {})
            import json
            data = json.loads((root/'state/analyst_revision_performance.json').read_text())
            self.assertEqual(len(data['cohorts']), 1)
            self.assertIn('Mature endpoints: 0', (root/'ANALYST_REVISIONS.md').read_text())


class DriverReview(unittest.TestCase):
    def review(self):
        return {key: {'assessment': 'Evidence is unavailable for this explanation.', 'evidence_status': 'unknown', 'source_ids': []}
                for key in ('earnings', 'company_news', 'sector_theme', 'valuation')}

    def test_news_context_is_valid_without_improving_earnings(self):
        review = self.review()
        review['company_news'] = {'assessment': 'A new contract may support demand; its link to the target change is a hypothesis.',
                                  'evidence_status': 'context_only', 'source_ids': ['news:contract']}
        data = {'MU': {'source_documents': {'news:contract': {'symbol': 'MU', 'text': 'Contract announcement'}}}}
        self.assertEqual(ar.validate_review(review, 'MU', data, {})['earnings']['evidence_status'], 'unknown')

    def test_invisible_provider_formatting_is_removed_but_numbers_stay_exact(self):
        import claim_evidence as ce
        raw = 'The company reported revenue of 120 million and '\
              'confirmed a new customer agreement with delivery scheduled next quarter.'
        invisible = raw.replace('company', 'company'+chr(0x200B)).replace('reported', chr(0x2060)+'reported')
        sources = ce.documents('MU', [{'symbol': 'MU', 'url': 'https://example.org/news', 'publishedDate': NOW.isoformat(), 'text': invisible}])
        key = next(iter(sources))
        self.assertEqual(sources[key]['raw_text'], invisible)
        self.assertEqual(sources[key]['text'], raw)
        ce.validate_citations([{'source_id': key, 'quote': raw}], sources)
        with self.assertRaises(ValueError):
            ce.validate_citations([{'source_id': key, 'quote': raw.replace('120', '121')}], sources)

    def test_price_evidence_cannot_be_a_reported_analyst_reason(self):
        review = self.review()
        review['sector_theme'] = {'assessment': 'The sector rose.', 'evidence_status': 'reported_reason', 'source_ids': ['SMH.price']}
        with self.assertRaisesRegex(ValueError, 'attributed'):
            ar.validate_review(review, 'MU', {}, {'SMH.price': {'symbol': 'SMH'}})

    def test_reviewer_copy_excerpt_remains_exact_and_does_not_mutate_sources(self):
        import json, claim_evidence, reassess
        data = {'MU': {'source_documents': {'news:source': {'symbol': 'MU', 'text': 'A sufficiently detailed original source excerpt for exact citation checks.'}}}}
        before = copy.deepcopy(data)
        facts = {'MU.price': {'symbol': 'MU', 'metric': 'price', 'value': 100, 'unit': 'USD', 'as_of': NOW.isoformat(), 'source': 'test'}}
        def model(*args, **kwargs):
            sources = json.loads(args[2])['sources']
            self.assertEqual(sources['MU.price']['metadata'], facts['MU.price'])
            quote = sources['MU.price']['citation_excerpt']
            output = {'verdict': 'supported', 'citations': [{'source_id': 'MU.price', 'quote': quote}], 'issues': [], 'counterargument': 'The target remains uncertain.'}
            kwargs['response_validator'](output)
            output['citations'][0]['quote'] = 'This quote was rewritten and is not evidence.'
            with self.assertRaises(ValueError): kwargs['response_validator'](output)
            output['citations'][0]['quote'] = quote
            return output, 'ok'
        with patch.object(reassess, 'call_llm', side_effect=model):
            claim_evidence.semantic_review({'assessment': 'Measured price'}, data, facts, 'test', 'test')
        self.assertEqual(data, before)

    def test_missing_axis_and_wrong_issuer_are_rejected(self):
        review = self.review(); del review['sector_theme']
        with self.assertRaises(ValueError): ar.validate_review(review, 'MU', {}, {})
        review = self.review(); review['valuation'].update(evidence_status='context_only', source_ids=['AMD.price'])
        with self.assertRaises(ValueError): ar.validate_review(review, 'MU', {}, {'AMD.price': {'symbol': 'AMD'}})

    def test_full_reassessment_preserves_axes_and_acknowledges_events(self):
        import json, os, reassess
        from tests.test_decision_lifecycle import thesis, data, monitor
        from tests.test_execute_trade import portfolio
        report = ar.collect('MU', NOW, fetch=Mock(side_effect=[sample(), []]))
        rows = data(); ar.attach(rows['MU'], report)
        trigger = ar.review_trigger('MU', report, {}, NOW)
        m = monitor(); m['next_review_at'] = (NOW+timedelta(days=1)).isoformat()
        proposal = {'thesis_assessment': 'New targets justify review; the causes remain uncertain.',
                    'new_thesis_summary': 'Demand supports the position.', 'claim_statuses': {'MU-1': 'valid'},
                    'monitoring': m, 'analyst_review': self.review(),
                    'decision': {'action': 'HOLD', 'reasoning': 'Wait for confirmation of competing explanations.',
                                 'falsifier': 'A breach of the monitored downside condition requires review.'}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); state = root/'state'; state.mkdir()
            (root/'theses.json').write_text(json.dumps({'MU': thesis()})); (root/'portfolio.json').write_text(json.dumps(portfolio()))
            (state/'violations.json').write_text(json.dumps({'lifecycle_version': 1, 'checked_at': NOW.isoformat(), 'market_open': True,
                                                           'data': rows, 'triggered': [trigger]}))
            with patch.object(reassess, 'BASE', str(root)), patch.object(reassess, 'THESES_PATH', str(root/'theses.json')), patch.object(reassess, 'PORTFOLIO_PATH', str(root/'portfolio.json')), patch.object(reassess, 'now_utc', return_value=NOW), patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test'}), patch('sys.argv', ['reassess', '--code', '20', '--state-dir', str(state)]), patch.object(reassess, '_single_call', return_value=(json.dumps(proposal), False)), patch('claim_evidence.semantic_review', return_value={'verdict': 'supported'}):
                self.assertEqual(reassess.main(), 0)
            final = json.loads((root/'theses.json').read_text())['MU']
            self.assertEqual(set(final['analyst_review']), set(self.review()))
            cooldown = json.loads((state/'cooldown.json').read_text())
            self.assertIsNone(ar.review_trigger('MU', report, cooldown, NOW))
            decision = json.loads((state/'pending_decision.json').read_text())['decisions'][0]
            self.assertEqual(decision['action'], 'HOLD')
            self.assertEqual(decision['event_ids'], [])
            self.assertEqual(json.loads((root/'portfolio.json').read_text()), portfolio())


if __name__ == '__main__': unittest.main()
