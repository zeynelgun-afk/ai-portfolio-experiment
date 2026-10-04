"""Offline regressions for malformed live-model responses seen in Actions runs."""
import unittest
from unittest.mock import patch
import json

import claim_evidence
import detector
import reassess
from tests.test_evidence_depth import TEXT


class LiveNewsResponseRegressions(unittest.TestCase):
    def setUp(self):
        self.sources = {'N1': {'text': TEXT}}
        self.valid = {
            'impact': 'uncertain', 'claim_ids': [],
            'citations': [{'source_id': 'N1'}],
            'reasoning': 'The excerpt does not establish a thesis-level change.',
            'counterevidence': 'The source does not report a change in guidance.',
            'uncertainty': 'One excerpt cannot establish persistence.',
        }

    def test_valid_alias_only_citation_and_uncertain_verdict_are_accepted(self):
        detector.validate_news_assessment(self.valid, {'MU-1', 'thesis_summary'}, self.sources)

    def test_live_failure_shapes_are_rejected_with_specific_contract_errors(self):
        cases = (
            (dict(self.valid, citations=[{'source_id': 'N999'}]), 'Unknown source_id'),
            (dict(self.valid, citations=[{'source_id': 'N1', 'quote': TEXT}]), 'only a supplied source_id'),
            (dict(self.valid, claim_ids=[{'id': 'MU-1'}]), 'list of claim IDs'),
            (dict(self.valid, claim_ids=['AMD-1']), 'Unknown affected claim'),
            (dict(self.valid, impact={'supports': True}), 'Invalid news impact'),
            (dict(self.valid, uncertainty=''), 'Missing news reasoning'),
            ({k: v for k, v in self.valid.items() if k != 'counterevidence'},
             'missing required fields: counterevidence'),
        )
        for payload, error in cases:
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                detector.validate_news_assessment(payload, {'MU-1', 'thesis_summary'}, self.sources)

    def test_schema_is_forwarded_to_local_validation(self):
        schema = {'name': 'test_contract', 'schema': {
            'type': 'object', 'properties': {'ok': {'type': 'boolean'}},
            'required': ['ok'], 'additionalProperties': False}}
        with patch('llm_transport.complete', return_value='{"ok":true}') as local:
            text, retryable = reassess._single_call('test-model', [], '', schema)
        self.assertEqual(text, '{"ok":true}')
        self.assertFalse(retryable)
        local.assert_called_once_with([], response_schema=schema)


class SemanticReviewResponseRegressions(unittest.TestCase):
    def setUp(self):
        self.sources = {'S1': {'text': TEXT}}
        self.valid = {
            'verdict': 'supported', 'citations': [{'source_id': 'S1'}], 'issues': [],
            'counterargument': 'The source supports this fact, while persistence remains uncertain.',
        }

    def test_supported_review_with_a_real_source_alias_passes(self):
        claim_evidence.validate_semantic_review(self.valid, self.sources)

    def test_unresolved_or_malformed_reviews_cannot_pass(self):
        cases = (
            (dict(self.valid, issues=['Unsupported causal assertion']), 'Unresolved material issues'),
            (dict(self.valid, citations=[{'source_id': 'S999'}]), 'Unknown source_id'),
            (dict(self.valid, citations=None), 'Select at most eight'),
            (dict(self.valid, issues='none'), 'list of strings'),
            (dict(self.valid, counterargument=' '), 'Missing counterargument'),
            (dict(self.valid, verdict={'supported': True}), 'Invalid semantic review verdict'),
        )
        for payload, error in cases:
            with self.subTest(payload=payload):
                if error is None:
                    claim_evidence.validate_semantic_review(payload, self.sources)
                else:
                    with self.assertRaisesRegex(ValueError, error):
                        claim_evidence.validate_semantic_review(payload, self.sources)

    def test_uncertain_verdict_is_valid_json_but_does_not_approve_the_draft(self):
        payload = dict(self.valid, verdict='uncertain')
        with patch.object(reassess, 'call_llm', return_value=(payload, 'ok')):
            with self.assertRaisesRegex(ValueError, 'did not support the draft'):
                claim_evidence.semantic_review(
                    {'assessment': 'A material claim.'},
                    {'MU': {'source_documents': {'news:test': {'text': TEXT}}}},
                    {}, 'test-key', 'test-model')


if __name__ == '__main__':
    unittest.main()
