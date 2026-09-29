import unittest
from unittest.mock import patch

import theme_macro_context


class _Response:
    def __init__(self, payload):
        self.payload = payload
    def raise_for_status(self):
        return None
    def json(self):
        return self.payload


class ThemeMacroContextTests(unittest.TestCase):
    def test_fred_observation_change_is_dated_and_non_predictive(self):
        payload={'observations':[{'date':f'2026-09-{28-i:02}','value':str(4+i/10)}
                                 for i in range(8)]}
        with patch.object(theme_macro_context.requests,'get',return_value=_Response(payload)):
            result=theme_macro_context._fred_series('DGS10','secret')
        self.assertEqual(result['as_of'],'2026-09-28')
        self.assertAlmostEqual(result['change_over_observations'],-0.5)

    def test_eia_sums_state_and_sector_sales_without_national_double_count(self):
        rows=[{'period':'2026-07','stateid':'CA','sectorid':'ALL','sales':'10'},
              {'period':'2026-07','stateid':'CA','sectorid':'COM','sales':'7'},
              {'period':'2026-07','stateid':'NY','sectorid':'ALL','sales':'20'},
              {'period':'2026-07','stateid':'US','sectorid':'ALL','sales':'999'},
              {'period':'2025-07','stateid':'CA','sectorid':'ALL','sales':'8'},
              {'period':'2025-07','stateid':'NY','sectorid':'ALL','sales':'22'}]
        with patch.object(theme_macro_context.requests,'get',return_value=_Response({'response':{'data':rows}})):
            result=theme_macro_context._electricity_sales('secret')
        self.assertEqual(result['value'],30)
        self.assertAlmostEqual(result['year_over_year_pct'],0)

    def test_missing_keys_are_reported_without_network_calls(self):
        with patch.dict('os.environ',{},clear=True), patch.object(theme_macro_context.requests,'get') as get:
            result=theme_macro_context.collect()
        get.assert_not_called()
        self.assertEqual(result['status'],'unavailable')
        self.assertFalse(result['scoring_use'])


if __name__ == '__main__':
    unittest.main()
