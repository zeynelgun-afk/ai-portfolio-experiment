#!/usr/bin/env python3
"""Tests for execute_trade.py — the arithmetic and the gates of an autonomous trade.

Every test here asks "can this trade be done with these numbers?", never "is this
decision right?". The content of the decision belongs to the AI; the arithmetic and the
data integrity belong to the script.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import execute_trade as et  # noqa: E402

MOMENT = datetime(2026, 9, 28, 15, 0, tzinfo=timezone.utc)
TODAY = MOMENT.date()


def portfolio():
    return {
        "cash_usd": 16421.0,
        "positions": [
            {"symbol": "MU", "shares": 33.6072, "entry_price": 892.67,
             "cost_usd": 30000.0, "stop_weekly_close": 730},
            {"symbol": "NVDA", "shares": 65.11, "entry_price": 230.36,
             "cost_usd": 15000.0, "stop_weekly_close": 190},
        ],
        "trade_history": [],
    }


def live(price=905.40, symbol="MU", source=et.LIVE_SOURCE):
    return {symbol: {"price": price, "previous_close": 1082.28, "data_source": source}}


def decision(action="TRIM", symbol="MU", **extra):
    payload = {"symbol": symbol, "action": action, "shares": None, "amount_usd": None,
               "new_stop": None, "reasoning": "test reasoning",
               "falsifier": "test falsifier",
               "trigger": "price 905.40 < 941.62",
               "thesis_assessment": "test assessment", "model": "test-model"}
    payload.update(extra)
    return payload


class ValidationGateTest(unittest.TestCase):
    def validate(self, payload, *, market_open=True, data=None, locks=None, holdings=None):
        return et.validate(payload, holdings or portfolio(), data or live(), market_open,
                           locks or {}, TODAY)

    def test_a_hold_decision_produces_no_trade(self):
        ok, reason, _ = self.validate(decision("HOLD"))
        self.assertFalse(ok)
        self.assertIn("HOLD", reason)

    def test_no_trade_while_the_market_is_closed(self):
        ok, reason, _ = self.validate(decision(shares=5), market_open=False)
        self.assertFalse(ok)
        self.assertIn("market is closed", reason)

    def test_a_non_live_price_source_is_refused(self):
        ok, reason, _ = self.validate(decision(shares=5),
                                      data=live(source="daily_close"))
        self.assertFalse(ok)
        self.assertIn("not live", reason)

    def test_no_trade_without_a_price(self):
        ok, reason, _ = self.validate(decision(shares=5), data={"MU": {
            "price": None, "data_source": et.LIVE_SOURCE}})
        self.assertFalse(ok)
        self.assertIn("no measured price", reason)

    def test_shares_cannot_exceed_the_holding(self):
        ok, reason, _ = self.validate(decision(shares=100))
        self.assertFalse(ok)
        self.assertIn("more shares than held", reason)

    def test_a_buy_without_enough_cash_is_refused(self):
        ok, reason, _ = self.validate(decision("BUY", amount_usd=50000))
        self.assertFalse(ok)
        self.assertIn("not enough cash", reason)

    def test_a_symbol_not_in_the_portfolio_cannot_be_sold(self):
        ok, reason, _ = self.validate(decision("SELL", symbol="AMD"),
                                      data=live(symbol="AMD"))
        self.assertFalse(ok)
        self.assertIn("not in the portfolio", reason)

    def test_a_second_trade_in_the_same_direction_today_is_blocked(self):
        locks = {f"{TODAY.isoformat()}:MU:TRIM": "2026-09-28T14:00Z"}
        ok, reason, _ = self.validate(decision(shares=5), locks=locks)
        self.assertFalse(ok)
        self.assertIn("already happened today", reason)

    def test_invalid_share_and_amount_values(self):
        for payload in (decision(shares=None), decision(shares=-3),
                        decision(shares="many"), decision("BUY", amount_usd=0),
                        decision("BUY", amount_usd=None)):
            ok, reason, _ = self.validate(payload)
            self.assertFalse(ok, payload)
            self.assertIn("invalid", reason)

    def test_a_valid_trim_passes(self):
        ok, reason, details = self.validate(decision(shares=10))
        self.assertTrue(ok, reason)
        self.assertAlmostEqual(details["amount"], 10 * 905.40, places=2)

    def test_a_sell_clamps_the_share_count_to_the_holding(self):
        ok, _, details = self.validate(decision("SELL", shares=999))
        self.assertTrue(ok)
        self.assertAlmostEqual(details["shares"], 33.6072, places=4)


class ArithmeticTest(unittest.TestCase):
    def test_a_trim_reduces_shares_and_cost_proportionally(self):
        book = portfolio()
        details = {"shares": 10.0, "price": 905.40, "amount": 9054.0}
        record = et.execute(decision("TRIM", shares=10), book, details, MOMENT)
        holding = next(p for p in book["positions"] if p["symbol"] == "MU")
        self.assertAlmostEqual(holding["shares"], 23.6072, places=4)
        # 30000 * (23.6072 / 33.6072) = 21073.34
        self.assertAlmostEqual(holding["cost_usd"], 21073.34, places=2)
        self.assertAlmostEqual(book["cash_usd"], 16421.0 + 9054.0, places=2)
        self.assertEqual(record["action"], "TRIM")
        self.assertEqual(record["source"], "intraday_autonomous")

    def test_a_sell_removes_the_position_entirely(self):
        book = portfolio()
        details = {"shares": 33.6072, "price": 905.40, "amount": 30428.36}
        record = et.execute(decision("SELL", shares=33.6072), book, details, MOMENT)
        self.assertEqual([p["symbol"] for p in book["positions"]], ["NVDA"])
        self.assertAlmostEqual(book["cash_usd"], 16421.0 + 30428.36, places=2)
        self.assertEqual(record["action"], "SELL")

    def test_a_buy_into_an_existing_position_recomputes_the_average_entry(self):
        book = portfolio()
        details = {"shares": 10.0, "price": 905.40, "amount": 9054.0}
        et.execute(decision("BUY", symbol="MU", amount_usd=9054.0), book, details, MOMENT)
        holding = next(p for p in book["positions"] if p["symbol"] == "MU")
        self.assertAlmostEqual(holding["shares"], 43.6072, places=4)
        self.assertAlmostEqual(holding["cost_usd"], 39054.0, places=2)
        # 39054 / 43.6072 = 895.59
        self.assertAlmostEqual(holding["entry_price"], 895.59, places=2)
        self.assertAlmostEqual(book["cash_usd"], 16421.0 - 9054.0, places=2)

    def test_a_buy_opens_a_position_in_a_new_symbol(self):
        book = portfolio()
        details = {"shares": 20.0, "price": 500.0, "amount": 10000.0}
        et.execute(decision("BUY", symbol="AMD", amount_usd=10000.0, new_stop=440),
                   book, details, MOMENT)
        holding = next(p for p in book["positions"] if p["symbol"] == "AMD")
        self.assertEqual(holding["entry_date"], TODAY.isoformat())
        self.assertEqual(holding["stop_weekly_close"], 440)

    def test_a_new_stop_is_written_onto_an_existing_position(self):
        book = portfolio()
        details = {"shares": 5.0, "price": 905.40, "amount": 4527.0}
        et.execute(decision("TRIM", shares=5, new_stop=820), book, details, MOMENT)
        holding = next(p for p in book["positions"] if p["symbol"] == "MU")
        self.assertEqual(holding["stop_weekly_close"], 820)

    def test_the_trade_record_carries_the_time_and_the_source(self):
        book = portfolio()
        et.execute(decision("TRIM", shares=5), book,
                   {"shares": 5.0, "price": 905.40, "amount": 4527.0}, MOMENT)
        record = book["trade_history"][-1]
        self.assertEqual(record["time_utc"], "15:00")
        self.assertEqual(book["last_updated"], TODAY.isoformat())


class EndToEndTest(unittest.TestCase):
    """The main() flow: pending_decision.json -> portfolio.json + DECISION_LOG.md."""

    def build(self, temporary, decisions, market_open=True, source=et.LIVE_SOURCE):
        state = os.path.join(temporary, "state")
        os.makedirs(state)
        et.write_json(os.path.join(state, "pending_decision.json"),
                      {"time": "2026-09-28T15:00Z", "decisions": decisions})
        et.write_json(os.path.join(state, "violations.json"),
                      {"market_open": market_open, "data": live(source=source)})
        et.PORTFOLIO_PATH = os.path.join(temporary, "portfolio.json")
        et.LOG_PATH = os.path.join(temporary, "DECISION_LOG.md")
        et.write_json(et.PORTFOLIO_PATH, portfolio())
        with open(et.LOG_PATH, "w", encoding="utf-8") as handle:
            handle.write("# Decision Log\n")
        return state

    def invoke(self, state, *extra):
        original = sys.argv
        sys.argv = ["execute_trade.py", "--state-dir", state, *extra]
        try:
            return et.main()
        finally:
            sys.argv = original

    def setUp(self):
        self._paths = (et.PORTFOLIO_PATH, et.LOG_PATH)

    def tearDown(self):
        et.PORTFOLIO_PATH, et.LOG_PATH = self._paths

    def test_an_executed_trade_reaches_the_files_and_the_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = self.build(temporary, [decision("TRIM", shares=10)])
            self.assertEqual(self.invoke(state), 0)
            with open(et.PORTFOLIO_PATH, encoding="utf-8") as handle:
                book = json.load(handle)
            with open(et.LOG_PATH, encoding="utf-8") as handle:
                log = handle.read()
            self.assertAlmostEqual(
                next(p["shares"] for p in book["positions"] if p["symbol"] == "MU"),
                23.6072, places=4)
            self.assertIn("INTRADAY DECISION", log)
            self.assertIn("(EXECUTED)", log)
            self.assertIn("test falsifier", log)
            # The decision bundle has been consumed
            self.assertFalse(os.path.exists(
                os.path.join(state, "pending_decision.json")))
            with open(os.path.join(state, "trade_lock.json"), encoding="utf-8") as handle:
                self.assertTrue(json.load(handle))

    def test_a_snapshot_is_taken_and_rollback_restores_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = self.build(temporary, [decision("TRIM", shares=10)])
            with open(et.PORTFOLIO_PATH, encoding="utf-8") as handle:
                before = json.load(handle)
            self.assertEqual(self.invoke(state), 0)
            snapshot = os.path.join(state, "portfolio_snapshot.json")
            self.assertTrue(os.path.exists(snapshot), "a snapshot must be taken")
            self.assertEqual(self.invoke(state, "--rollback"), 0)
            with open(et.PORTFOLIO_PATH, encoding="utf-8") as handle:
                after = json.load(handle)
        self.assertEqual(before, after, "rollback must restore the pre-trade state")

    def test_rollback_without_a_snapshot_fails_loudly(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = self.build(temporary, [])
            self.assertEqual(self.invoke(state, "--rollback"), 1)

    def test_a_rejected_decision_reaches_the_log_and_the_pending_notes(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = self.build(temporary, [decision("TRIM", shares=10)],
                               market_open=False)
            self.assertEqual(self.invoke(state), 0)
            with open(et.PORTFOLIO_PATH, encoding="utf-8") as handle:
                book = json.load(handle)
            with open(et.LOG_PATH, encoding="utf-8") as handle:
                log = handle.read()
            with open(os.path.join(state, "pending_notes.md"),
                      encoding="utf-8") as handle:
                notes = handle.read()
            # The position was left untouched
            self.assertAlmostEqual(
                next(p["shares"] for p in book["positions"] if p["symbol"] == "MU"),
                33.6072, places=4)
            self.assertIn("(NOT EXECUTED)", log)
            self.assertIn("market is closed", log)
            self.assertIn("DECISION NOT EXECUTED", notes)

    def test_dry_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = self.build(temporary, [decision("TRIM", shares=10)])
            with open(et.PORTFOLIO_PATH, encoding="utf-8") as handle:
                before = handle.read()
            self.assertEqual(self.invoke(state, "--dry-run"), 0)
            with open(et.PORTFOLIO_PATH, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), before)
            self.assertTrue(os.path.exists(
                os.path.join(state, "pending_decision.json")))

    def test_it_exits_quietly_when_there_is_no_decision(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = self.build(temporary, [])
            self.assertEqual(self.invoke(state), 0)


class AtomicWriteTest(unittest.TestCase):
    """A crash mid-write must not leave portfolio.json half-rewritten."""

    def test_no_temporary_file_survives_a_successful_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = os.path.join(temporary, "portfolio.json")
            et.write_json(target, {"positions": []})
            self.assertEqual(os.listdir(temporary), ["portfolio.json"])

    def test_a_failed_write_leaves_the_original_intact(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = os.path.join(temporary, "portfolio.json")
            et.write_json(target, {"positions": [], "marker": "original"})

            class Unserializable:
                pass

            with self.assertRaises(TypeError):
                et.write_json(target, {"bad": Unserializable()})
            with open(target, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["marker"], "original")
            self.assertEqual(os.listdir(temporary), ["portfolio.json"],
                             "the temporary file must be cleaned up")


if __name__ == "__main__":
    unittest.main(verbosity=2)
