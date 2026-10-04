import copy
import unittest
from unittest.mock import patch
import llm_context
import reassess


class SpendTests(unittest.TestCase):
    def test_projection_keeps_facts_and_original_sources(self):
        data = {'ABC': {'daily_returns': [1]*500,
            'analyst_revisions': {'windows': {'90': {'up_firms': 2, 'revisions': [1]*500}}},
            'source_documents': {str(i): {'text': 'a'*4000, 'published_at': str(i)} for i in range(20)}}}
        original = copy.deepcopy(data)
        view = llm_context.research_view(data)
        self.assertEqual(data, original)
        self.assertEqual(view['ABC']['analyst_revisions']['windows']['90'], {'up_firms': 2})
        self.assertEqual(len(view['ABC']['source_documents']), 8)
        self.assertTrue(all(d['text_truncated'] for d in view['ABC']['source_documents'].values()))

    def test_oversize_request_never_reaches_provider(self):
        with patch('llm_transport.complete') as network:
            self.assertEqual(reassess._single_call('model', [{'role':'user','content':'x'*1500001}], 'fake'), (None, False))
            network.assert_not_called()

    def test_retry_only_sends_latest_correction(self):
        seen = []
        def provider(model, messages, api_key):
            seen.append(copy.deepcopy(messages))
            return ('{"bad": "' + 'x'*40000 + '"}', False)
        with patch.object(reassess, '_single_call', side_effect=provider):
            reassess._call_llm('model', 'system', 'user', 'fake',
                response_validator=lambda payload: (_ for _ in ()).throw(ValueError('bad schema')))
        self.assertEqual([len(messages) for messages in seen], [2, 4, 4])
        self.assertLessEqual(len(seen[-1][-2]['content']), 32000)

    def test_small_request_uses_subscription_transport(self):
        with patch('llm_transport.complete', return_value='{}') as inference:
            self.assertEqual(reassess._single_call('model', [{'role':'user','content':'small'}], 'fake'), ('{}', False))
            inference.assert_called_once()
