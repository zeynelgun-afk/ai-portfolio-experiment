import copy
import json
import unittest
from unittest.mock import patch
import claim_evidence as ce
import reassess
import detector
from tests.test_evidence_depth import NEWS, TEXT
from tests.test_analyst_revisions import NOW, row, sample
import analyst_revisions as ar

class CitationSelection(unittest.TestCase):
    def setUp(self):
        self.sources = ce.documents('MU', NEWS)
        self.catalog = ce.excerpt_catalog(self.sources)
        self.ident = next(iter(self.catalog))
        self.source_id = next(iter(self.sources))

    def test_code_restores_exact_source_and_quote(self):
        result = ce.resolve_citations([{'excerpt_id':self.ident}],self.sources,self.catalog)
        self.assertEqual(result[0]['quote'], TEXT)
        ce.validate_citations(result,self.sources)

    def test_unknown_id_extra_quote_and_changed_snapshot_rejected(self):
        for value in ([],[{'excerpt_id':'invented'}],[{'excerpt_id':self.ident,'quote':'invented'}],[{'excerpt_id':[]}],['bad']):
            with self.assertRaises(ValueError):ce.resolve_citations(value,self.sources,self.catalog)
        altered=copy.deepcopy(self.sources)
        for source in altered.values():source['text']='Different source content entirely.'
        with self.assertRaises(ValueError):ce.resolve_citations([{'excerpt_id':self.ident}],altered,self.catalog)

    def test_long_text_is_fully_preserved_and_ids_bind_source_content(self):
        text=('Exact values and uncertainty belong together. '*100)+'tail of the final paragraph'
        sources={'a':{'text':text},'b':{'text':text}}
        catalog=ce.excerpt_catalog(sources)
        self.assertEqual(''.join(c['quote'] for c in catalog.values() if c['source_id']=='a'),text)
        self.assertEqual(len(catalog),len(set(catalog)))
        changed=ce.excerpt_catalog({'a':{'text':text+' changed'}})
        self.assertFalse(set(changed)&set(catalog))

    def invoke(self, verdict):
        def model(*args, **kwargs):
            inputs=json.loads(args[2]);ident=next(iter(inputs['sources']))
            output={'verdict':verdict,'citations':[{'source_id':ident}],
                    'issues':[] if verdict=='supported' else ['A material assertion lacks evidence.'],
                    'counterargument':'The future remains uncertain.'}
            kwargs['response_validator'](output)
            return output,'ok'
        with patch.object(reassess,'call_llm',side_effect=model):
            return ce.semantic_review({'assessment':'A source-backed observation.'},{'MU':{'source_documents':self.sources}},{},'test','review')

    def test_supported_review_returns_auditable_quotes_and_bundle_hash(self):
        result=self.invoke('supported')
        ce.validate_citations(result['citations'],self.sources)
        self.assertEqual(len(result['source_bundle_sha256']),64)
        self.assertEqual(result['citation_selections'],[{'source_id':self.source_id}])

    def test_real_quote_selection_does_not_override_negative_verdict(self):
        for verdict in ('uncertain','unsupported'):
            with self.assertRaises(ValueError):self.invoke(verdict)

    def test_news_model_selects_stable_source_ids(self):
        def model(*args,**kwargs):
            inputs=json.loads(args[2])
            payload={'impact':'supports','claim_ids':['MU-1'],'citations':[{'source_id':next(iter(inputs['sources']))}],
                     'reasoning':'New evidence supports a review.','counterevidence':'Only one period.','uncertainty':'Future demand is unknown.',
                     'provider_metadata':'ignored safely'}
            kwargs['response_validator'](payload)
            return payload,'ok'
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test'}),patch.object(reassess,'call_llm',side_effect=model):
            supported,report=detector.check_news_shock('MU','Demand',NEWS,[{'id':'MU-1'}])
        self.assertTrue(supported)
        self.assertNotIn('provider_metadata',report)
        self.assertEqual(report['citation_selections'],[{'source_id':next(iter(report['source_documents']))}])
        ce.validate_citations(report['citations'],report['source_documents'])

    def test_unknown_short_source_alias_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown source_id'):
            ce.resolve_source_references([{'source_id':'S999'}], {'S1':{'text':TEXT}})

class ProviderIntegrity(unittest.TestCase):
    def test_business_start_is_not_coverage_initiation(self):
        rows=sample();rows[1]['newsTitle']='MU starts manufacturing new products; target raised at Alpha'
        result=ar.analyze('MU',rows,NOW,True)
        self.assertEqual(result['windows']['30']['up_firms'],2)

    def test_target_value_conflict_is_quarantined_with_original_record(self):
        rows=sample();rows[1]['newsTitle']='MU PT Raised to $999 at Alpha'
        result=ar.analyze('MU',rows,NOW,True)
        self.assertEqual(result['status'],'incomplete')
        self.assertEqual(result['quarantined_records'][0]['raw_record'],rows[1])
        self.assertIn('headline_target_differs_from_raw_provider_target',result['quarantined_records'][0]['reasons'])
        self.assertIsNone(ar.review_trigger('MU',result,{},NOW))

    def test_later_consistent_observation_recovers_without_rewriting_history(self):
        from datetime import timedelta
        from unittest.mock import Mock
        rows=sample();rows[1]['newsTitle']='MU target raised at Beta'
        state={}
        bad,_=ar.refresh('MU',NOW,state,Mock(side_effect=[rows,[]]))
        frozen=copy.deepcopy(bad)
        good,_=ar.refresh('MU',NOW+timedelta(days=1),state,Mock(side_effect=[sample(),[]]))
        self.assertEqual(bad,frozen)
        self.assertEqual(bad['status'],'incomplete')
        self.assertEqual(good['status'],'ok')
        self.assertIsNotNone(ar.review_trigger('MU',good,{},NOW+timedelta(days=1)))

if __name__=='__main__':unittest.main()
