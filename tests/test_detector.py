#!/usr/bin/env python3
"""Tests for detector.py — thresholds, hysteresis, cooldown and the recovery band.

No network: `run()` is a pure function that takes its data as a dict. The CLI modes
(`--dry-run`, `--fixed-data`) are exercised separately through a subprocess.

Run with:  python -m unittest discover -s tests -t .
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import detector  # noqa: E402

MOMENT = datetime(2026, 9, 28, 15, 0, tzinfo=timezone.utc)  # Monday, mid-session


def thesis(conditions, symbol="MU", claim_id="MU-1"):
    return {symbol: {"thesis_summary": "test", "claims": [
        {"id": claim_id, "text": "test claim", "conditions": conditions,
         "status": "valid", "last_updated": None, "trigger": None}]}}


def data(price=900.0, previous=1000.0, volume=None, average=None, earnings=None, **extra):
    row = {"price": price, "previous_close": previous, "volume": volume,
           "volume_avg_20d": average, "earnings_date": earnings}
    row.update(extra)
    return {"MU": row}


def run(theses, rows, previous=None, cooldown=None, moment=MOMENT, stops=None,
        full=False):
    return detector.run(theses, rows, stops or {"MU": 730},
                        previous or {}, cooldown or {}, moment, full)


class ThresholdTest(unittest.TestCase):
    def test_benchmark_etfs_do_not_request_an_earnings_calendar(self):
        dates = pd.date_range(end=datetime.now(), periods=205, freq='D')
        symbols = ['MU', 'SPY']
        closes = pd.DataFrame({symbol: [100.0 + i for i in range(205)] for symbol in symbols}, index=dates)
        volumes = pd.DataFrame({symbol: [1_000_000.0] * 205 for symbol in symbols}, index=dates)
        daily = pd.concat({'Close': closes, 'Volume': volumes}, axis=1)
        intraday = pd.concat({'Close': pd.DataFrame({'MU':[305.0], 'SPY':[305.0]},
                                                     index=[datetime.now()]),
                              'Volume': pd.DataFrame({'MU':[1000.0], 'SPY':[1000.0]},
                                                     index=[datetime.now()])}, axis=1)
        with patch('market_data.download', side_effect=[daily, intraday]), \
                patch('market_data.news', return_value=([], 'FMP')), \
                patch.object(detector, '_earnings_date', return_value=None) as earnings:
            result = detector.collect_live_data(symbols, {'MU':'2026-10-01'}, {'MU'})
        self.assertEqual(set(result), set(symbols))
        self.assertEqual(earnings.call_count, 1)
        self.assertEqual(earnings.call_args.args[1], 'MU')

    def test_price_below_threshold_is_a_breach(self):
        report = run(thesis([{"type": "price_below", "value": 941.62,
                              "severity": "claim"}]),
                     data(price=905.40, previous=1082.28))
        self.assertTrue(report["conditions"]["MU-1#0"]["breach"])

    def test_above_the_threshold_is_no_breach(self):
        report = run(thesis([{"type": "price_below", "value": 941.62,
                              "severity": "claim"}]),
                     data(price=1000.0, previous=1082.28))
        self.assertFalse(report["conditions"]["MU-1#0"]["breach"])
        self.assertEqual(report["code"], 0)

    def test_severity_maps_to_exit_code(self):
        for severity, expected in (("warning", 0), ("claim", 10), ("thesis", 20)):
            conditions = [{"type": "price_below", "value": 941.62,
                           "severity": severity}]
            state = {}
            for _ in range(2):  # clear hysteresis
                report = run(thesis(conditions), data(price=905.40, previous=1082.28),
                             previous=state)
                state = report["conditions"]
            self.assertEqual(report["code"], expected, f"severity {severity}")

    def test_stop_proximity_is_measured_as_a_percentage(self):
        conditions = [{"type": "stop_proximity_pct", "value": 5, "severity": "claim"}]
        near = run(thesis(conditions), data(price=750.0, previous=800.0))   # +2.7%
        far = run(thesis(conditions), data(price=1000.0, previous=1000.0))  # +37.0%
        self.assertTrue(near["conditions"]["MU-1#0"]["breach"])
        self.assertFalse(far["conditions"]["MU-1#0"]["breach"])

    def test_volume_ratio_breaches_upward(self):
        conditions = [{"type": "volume_ratio_20d", "value": 3.0, "severity": "claim"}]
        spike = run(thesis(conditions), data(volume=62_000_000, average=17_000_000))
        normal = run(thesis(conditions), data(volume=20_000_000, average=17_000_000))
        self.assertTrue(spike["conditions"]["MU-1#0"]["breach"])
        self.assertFalse(normal["conditions"]["MU-1#0"]["breach"])

    def test_missing_volume_skips_the_condition(self):
        conditions = [{"type": "volume_ratio_20d", "value": 3.0, "severity": "claim"}]
        report = run(thesis(conditions), data(volume=None, average=None))
        self.assertNotIn("MU-1#0", report["conditions"])
        self.assertEqual(report["code"], 0)

    def test_daily_change_against_a_negative_threshold(self):
        conditions = [{"type": "daily_change_pct", "value": -7, "severity": "thesis"}]
        crash = run(thesis(conditions), data(price=905.40, previous=1000.0))  # -9.5%
        mild = run(thesis(conditions), data(price=970.0, previous=1000.0))    # -3.0%
        self.assertTrue(crash["conditions"]["MU-1#0"]["breach"])
        self.assertFalse(mild["conditions"]["MU-1#0"]["breach"])

    def test_sector_etf_is_measured_from_its_own_series(self):
        conditions = [{"type": "sector_etf_change_pct", "symbol": "SMH", "value": -4,
                       "severity": "claim"}]
        rows = data(price=1000.0, previous=1000.0)  # the symbol itself is quiet
        rows["SMH"] = {"price": 596.20, "previous_close": 627.10}  # -4.9%
        report = run(thesis(conditions), rows)
        self.assertTrue(report["conditions"]["MU-1#0"]["breach"])
        self.assertIn("SMH", report["conditions"]["MU-1#0"]["detail"])

    def test_earnings_proximity_and_past_earnings(self):
        conditions = [{"type": "earnings_approaching", "days": 3,
                       "severity": "warning"}]
        near = run(thesis(conditions), data(earnings="2026-09-30"))  # 2 days
        far = run(thesis(conditions), data(earnings="2026-11-03"))
        past = run(thesis(conditions), data(earnings="2026-09-01"))
        self.assertTrue(near["conditions"]["MU-1#0"]["breach"])
        self.assertFalse(far["conditions"]["MU-1#0"]["breach"])
        self.assertNotIn("MU-1#0", past["conditions"])

    def test_a_missing_earnings_date_does_not_raise(self):
        conditions = [{"type": "earnings_approaching", "days": 3,
                       "severity": "warning"}]
        for broken in (None, "", "unknown"):
            report = run(thesis(conditions), data(earnings=broken))
            self.assertEqual(report["code"], 0)

    def test_an_unknown_condition_type_is_skipped_silently(self):
        report = run(thesis([{"type": "not_yet", "value": 1, "severity": "thesis"}]),
                     data())
        self.assertEqual(report["code"], 0)


class HysteresisTest(unittest.TestCase):
    CONDITION = [{"type": "price_below", "value": 941.62, "severity": "claim"}]

    def test_the_first_check_does_not_confirm(self):
        report = run(thesis(self.CONDITION), data(price=905.40, previous=1082.28))
        record = report["conditions"]["MU-1#0"]
        self.assertEqual((record["streak"], record["confirmed"], report["code"]),
                         (1, False, 0))
        self.assertEqual(report["triggered"], [])

    def test_the_second_consecutive_check_confirms(self):
        rows = data(price=905.40, previous=1082.28)
        first = run(thesis(self.CONDITION), rows)
        second = run(thesis(self.CONDITION), rows, previous=first["conditions"])
        record = second["conditions"]["MU-1#0"]
        self.assertEqual((record["streak"], record["confirmed"], second["code"]),
                         (2, True, 10))
        self.assertEqual(len(second["triggered"]), 1)

    def test_clearing_in_between_resets_the_streak(self):
        theses = thesis(self.CONDITION)
        first = run(theses, data(price=905.40, previous=1082.28))
        # Back above the band: 941.62 * 1.01 = 951.04
        cleared = run(theses, data(price=960.0, previous=1082.28),
                      previous=first["conditions"])
        again = run(theses, data(price=905.40, previous=1082.28),
                    previous=cleared["conditions"])
        self.assertEqual(cleared["conditions"]["MU-1#0"]["streak"], 0)
        self.assertEqual(again["conditions"]["MU-1#0"]["streak"], 1)
        self.assertFalse(again["conditions"]["MU-1#0"]["confirmed"])

    def test_suspect_data_requires_three_consecutive_checks(self):
        # A -30% deviation may be a corrupt bar. It must not trigger before three checks.
        rows = data(price=700.0, previous=1000.0)
        theses = thesis(self.CONDITION)
        state, codes = {}, []
        for _ in range(3):
            report = run(theses, rows, previous=state)
            state = report["conditions"]
            codes.append(report["code"])
        self.assertEqual(codes, [0, 0, 10])
        self.assertTrue(state["MU-1#0"]["data_suspect"])
        self.assertEqual(state["MU-1#0"]["required_streak"], 3)


class RecoveryBandTest(unittest.TestCase):
    """Below 850 triggers, above 858.5 clears — oscillation in between is no signal."""

    CONDITION = [{"type": "price_below", "value": 850, "severity": "claim"}]

    def breached(self, price, previous_state):
        report = run(thesis(self.CONDITION), data(price=price, previous=860.0),
                     previous=previous_state)
        return report["conditions"]["MU-1#0"]["breach"], report["conditions"]

    def test_the_breach_persists_inside_the_band(self):
        breach, state = self.breached(845.0, {})
        self.assertTrue(breach)
        for price in (851.0, 855.0, 858.0):  # above the threshold, inside the band
            breach, state = self.breached(price, state)
            self.assertTrue(breach, f"{price} is inside the band; breach should persist")

    def test_above_the_band_it_clears(self):
        _, state = self.breached(845.0, {})
        breach, _ = self.breached(859.0, state)  # above 850 * 1.01 = 858.5
        self.assertFalse(breach)

    def test_a_condition_not_in_breach_does_not_trigger_inside_the_band(self):
        breach, _ = self.breached(852.0, {})  # above the threshold, never was in breach
        self.assertFalse(breach)


class CooldownTest(unittest.TestCase):
    CONDITION = [{"type": "price_below", "value": 941.62, "severity": "claim"}]

    def confirmed_state(self):
        rows = data(price=905.40, previous=1082.28)
        first = run(thesis(self.CONDITION), rows)
        return rows, first["conditions"]

    def test_a_fresh_cooldown_blocks_the_trigger(self):
        rows, state = self.confirmed_state()
        cooldown = {"MU-1": detector.iso(MOMENT - timedelta(hours=1))}
        report = run(thesis(self.CONDITION), rows, previous=state, cooldown=cooldown)
        self.assertTrue(report["conditions"]["MU-1#0"]["confirmed"])
        self.assertEqual(report["triggered"], [])
        self.assertEqual(report["code"], 0)
        self.assertTrue(report["conditions"]["MU-1#0"]["cooldown"])

    def test_after_four_hours_it_triggers_again(self):
        rows, state = self.confirmed_state()
        cooldown = {"MU-1": detector.iso(MOMENT - timedelta(hours=4, minutes=1))}
        report = run(thesis(self.CONDITION), rows, previous=state, cooldown=cooldown)
        self.assertEqual(report["code"], 10)

    def test_thesis_level_cooldown_is_keyed_by_position(self):
        conditions = [{"type": "price_below", "value": 941.62, "severity": "thesis"}]
        rows = data(price=905.40, previous=1082.28)
        state = run(thesis(conditions), rows)["conditions"]
        # A claim key does not block the thesis level; the key that does is "thesis:MU"
        open_ = run(thesis(conditions), rows, previous=state,
                    cooldown={"MU-1": detector.iso(MOMENT)})
        blocked = run(thesis(conditions), rows, previous=state,
                      cooldown={"thesis:MU": detector.iso(MOMENT)})
        self.assertEqual(open_["code"], 20)
        self.assertEqual(blocked["code"], 0)

    def test_a_corrupt_cooldown_stamp_does_not_block(self):
        rows, state = self.confirmed_state()
        report = run(thesis(self.CONDITION), rows, previous=state,
                     cooldown={"MU-1": "corrupt"})
        self.assertEqual(report["code"], 10)


class SessionAndFullReviewTest(unittest.TestCase):
    def test_full_review_returns_code_10_without_a_breach(self):
        report = run(thesis([{"type": "price_below", "value": 500,
                              "severity": "claim"}]),
                     data(price=1000.0, previous=1000.0), full=True)
        self.assertEqual(report["code"], 10)
        self.assertEqual(report["triggered"], [])

    def test_full_review_does_not_override_the_thesis_level(self):
        conditions = [{"type": "price_below", "value": 941.62, "severity": "thesis"}]
        rows = data(price=905.40, previous=1082.28)
        state = run(thesis(conditions), rows)["conditions"]
        report = run(thesis(conditions), rows, previous=state, full=True)
        self.assertEqual(report["code"], 20)

    def test_the_session_window(self):
        self.assertTrue(detector.market_open(
            datetime(2026, 9, 28, 14, 0, tzinfo=timezone.utc)))
        self.assertFalse(detector.market_open(
            datetime(2026, 9, 28, 21, 15, tzinfo=timezone.utc)))
        self.assertFalse(detector.market_open(
            datetime(2026, 9, 26, 15, 0, tzinfo=timezone.utc)))

    def test_warning_severity_produces_a_flag_but_no_code(self):
        conditions = [{"type": "price_below", "value": 941.62, "severity": "warning"}]
        rows = data(price=905.40, previous=1082.28)
        state = run(thesis(conditions), rows)["conditions"]
        report = run(thesis(conditions), rows, previous=state)
        self.assertEqual(report["code"], 0)
        self.assertEqual(len(report["flags"]), 1)


class BackoffTest(unittest.TestCase):
    """A flaky data source should not read as "the thesis could not be measured"."""

    def setUp(self):
        self._sleep = detector.SLEEP
        self.waits = []
        detector.SLEEP = self.waits.append

    def tearDown(self):
        detector.SLEEP = self._sleep

    def test_a_transient_failure_is_retried_and_succeeds(self):
        attempts = []

        def flaky():
            attempts.append(1)
            if len(attempts) < 2:
                raise RuntimeError("rate limited")
            return "data"

        self.assertEqual(detector._retry("test", flaky), "data")
        self.assertEqual(len(attempts), 2)
        self.assertEqual(len(self.waits), 1)

    def test_it_gives_up_after_the_attempt_limit(self):
        def always_fails():
            raise RuntimeError("down")

        self.assertIsNone(detector._retry("test", always_fails))
        self.assertEqual(len(self.waits), detector.FETCH_ATTEMPTS - 1)

    def test_each_delay_sits_in_its_jittered_band(self):
        """The delay doubles per attempt, spread over a 0.5x-1.5x jitter band.

        Asserting waits[1] > waits[0] would be flaky: the bands overlap by design
        (attempt 1 reaches 4.5s, attempt 2 starts at 3.0s). The contract is the band,
        so that is what is checked.
        """
        detector._retry("test", lambda: None)
        for attempt, delay in enumerate(self.waits):
            expected = detector.BACKOFF_BASE * (2 ** attempt)
            self.assertGreaterEqual(delay, expected * 0.5)
            self.assertLessEqual(delay, expected * 1.5)

    def test_an_empty_response_counts_as_a_failure(self):
        class Empty:
            empty = True

        self.assertIsNone(detector._retry("test", lambda: Empty()))


class CliTest(unittest.TestCase):
    """--dry-run and --fixed-data: no network, no file writes."""

    def invoke(self, *extra, state_dir=None):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as inputs:
            target = state_dir or temporary
            theses_path = os.path.join(inputs, "theses.json")
            portfolio_path = os.path.join(inputs, "portfolio.json")
            with open(theses_path, "w") as handle:
                json.dump(thesis([
                    {"type": "price_below", "value": 941.62, "severity": "claim"},
                    {"type": "price_change_pct", "value": -10, "severity": "thesis"}]), handle)
            with open(portfolio_path, "w") as handle:
                json.dump({"positions": [{"symbol": "MU", "stop_weekly_close": 730}]}, handle)
            bootstrap = ("import detector,sys; detector.THESES_PATH=sys.argv.pop(1); "
                         "detector.PORTFOLIO_PATH=sys.argv.pop(1); sys.exit(detector.main())")
            process = subprocess.run(
                [sys.executable, "-c", bootstrap, theses_path, portfolio_path,
                 "--fixed-data", os.path.join(BASE, "tests", "sample.json"),
                 "--state-dir", target, *extra],
                capture_output=True, text=True, cwd=BASE)
            return process, sorted(os.listdir(target))

    def test_fixed_data_runs_and_writes_state(self):
        process, files = self.invoke()
        self.assertEqual(process.returncode, 20, process.stderr)  # hysteresis pending
        self.assertIn("violations.json", files)
        self.assertIn("awaiting confirmation", process.stdout)

    def test_dry_run_writes_nothing(self):
        process, files = self.invoke("--dry-run")
        self.assertEqual(process.returncode, 20, process.stderr)
        self.assertEqual(files, [])

    def test_two_consecutive_runs_trigger(self):
        with tempfile.TemporaryDirectory() as temporary:
            for _ in range(2):
                process, _ = self.invoke(state_dir=temporary)
            # sample.json: MU 905.40 is below 941.62 (claim) and the daily change of
            # -16.3% crosses the thesis threshold. The deviation is under 25%, so it is
            # not suspect and confirms on the second check.
            self.assertEqual(process.returncode, 20, process.stdout + process.stderr)
            with open(os.path.join(temporary, "violations.json"),
                      encoding="utf-8") as handle:
                state = json.load(handle)
        self.assertTrue(state["triggered"])
        self.assertTrue(any(item["severity"] == "thesis"
                            for item in state["triggered"]))

    def test_full_review_runs_even_when_no_legacy_migration_is_needed(self):
        with tempfile.TemporaryDirectory() as temporary:
            process, _ = self.invoke("--full-review", state_dir=temporary)
        self.assertEqual(process.returncode, 20, process.stdout + process.stderr)
        self.assertIn("[THESIS]",process.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
