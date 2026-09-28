#!/usr/bin/env python3
"""Tests for reviewers.py — the two-auditor consensus rule.

The whole point of the layer is that ONE auditor's reading is not evidence. These tests
pin that: agreement records, disagreement does not, and an auditor that fails takes the
consensus down with it rather than leaving the other one to rule alone.
"""

import json
import os
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import reviewers  # noqa: E402


def finding(pattern, model, severity="medium", where="round 7", evidence="quote"):
    return {"pattern": pattern, "where": where, "evidence": evidence,
            "severity": severity, "why": "reason", "model": model}


class ConsensusTest(unittest.TestCase):
    def test_a_pattern_both_auditors_report_is_recorded(self):
        agreed, note = reviewers.find_consensus(
            [finding("wish_as_thesis", "A")], [finding("wish_as_thesis", "B")])
        self.assertEqual(len(agreed), 1)
        self.assertEqual(agreed[0]["pattern"], "wish_as_thesis")
        self.assertIn("1 agreed", note)

    def test_a_pattern_only_one_auditor_reports_is_not_recorded(self):
        agreed, note = reviewers.find_consensus(
            [finding("wish_as_thesis", "A")], [finding("phantom_rule", "B")])
        self.assertEqual(agreed, [])
        self.assertIn("0 agreed", note)
        self.assertIn("one auditor only", note)

    def test_both_auditors_evidence_is_kept(self):
        agreed, _ = reviewers.find_consensus(
            [finding("phantom_rule", "A", evidence="from A")],
            [finding("phantom_rule", "B", evidence="from B")])
        self.assertEqual(agreed[0]["auditor_a"]["evidence"], "from A")
        self.assertEqual(agreed[0]["auditor_b"]["evidence"], "from B")

    def test_consensus_severity_is_the_floor_not_the_louder_opinion(self):
        agreed, _ = reviewers.find_consensus(
            [finding("phantom_rule", "A", severity="high")],
            [finding("phantom_rule", "B", severity="low")])
        self.assertEqual(agreed[0]["severity"], "low")

    def test_a_pattern_is_recorded_once_even_if_reported_twice(self):
        agreed, _ = reviewers.find_consensus(
            [finding("phantom_rule", "A", where="r1"),
             finding("phantom_rule", "A", where="r2")],
            [finding("phantom_rule", "B")])
        self.assertEqual(len(agreed), 1)

    def test_a_failed_auditor_takes_the_consensus_down(self):
        """If one auditor's output is unusable the other must not rule alone."""
        agreed, note = reviewers.find_consensus(None, [finding("phantom_rule", "B")])
        self.assertEqual(agreed, [])
        self.assertIn("no consensus possible", note)
        agreed, note = reviewers.find_consensus([finding("phantom_rule", "A")], None)
        self.assertEqual(agreed, [])

    def test_two_empty_reports_agree_on_nothing(self):
        agreed, note = reviewers.find_consensus([], [])
        self.assertEqual(agreed, [])
        self.assertIn("0 agreed", note)


class TaxonomyTest(unittest.TestCase):
    def setUp(self):
        self._call = reviewers.reassess.call_llm

    def tearDown(self):
        reviewers.reassess.call_llm = self._call

    def stub(self, payload, status="ok"):
        reviewers.reassess.call_llm = lambda *a, **k: (payload, status)

    def test_an_invented_pattern_is_discarded(self):
        """The taxonomy is closed so consensus stays computable across two models."""
        self.stub({"findings": [
            {"pattern": "vibes_off", "where": "x", "evidence": "e", "severity": "high",
             "why": "w"},
            {"pattern": "phantom_rule", "where": "y", "evidence": "f",
             "severity": "low", "why": "v"}]})
        result = reviewers.run_auditor("m", "prompt", "key")
        self.assertEqual([f["pattern"] for f in result], ["phantom_rule"])

    def test_a_missing_severity_does_not_lose_the_finding(self):
        self.stub({"findings": [
            {"pattern": "phantom_rule", "where": "y", "evidence": "f", "why": "v"}]})
        result = reviewers.run_auditor("m", "prompt", "key")
        self.assertEqual(result[0]["severity"], reviewers.DEFAULT_SEVERITY)

    def test_an_unrecognised_severity_is_normalised(self):
        self.stub({"findings": [
            {"pattern": "phantom_rule", "where": "y", "evidence": "f",
             "severity": "CATASTROPHIC", "why": "v"}]})
        self.assertEqual(reviewers.run_auditor("m", "p", "k")[0]["severity"],
                         reviewers.DEFAULT_SEVERITY)

    def test_unusable_output_returns_none_not_an_empty_list(self):
        """None and [] mean different things: 'the auditor failed' vs 'it found nothing'."""
        self.stub(None, "unparseable")
        self.assertIsNone(reviewers.run_auditor("m", "prompt", "key"))
        self.stub({"clean": True})  # no findings key at all
        self.assertIsNone(reviewers.run_auditor("m", "prompt", "key"))

    def test_a_clean_report_is_an_empty_list(self):
        self.stub({"findings": [], "clean": True})
        self.assertEqual(reviewers.run_auditor("m", "prompt", "key"), [])


class AmendmentThresholdTest(unittest.TestCase):
    def test_a_pattern_becomes_an_amendment_only_after_repetition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "audit_patterns.json")
            agreed = [{"pattern": "phantom_rule"}]
            for round_number in range(1, reviewers.AMENDMENT_THRESHOLD):
                self.assertEqual(reviewers.update_pattern_counts(path, agreed), [],
                                 f"flagged too early at {round_number}")
            recurring = reviewers.update_pattern_counts(path, agreed)
            self.assertEqual(len(recurring), 1)
            self.assertEqual(recurring[0]["count"], reviewers.AMENDMENT_THRESHOLD)

    def test_counts_survive_a_corrupt_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "audit_patterns.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{broken")
            reviewers.update_pattern_counts(path, [{"pattern": "phantom_rule"}])
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["phantom_rule"]["count"], 1)


class PromptTest(unittest.TestCase):
    def test_the_system_prompt_forbids_proposing_trades(self):
        system = reviewers.SYSTEM.format(patterns="x")
        self.assertIn("Do not propose a trade", system)
        self.assertIn("stopped auditing", system)

    def test_the_system_prompt_separates_reasoning_from_outcome(self):
        system = reviewers.SYSTEM.format(patterns="x")
        self.assertIn("never as the verdict", system)

    def test_the_prompt_leads_with_the_deterministic_scorecard(self):
        prompt = reviewers.build_prompt({"weekly_rounds": 3}, "## #1 — round", {})
        self.assertTrue(prompt.startswith("=== DETERMINISTIC SCORECARD"))
        self.assertIn("no model wrote these", prompt)


class AuditLogTest(unittest.TestCase):
    def test_no_consensus_is_written_down_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "AUDIT_LOG.md")
            reviewers.append_audit_log(path, "2026-09-28T10:00Z", [], "0 agreed", [],
                                       ("A", "B"))
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        self.assertIn("No finding was reported by both auditors", text)
        self.assertIn("only when both auditors report the same pattern", text)

    def test_a_recurring_pattern_proposes_and_never_applies(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "AUDIT_LOG.md")
            reviewers.append_audit_log(
                path, "2026-09-28T10:00Z", [], "0 agreed",
                [{"pattern": "phantom_rule", "count": 3, "since": "2026-09-01T10:00Z"}],
                ("A", "B"))
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        self.assertIn("Instruction amendment warranted", text)
        self.assertIn("The owner decides", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
