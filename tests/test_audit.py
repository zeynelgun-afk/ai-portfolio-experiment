#!/usr/bin/env python3
"""Tests for audit.py — the deterministic scorecard.

Every number the scorecard prints comes from the repository's own record, so the tests
feed it small, hand-written records and check what it concludes. No network: price
lookups are injected.
"""

import json
import os
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import audit  # noqa: E402


LOG = """# Decision Log

## #1 — 2026-08-05 · WEEKLY ROUND

**MU (892.67 $, Wednesday 5 August) — memory super-cycle → VALID**
**AVGO (418.16 $) — custom AI chips → VALID**

#### DECISION 1: BUY — MU, AVGO

## #2 — 2026-08-12 · WEEKLY ROUND

**MU (900.00 $) — memory super-cycle → VALID**
**AVGO (400.00 $) — custom AI chips → WEAKENING**

#### DECISION 1: HOLD — MU, AVGO

## #3 — 2026-08-19 · WEEKLY ROUND

**MU (910.00 $) — memory super-cycle → VALID**
**AVGO (380.00 $) — custom AI chips → WEAKENING**

#### DECISION 1: HOLD — MU, AVGO

## #4 — 2026-08-26 · WEEKLY ROUND

**MU (920.00 $) — memory super-cycle → VALID**
**AVGO (370.00 $) — custom AI chips → WEAKENING**

#### DECISION 1: HOLD — MU, AVGO

## #5 — 2026-09-02 · WEEKLY ROUND

**MU (930.00 $) — memory super-cycle → VALID**
**AVGO (360.00 $) — custom AI chips → BROKEN**

#### DECISION 1: HOLD — MU, AVGO

## S#1 — 2026-09-03 10:00 UTC · INTRADAY DECISION

## #6 — 2026-09-09 · WEEKLY ROUND

**MU (940.00 $) — memory super-cycle → VALID**
**AVGO (350.00 $) — custom AI chips → BROKEN**

#### DECISION 1: SELL — AVGO (thesis broken)
"""

PORTFOLIO = {
    "trade_history": [
        {"date": "2026-08-05", "action": "BUY", "symbol": "MU", "shares": 33.6,
         "price": 892.67, "amount_usd": 30000.0},
        {"date": "2026-08-05", "action": "BUY", "symbol": "AVGO", "shares": 23.9,
         "price": 418.16, "amount_usd": 10000.0},
        {"date": "2026-09-09", "action": "SELL", "symbol": "AVGO", "shares": 23.9,
         "price": 350.00, "amount_usd": 8365.0},
        {"date": "2026-09-10", "action": "TRIM", "symbol": "MU", "shares": 5.0,
         "price": 950.00, "amount_usd": 4750.0, "source": "intraday_autonomous",
         "time_utc": "15:30"},
    ]
}

THESES = {
    "_meta": {"version": 1},
    "MU": {"thesis_summary": "memory", "claims": [
        {"id": "MU-1", "text": "a", "status": "valid", "last_updated": None,
         "conditions": [{"type": "price_below", "value": 900, "severity": "claim"},
                        {"type": "daily_change_pct", "value": -7, "severity": "thesis"}]},
        {"id": "MU-2", "text": "b", "status": "unassessed",
         "last_updated": "2026-09-20T10:00Z",
         "conditions": [{"type": "volume_ratio_20d", "value": 3.0,
                         "severity": "claim"}]},
    ]},
}


class RoundParsingTest(unittest.TestCase):
    def test_weekly_rounds_are_split(self):
        rounds = audit.read_rounds(LOG)
        self.assertEqual([number for number, _, _ in rounds], [1, 2, 3, 4, 5, 6])

    def test_intraday_headings_are_counted_separately(self):
        self.assertEqual(len(audit.INTRADAY_HEADING.findall(LOG)), 1)
        self.assertEqual([n for n, _, _ in audit.read_rounds(LOG)], [1, 2, 3, 4, 5, 6])


class LabelAuditTest(unittest.TestCase):
    def setUp(self):
        self.result = audit.label_audit(audit.read_rounds(LOG))

    def test_broken_and_held_is_caught(self):
        """The instructions forbid marking a thesis BROKEN and quietly holding it."""
        flagged = [(item["round"], item["symbol"])
                   for item in self.result["broken_but_held"]]
        self.assertIn((5, "AVGO"), flagged)

    def test_broken_with_an_action_is_not_flagged(self):
        """Round 6 marked AVGO BROKEN and sold it — that is the rule being followed."""
        flagged = [(item["round"], item["symbol"])
                   for item in self.result["broken_but_held"]]
        self.assertNotIn((6, "AVGO"), flagged)

    def test_an_unsettled_label_streak_is_caught(self):
        streaks = {(item["symbol"], item["label"]): item["rounds"]
                   for item in self.result["label_streaks"]}
        self.assertGreaterEqual(streaks.get(("AVGO", "WEAKENING"), 0), 3)

    def test_a_settled_label_streak_is_not_flagged(self):
        """MU is VALID for six rounds and held — a settled state, not a deferral.

        Flagging it would make the scorecard cry wolf, and a scorecard nobody reads is
        worth nothing.
        """
        symbols = {item["symbol"] for item in self.result["label_streaks"]}
        self.assertNotIn("MU", symbols)

    def test_every_health_line_is_read(self):
        self.assertEqual(self.result["labels_seen"], {"MU": 6, "AVGO": 6})


