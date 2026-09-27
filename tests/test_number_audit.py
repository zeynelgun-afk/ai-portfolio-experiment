#!/usr/bin/env python3
"""Tests for number_audit.py — the unsourced-number gate.

The most important test: round #7's actual hallucination (an "80-90% market share"
figure written into the NVDA thesis from memory) must be caught. Equally important,
legitimate derived percentages — the instructions require a percentage to carry its
base — must NOT be flagged.
"""

import os
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import number_audit as na  # noqa: E402

# The data block of a real claim prompt (reassess.claim_prompt format)
PROMPT = """Time (UTC): 2026-09-28T15:00Z
Symbol: MU
TRIGGERING DATA:
  measured: 905.4 · threshold: 941.62
CURRENT DATA:
  price: 905.4 $ (source: intraday_5m)
  previous close: 1082.28 $
  earnings date: 2026-09-30
  volume / 20d average: 3.65x
  entry price: 892.67 $
  shares: 33.6072
  stop_weekly_close: 730 $
"""


class ExtractionTest(unittest.TestCase):
    def test_decimal_point(self):
        self.assertIn(905.4, [v for _, v in na.extract_numbers("price 905.4 $")])

    def test_comma_thousands(self):
        self.assertIn(30428.36, [v for _, v in na.extract_numbers("amount 30,428.36 $")])

    def test_dot_thousands(self):
        self.assertIn(1082.28, [v for _, v in na.extract_numbers("price 1.082,28 $")])

    def test_percentages_with_signs(self):
        values = [v for _, v in na.extract_numbers("+14.9% and -16.3%")]
        self.assertIn(14.9, values)
        self.assertIn(16.3, values)

    def test_multiplier(self):
        self.assertIn(3.65, [v for _, v in na.extract_numbers("volume 3.65x")])

    def test_text_without_numbers_is_empty(self):
        self.assertEqual(na.extract_numbers("the thesis was stated without numbers"), [])


class UnsourcedNumberTest(unittest.TestCase):
    def check(self, output, prompt=PROMPT):
        return [raw for raw, _ in na.unsourced_numbers(output, prompt)]

    def test_number_present_in_prompt_is_clean(self):
        self.assertEqual(self.check(
            "The price fell below the 941.62 threshold to 905.4 $; stop 730 $."), [])

    def test_derived_percentage_is_clean(self):
        # (905.4 / 941.62 - 1) * 100 = -3.85 — absent from the prompt but derivable
        self.assertEqual(self.check(
            "The price is 3.8% below the 50d threshold (905.4 vs 941.62)."), [])

    def test_return_against_entry_is_clean(self):
        # (905.4 / 892.67 - 1) * 100 = 1.43
        self.assertEqual(self.check(
            "Up 1.4% against entry (entry 892.67 $, now 905.4 $)."), [])

    def test_stop_distance_is_clean(self):
        # (905.4 / 730 - 1) * 100 = 24.03
        self.assertEqual(self.check(
            "Stop distance +24.0%, comfortable against the 730 $ stop."), [])

    def test_rounded_threshold_is_clean(self):
        # The model may write the 941.62 threshold as "941"
        self.assertEqual(self.check("A move back above 941 would restore the claim."), [])

    def test_indicator_windows_are_clean(self):
        self.assertEqual(self.check(
            "Below the 50d average and holding above the 200d; RSI(14) is neutral."), [])

    def test_round_7_hallucination_is_caught(self):
        """The real case: a market-share figure written into the NVDA thesis."""
        unsourced = self.check(
            "NVDA leads AI accelerators with an 80-90% market share.")
        self.assertIn("80", unsourced)
        self.assertIn("90", unsourced)

    def test_invented_analyst_target_is_caught(self):
        self.assertEqual(self.check("The average analyst target sits at 1350 $."),
                         ["1350"])

    def test_invented_pe_ratio_is_caught(self):
        self.assertEqual(self.check("A P/E of 18.4 is below the sector average."),
                         ["18.4"])

    def test_counting_numbers_pass(self):
        self.assertEqual(self.check(
            "This is the 3rd round with the same label; confirmed on 2 consecutive "
            "checks."), [])

    def test_date_from_the_prompt_is_clean(self):
        self.assertEqual(self.check("Earnings land on 2026-09-30."), [])

    def test_date_absent_from_the_prompt_is_caught(self):
        unsourced = self.check("The next report is around 2027-03-15.")
        self.assertTrue(any(raw == "2027" for raw in unsourced), unsourced)

    def test_the_same_number_is_reported_once(self):
        self.assertEqual(self.check("Target 1350 $, so up to the 1350 $ level."),
                         ["1350"])

    def test_multiple_sources_are_merged(self):
        # second source: the claim's previous text — its numbers are legitimate too
        self.assertEqual(na.unsourced_numbers(
            "The +14.9% cushion above the average is gone.",
            PROMPT, "The 25 Sep close of 1082.28 $ was +14.9% above the average."), [])

    def test_tolerance_forgives_written_rounding(self):
        self.assertEqual(self.check("Price 905.40 $, volume 3.6x."), [])


class GateSelectivityTest(unittest.TestCase):
    """A gate that lets everything through is not a gate. This pins the calibration.

    An earlier version derived over every pair of numbers and let almost every
    two-digit integer pass; that is what allowed round #7's figure through.
    """

    def test_two_digit_integers_do_not_pass_wholesale(self):
        allowed = na.allowed_values(PROMPT)
        passing = sum(1 for n in range(13, 100)
                      if na._is_allowed(float(n), allowed))
        self.assertLess(passing, 30, f"gate too permissive: {passing}/87 passed")


class CorrectionPromptTest(unittest.TestCase):
    def test_prompt_names_the_offending_numbers(self):
        text = na.correction_prompt([("1350", 1350.0), ("18.4", 18.4)])
        self.assertIn("1350", text)
        self.assertIn("18.4", text)
        self.assertIn("without it", text)
        self.assertIn("JSON", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
