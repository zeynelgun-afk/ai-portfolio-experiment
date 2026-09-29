import unittest
from earnings_pool_validation import validate


def event(symbol, sector, day, gross, excess):
    result={'gross_pct':gross,'excess_benchmark_pp':excess,'max_close_drawdown_pct':-10}
    return {'symbol':symbol,'sector':sector,'filing_date':day,'entry_date':day,
        'status':'exploratory_only','operating_change':{'operating_improvement_group':'improving',
        'operating_indicators':{'revenue_positive_yoy':True,'gross_margin_expanding':True,
                                 'operating_cash_flow_improving':None}},
        'outcomes':{'IWM':{'20':result,'60':result}}}


class EarningsPoolValidationTests(unittest.TestCase):
    def test_deduplicates_issuer_updates_and_reports_technology_subset(self):
        report=validate({'filing_events':[
            event('AAA','Technology','2025-01-02',8,4),
            event('AAA','Technology','2025-01-15',-20,-22),
            event('BBB','Industrials','2025-01-02',6,3),
        ]})
        self.assertEqual(report['qualifying_filing_events'],3)
        self.assertEqual(report['deduplicated_pool_admissions'],2)
        self.assertEqual(report['deduplicated_technology_sector_admissions'],1)
        self.assertEqual(report['technology_admission_issuers'],['AAA'])
        self.assertEqual(report['technology_only']['median_excess_60_pp'],4)

    def test_only_measured_improving_filing_events_are_admissions(self):
        a=event('AAA','Technology','2025-01-02',8,4)
        b=event('BBB','Technology','2025-01-02',5,2);b['status']='incomplete_price_window'
        c=event('CCC','Technology','2025-01-02',5,2);c['operating_change']['operating_improvement_group']='mixed_or_incomplete'
        report=validate({'filing_events':[a,b,c]})
        self.assertEqual(report['qualifying_filing_events'],1)
        self.assertEqual(report['admission_issuers'],['AAA'])


if __name__=='__main__':
    unittest.main()