class ExitAuditTest(unittest.TestCase):
    def test_an_exit_before_a_rise_is_costly(self):
        result = audit.exit_audit(PORTFOLIO, {"AVGO": 500.0, "MU": 1000.0})
        avgo = next(r for r in result if r["symbol"] == "AVGO")
        self.assertEqual(avgo["verdict"], "costly")
        self.assertAlmostEqual(avgo["move_pct"], 42.9, places=1)

    def test_an_exit_before_a_fall_is_vindicated(self):
        result = audit.exit_audit(PORTFOLIO, {"AVGO": 250.0, "MU": 1000.0})
        avgo = next(r for r in result if r["symbol"] == "AVGO")
        self.assertEqual(avgo["verdict"], "vindicated")

    def test_a_small_move_is_neutral(self):
        result = audit.exit_audit(PORTFOLIO, {"AVGO": 355.0, "MU": 960.0})
        self.assertTrue(all(r["verdict"] == "neutral" for r in result))

    def test_a_missing_price_is_unmeasured_not_guessed(self):
        result = audit.exit_audit(PORTFOLIO, {})
        self.assertTrue(all(r["verdict"] == "unmeasured" for r in result))
        self.assertTrue(all(r["move_pct"] is None for r in result))

    def test_buys_are_not_scored(self):
        result = audit.exit_audit(PORTFOLIO, {"AVGO": 500.0, "MU": 1000.0})
        self.assertEqual({r["action"] for r in result}, {"SELL", "TRIM"})


class ThresholdAuditTest(unittest.TestCase):
    def write_log(self, directory, entries):
        path = os.path.join(directory, "triggers.jsonl")
        with open(path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry) + "\n")
        return path

    def test_a_condition_that_never_fired_is_named(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_log(directory, [])
            result = audit.threshold_audit(path, THESES)
        qualities = {(r["claim_id"], r["type"]): r["quality"]
                     for r in result["conditions"]}
        self.assertEqual(qualities[("MU-1", "price_below")], "never fired")

    def test_a_condition_firing_on_most_checks_is_noisy(self):
        entries = [{"checked_at": f"2026-09-2{i}T15:00:00Z", "claim_id": "MU-1",
                    "type": "price_below", "severity": "claim", "measured": 1,
                    "threshold": 2, "acted_on": False} for i in range(4)]
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_log(directory, entries)
            result = audit.threshold_audit(path, THESES)
        row = next(r for r in result["conditions"]
                   if (r["claim_id"], r["type"]) == ("MU-1", "price_below"))
        self.assertEqual(result["checks_recorded"], 4)
        self.assertEqual(row["fired"], 4)
        self.assertEqual(row["quality"], "noisy")

    def test_an_occasional_condition_is_informative(self):
        entries = [{"checked_at": f"2026-09-2{i}T15:00:00Z", "claim_id": "MU-1",
                    "type": "price_below", "severity": "claim", "measured": 1,
                    "threshold": 2, "acted_on": True} for i in range(1)]
        entries += [{"checked_at": f"2026-09-1{i}T15:00:00Z", "claim_id": "MU-2",
                     "type": "volume_ratio_20d", "severity": "claim", "measured": 1,
                     "threshold": 2, "acted_on": False} for i in range(5)]
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_log(directory, entries)
            result = audit.threshold_audit(path, THESES)
        row = next(r for r in result["conditions"]
                   if (r["claim_id"], r["type"]) == ("MU-1", "price_below"))
        self.assertEqual(row["quality"], "informative")
        self.assertEqual(row["acted_on"], 1)

    def test_a_corrupt_line_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "triggers.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write('{"broken\n')
                handle.write(json.dumps({
                    "checked_at": "2026-09-28T15:00:00Z", "claim_id": "MU-1",
                    "type": "price_below", "severity": "claim", "measured": 1,
                    "threshold": 2, "acted_on": True}) + "\n")
            result = audit.threshold_audit(path, THESES)
        self.assertEqual(result["checks_recorded"], 1)


class AttributionAndChurnTest(unittest.TestCase):
    def test_the_two_cadences_are_separated(self):
        result = audit.attribution_audit(PORTFOLIO)
        self.assertEqual(result["weekly"]["count"], 3)
        self.assertEqual(result["intraday"]["count"], 1)
        self.assertEqual(result["intraday"]["exits"], 1)
        self.assertEqual(result["weekly"]["buys"], 2)

    def test_stuck_claims_are_surfaced(self):
        result = audit.churn_audit(THESES)
        self.assertEqual(result["claims"], 2)
        self.assertEqual([c["claim_id"] for c in result["unassessed"]], ["MU-2"])

    def test_meta_is_not_counted_as_a_position(self):
        self.assertEqual(audit.churn_audit(THESES)["claims"], 2)


class RenderTest(unittest.TestCase):
    def scorecard(self):
        return {
            "generated_at": "2026-09-28T10:00Z", "weekly_rounds": 6,
            "intraday_rounds": 1,
            "labels": audit.label_audit(audit.read_rounds(LOG)),
            "exits": audit.exit_audit(PORTFOLIO, {"AVGO": 500.0, "MU": 1000.0}),
            "thresholds": {"checks_recorded": 0, "conditions": []},
            "attribution": audit.attribution_audit(PORTFOLIO),
            "churn": audit.churn_audit(THESES),
        }

    def test_the_report_states_no_model_produced_it(self):
        text = audit.render(self.scorecard())
        self.assertIn("No model produced any number", text)

    def test_findings_reach_the_report(self):
        text = audit.render(self.scorecard())
        self.assertIn("AVGO", text)
        self.assertIn("costly", text)
        self.assertIn("unassessed", text)

    def test_an_empty_trigger_log_says_so_rather_than_implying_clean(self):
        text = audit.render(self.scorecard())
        self.assertIn("trigger log starts empty", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
