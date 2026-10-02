import copy
import json
import unittest
from unittest.mock import patch
import evidence
import detector
import reassess
from tests.test_citation_selection import NEWS

class AssessmentRetries(unittest.TestCase):
    def test_retry_receives_rejected_response_and_exact_error(self):
        bad = json.dumps({'answer': 'wrong shape'})
        good = json.dumps({'text': 'Demand remains uncertain.', 'status': 'valid'})
        seen = []
        def call(model, messages, key, **kwargs):
            seen.append(copy.deepcopy(messages))
            return (bad if len(seen) == 1 else good), False
        with patch.object(reassess, '_single_call', side_effect=call):
            result, status = reassess.call_llm('model', 'system', 'input', 'key',
                source_ledger={}, audit_scope=reassess.claim_audit_scope)
        self.assertEqual(status, 'ok')
        self.assertEqual(seen[1][-2], {'role': 'assistant', 'content': bad})
        self.assertIn('Claim output', seen[1][-1]['content'])

    def test_evidence_rejection_is_explained_and_corrected(self):
        bad=json.dumps({'text':'Demand grew 99 percent.', 'status':'valid'})
        good=json.dumps({'text':'Demand remains uncertain.', 'status':'valid'})
        seen=[]
        def call(model,messages,key,**kwargs):
            seen.append(copy.deepcopy(messages))
            return (bad if len(seen)==1 else good),False
        with patch.object(reassess,'_single_call',side_effect=call):
            _,status=reassess.call_llm('model','system','input','key',
                source_ledger={},audit_scope=reassess.claim_audit_scope)
        self.assertEqual(status,'ok')
        self.assertEqual(seen[1][-2]['content'],bad)
        self.assertIn('Raw numeric',seen[1][-1]['content'])
        self.assertIn('invalid_evidence',reassess.REJECTION_REASON)

    def test_duplicate_valid_news_does_not_look_like_missing_source(self):
        def call(*args,**kwargs):
            inputs=json.loads(args[2]); ident=next(iter(inputs['sources']))
            output={'impact':'neutral','claim_ids':[], 'citations':[{'source_id':ident}],
                'reasoning':'No material thesis change.', 'counterevidence':'Demand remains uncertain.',
                'uncertainty':'Future outcomes are unknown.'}
            kwargs['response_validator'](output)
            return output,'ok'
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test'}),patch.object(reassess,'call_llm',side_effect=call) as model:
            shock,report=detector.check_news_shock('MU','Demand',NEWS+NEWS,[{'id':'MU-1'}])
        model.assert_called_once()
        self.assertFalse(shock)
        self.assertEqual(len(report['source_documents']),1)

    def test_publisher_name_is_not_an_unsourced_market_number(self):
        for publisher in ('24/7 Wall St.', '24/7 Wall Street'):
            text=publisher + ' describes a valuation scenario.'
            self.assertEqual(evidence.render(text, {}), text)
        for text in ('Revenue grew 24 percent.', 'Demand grew 24/7.', '24/7 Wall St. forecasts 99 percent growth.'):
            with self.assertRaises(ValueError):
                evidence.render(text, {})

    def test_evidence_error_identifies_rejected_field(self):
        with self.assertRaisesRegex(ValueError, 'reasoning: Raw numeric.*99'):
            evidence.render_payload({'decision': {'reasoning': 'Revenue rose 99 percent.'}}, {})

    def test_invalid_news_still_blocks_assessment(self):
        invalid=dict(NEWS[0],text='Headline only')
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test'}),patch.object(reassess,'call_llm') as model:
            shock,_=detector.check_news_shock('MU','Demand',NEWS+[invalid])
        self.assertIsNone(shock)
        model.assert_not_called()
