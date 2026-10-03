import copy
import json
import unittest
from unittest.mock import patch
import reassess
import scout

class RecoveryTests(unittest.TestCase):
    def test_semantic_rejection_is_repaired_before_acceptance(self):
        seen=[]
        def call(model,messages,key):
            seen.append(copy.deepcopy(messages))
            return json.dumps({'text':'unsupported' if len(seen)==1 else 'attributed opinion'}),False
        def review(payload):
            if payload['text']=='unsupported':
                raise ValueError('Management guidance has no primary evidence')
        with patch.object(reassess,'_single_call',side_effect=call):
            result,status=reassess.call_llm('m','s','u','key',semantic_validator=review)
        self.assertEqual(status,'ok')
        self.assertEqual(result['text'],'attributed opinion')
        self.assertIn('Management guidance',seen[1][-1]['content'])
        self.assertIn('unsupported',seen[1][-2]['content'])

    def test_semantic_rejection_never_passes_after_retry_limit(self):
        with patch.object(reassess,'_single_call',return_value=('{}',False)) as call:
            result,status=reassess.call_llm('m','s','u','key',
                semantic_validator=lambda _: (_ for _ in ()).throw(ValueError('Unsupported fact')))
        self.assertIsNone(result)
        self.assertEqual(status,'invalid_semantic_evidence')
        self.assertEqual(call.call_count,reassess.MAX_ATTEMPTS)

    def test_theme_validation_error_reaches_retry(self):
        with patch.object(scout,'_theme_model_json',side_effect=[{'bad':True},{'themes':[]}]) as model, \
             patch.object(scout,'validate_theme_analysis',side_effect=[ValueError('Unknown article ID'),{'themes':[],'company_exposures':[]}]):
            result=scout.annotate_theme_stories({},'key')
        self.assertEqual(result['themes'],[])
        self.assertIn('Unknown article ID',model.call_args_list[1].args[0])
