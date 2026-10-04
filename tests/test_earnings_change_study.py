import copy
from datetime import date
import unittest
from earnings_change_study import DIMENSIONS, validate_label, catalog
from earnings_news_study import filter_news


class ChangeStudyTests(unittest.TestCase):
    def label(self):
        return {'dimensions':{k:{'direction':'unchanged','previous_ids':['P0'],
                                 'current_ids':['C0'],'reason':'Comparable disclosures.'} for k in DIMENSIONS}}

    def test_both_periods_required_and_unknown_allowed(self):
        label=self.label();label['dimensions']['margins']['previous_ids']=[]
        with self.assertRaises(ValueError):validate_label(label,{'P0':'old'},{'C0':'new'})
        label['dimensions']['margins']['direction']='unknown'
        self.assertEqual(validate_label(label,{'P0':'old'},{'C0':'new'})['unknown_dimensions'],1)

    def test_invented_source_and_missing_dimension_rejected(self):
        label=self.label();label['dimensions']['margins']['current_ids']=['N999']
        with self.assertRaises(ValueError):validate_label(label,{'P0':'old'},{'C0':'new'})
        del label['dimensions']['margins']
        with self.assertRaises(ValueError):validate_label(label,{'P0':'old'},{'C0':'new'})

    def test_counterevidence_prevents_broad_improvement(self):
        label=self.label()
        for k in ('demand_orders','margins'):label['dimensions'][k]['direction']='improved'
        self.assertEqual(validate_label(label,{'P0':'old'},{'C0':'new'})['group'],'broad_improvement')
        label['dimensions']['cash_financing']['direction']='deteriorated'
        self.assertEqual(validate_label(label,{'P0':'old'},{'C0':'new'})['group'],'mixed')

    def test_news_future_wrong_issuer_duplicates_excluded(self):
        row={'symbol':'TEST','publishedDate':'2025-01-17 18:00:00','title':'New order',
             'url':'https://example.org/story?utm=a','text':'A signed new order.'}
        rows=[row,{**row,'url':'https://example.org/story?utm=b'},
              {**row,'symbol':'OTHER'}, {**row,'publishedDate':'2025-01-18 08:00:00'},
              {**row,'publishedDate':None}]
        accepted,rejected=filter_news(rows,'TEST',date(2025,1,15),date(2025,1,17))
        self.assertEqual(len(accepted),1)
        self.assertEqual(len(rejected),4)

    def test_catalog_retains_end_of_call(self):
        text='One sentence. '*300+'Unique final counterevidence.'
        c=catalog(text,'P')
        self.assertIn('Unique final counterevidence.',list(c.values())[-1])

    def test_annotation_request_has_no_outcomes_or_stock_prices(self):
        from unittest.mock import patch, Mock
        from earnings_change_study import annotate
        import json
        pair={'symbol':'TEST','event_date':'2025-01-17',
              'previous':{'date':'2024-10-17','content':'Old demand.'},
              'current':{'date':'2025-01-17','content':'New demand.'},
              'outcomes':{'60':{'gross_return_pct':987654321}}}
        with patch('llm_transport.complete', return_value=json.dumps(self.label())) as request:
            result=annotate(pair,'test-model','fake')
            messages=request.call_args.args[0]
            self.assertNotIn('987654321',json.dumps(messages))
            self.assertNotIn('outcomes',messages[1]['content'])
            self.assertEqual(result['group'],'limited_or_no_change')

    def test_flat_schema_normalization_preserves_strict_dimensions(self):
        payload=self.label()['dimensions']
        self.assertEqual(validate_label(payload,{'P0':'old'},{'C0':'new'})['group'],'limited_or_no_change')
        payload['unexpected']='extra'
        with self.assertRaises(ValueError):validate_label(payload,{'P0':'old'},{'C0':'new'})

    def test_unapproved_model_labels_cannot_produce_validated_summary(self):
        from earnings_change_study import summarize
        label={'symbol':'TEST','event_date':'2025-01-17','group':'broad_improvement'}
        report={'limitations':[], 'events':[{'symbol':'TEST','event_date':'2025-01-17',
                 'group':'eps_beat_only','outcomes':{'20':{'status':'measured','gross_return_pct':5}}}]}
        result=summarize([label],report)
        self.assertEqual(result['summary'],{})
        self.assertFalse(result['strategy_validated'])
        self.assertTrue(result['semantic_acceptance_required'])
        self.assertEqual(result['annotation_summary']['broad_improvement:20']['n'],1)
