#!/usr/bin/env python3
"""Tests for reassess.py — the LLM call is stubbed at the HTTP layer; no network.

The most important test: when the model returns malformed output, the claim's TEXT MUST
NOT CHANGE. Rewriting a thesis from a half-understood answer is worse than stale
commentary.
"""

import os
import sys
import unittest
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import number_audit as na  # noqa: E402
import reassess as ra  # noqa: E402

MOMENT = datetime(2026, 9, 28, 15, 0, tzinfo=timezone.utc)
OLD_TEXT = "HBM demand is holding the price above 941.62."


def stub_http(*responses):
    """Stand in for _single_call — the retry and audit logic stay REAL.

    Each response is either a text (a successful HTTP call) or a (None, retryable) pair.
    Once the queue runs down, the last response repeats.
    """
    queue = list(responses) or [None]
    record = {"calls": 0, "prompts": []}

    def stub(model, messages, api_key, **kwargs):
        record["calls"] += 1
        record["prompts"].append(messages[-1]["content"])
        record.setdefault("call_options", []).append(kwargs)
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        return item if isinstance(item, tuple) else (item, False)

    return stub, record


def theses():
    return {"MU": {"thesis_summary": "Memory super-cycle", "claims": [
        {"id": "MU-1", "text": OLD_TEXT, "status": "valid",
         "conditions": [{"type": "price_below", "value": 941.62, "severity": "claim"}],
         "last_updated": "2026-09-26T00:00Z", "trigger": None}]}}


def violations(severity="claim"):
    return {
        "market_open": True,
        "data": {"MU": {"price": 905.40, "price_at": MOMENT.isoformat(), "previous_close": 1082.28,
                        "data_source": "intraday_5m", "earnings_date": "2026-09-30"}},
        "triggered": [{"symbol": "MU", "claim_id": "MU-1", "severity": severity,
                       "condition_type": "price_below", "measured": 905.40,
                       "threshold": 941.62, "trigger": "price 905.40",
                       "cooldown_key": "MU-1"}],
    }


PORTFOLIO = {"cash_usd": 16421.0, "positions": [
    {"symbol": "MU", "shares": 33.6072, "entry_price": 892.67, "cost_usd": 30000.0,
     "stop_weekly_close": 730, "next_earnings": "2026-09-30"}]}


class JsonExtractionTest(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(ra.extract_json('{"status": "valid"}'), {"status": "valid"})

    def test_json_inside_a_code_fence(self):
        self.assertEqual(ra.extract_json('```json\n{"status": "weakened"}\n```'),
                         {"status": "weakened"})

    def test_json_wrapped_in_prose(self):
        raw = 'Certainly, here is the assessment:\n{"status": "invalid"}\nHope that helps.'
        self.assertEqual(ra.extract_json(raw), {"status": "invalid"})

    def test_unparseable_inputs_return_none(self):
        for broken in (None, "", "no JSON here", "{broken:", "```json\n{half\n```"):
            self.assertIsNone(ra.extract_json(broken), repr(broken))


class BudgetTest(unittest.TestCase):
    def test_a_new_week_resets_the_counter(self):
        counter, limit = ra.budget_state("/nonexistent/llm_counter.json", MOMENT)
        self.assertEqual(counter, {"week": ra.week_label(MOMENT), "calls": 0})
        self.assertEqual(limit, ra.DEFAULT_BUDGET)

    def test_the_env_limit_is_read_and_stripped(self):
        os.environ["MAX_LLM_CALLS_PER_WEEK"] = "  25 \n"
        try:
            _, limit = ra.budget_state("/nonexistent/llm_counter.json", MOMENT)
        finally:
            del os.environ["MAX_LLM_CALLS_PER_WEEK"]
        self.assertEqual(limit, 25)

    def test_a_malformed_env_falls_back_to_the_default(self):
        os.environ["MAX_LLM_CALLS_PER_WEEK"] = "sixty"
        try:
            _, limit = ra.budget_state("/nonexistent/llm_counter.json", MOMENT)
        finally:
            del os.environ["MAX_LLM_CALLS_PER_WEEK"]
        self.assertEqual(limit, ra.DEFAULT_BUDGET)


class ClaimFlowTest(unittest.TestCase):
    def setUp(self):
        self._real = ra._single_call
        self._sleep = ra.SLEEP
        ra.SLEEP = lambda seconds: None

    def tearDown(self):
        ra._single_call = self._real
        ra.SLEEP = self._sleep

    def invoke(self, response, payload=None, full=False, counter=None):
        ra._single_call = stub_http(response)[0]
        payload = payload if payload is not None else theses()
        counter = counter or {"week": "2026-W40", "calls": 0}
        updated, counter = ra.claim_flow(payload, violations(), PORTFOLIO, MOMENT,
                                        "test-model", "key", counter, 60, False, full)
        return payload["MU"]["claims"][0], updated, counter

    def test_valid_output_rewrites_the_claim(self):
        claim, updated, counter = self.invoke(
            '{"text": "The price slipped below the 50d average to {{MU.price}}.",'
            ' "status": "weakened"}')
        self.assertEqual(updated, ["MU-1"])
        self.assertEqual(claim["status"], "weakened")
        self.assertIn("905.4", claim["text"])
        self.assertEqual(claim["last_updated"], ra.iso(MOMENT))
        self.assertIn("trigger: price 905.40", claim["trigger"])
        self.assertEqual(counter["calls"], 2)

    def test_malformed_json_leaves_the_claim_text_alone(self):
        claim, updated, _ = self.invoke("the model rambled, no JSON")
        self.assertEqual(claim["text"], OLD_TEXT)
        self.assertEqual(claim["status"], "unassessed")
        self.assertIn("Assessment failed", claim["trigger"])
        self.assertIn("price 905.40", claim["trigger"])
        self.assertEqual(updated, ["MU-1"])

    def test_an_invalid_status_value_is_rejected(self):
        claim, _, _ = self.invoke('{"text": "new text", "status": "great"}')
        self.assertEqual(claim["text"], OLD_TEXT)
        self.assertEqual(claim["status"], "unassessed")

    def test_empty_text_is_rejected(self):
        claim, _, _ = self.invoke('{"text": "   ", "status": "valid"}')
        self.assertEqual(claim["text"], OLD_TEXT)
        self.assertEqual(claim["status"], "unassessed")

    def test_no_call_is_made_once_the_budget_is_spent(self):
        claim, updated, _ = self.invoke('{"text": "new", "status": "valid"}',
                                        counter={"week": "2026-W40", "calls": 60})
        self.assertEqual(updated, [])
        self.assertEqual(claim["text"], OLD_TEXT)

    def test_a_full_review_also_covers_untriggered_claims(self):
        payload = theses()
        payload["MU"]["claims"].append({
            "id": "MU-2", "text": "a second claim", "status": "valid",
            "conditions": [], "last_updated": None, "trigger": None})
        ra._single_call = stub_http('{"text": "refreshed", "status": "valid"}')[0]
        updated, _ = ra.claim_flow(payload, violations(), PORTFOLIO, MOMENT, "m", "k",
                                   {"week": "x", "calls": 0}, 60, False, True)
        self.assertEqual(sorted(updated), ["MU-1", "MU-2"])

    def test_outside_a_full_review_only_triggered_claims_are_processed(self):
        payload = theses()
        payload["MU"]["claims"].append({
            "id": "MU-2", "text": "a second claim", "status": "valid",
            "conditions": [], "last_updated": None, "trigger": None})
        ra._single_call = stub_http('{"text": "refreshed", "status": "valid"}')[0]
        updated, _ = ra.claim_flow(payload, violations(), PORTFOLIO, MOMENT, "m", "k",
                                   {"week": "x", "calls": 0}, 60, False, False)
        self.assertEqual(updated, ["MU-1"])
        self.assertEqual(payload["MU"]["claims"][1]["text"], "a second claim")


class ThesisFlowTest(unittest.TestCase):
    def setUp(self):
        self._real = ra._single_call
        self._sleep = ra.SLEEP
        ra.SLEEP = lambda seconds: None
        self.temporary = os.path.join(BASE, "tests", "_tmp")
        os.makedirs(self.temporary, exist_ok=True)
        self.notes = os.path.join(self.temporary, "pending_notes.md")
        self.decision = os.path.join(self.temporary, "pending_decision.json")
        for path in (self.notes, self.decision):
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        ra._single_call = self._real
        ra.SLEEP = self._sleep
        for path in (self.notes, self.decision):
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(self.temporary)

    def invoke(self, response, payload=None):
        ra._single_call = stub_http(response)[0]
        payload = payload if payload is not None else theses()
        decisions, counter = ra.thesis_flow(payload, violations("thesis"), PORTFOLIO,
                                            MOMENT, "deep-model", "key",
                                            {"week": "x", "calls": 0}, False,
                                            self.notes, self.decision)
        return payload, decisions, counter

    def test_a_thesis_assessment_produces_a_decision_and_a_note(self):
        payload, decisions, _ = self.invoke(
            '{"thesis_assessment": "The 50d average was lost; the thesis weakened.",'
            ' "new_thesis_summary": "The super-cycle thesis is in question below the 50d.",'
            ' "claim_statuses": {"MU-1": "weakened"},'
            ' "decision": {"action": "TRIM", "shares": 8.5, "amount_usd": null,'
            ' "new_stop": 820, "reasoning": "lost the 50d", "falsifier": "regaining the measured average"},'
            ' "saturday_note": "Revisit after earnings."}')
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["action"], "TRIM")
        self.assertEqual(decisions[0]["shares"], 8.5)
        self.assertEqual(payload["MU"]["claims"][0]["status"], "weakened")
        self.assertIn("below the 50d", payload["MU"]["thesis_summary"])
        self.assertTrue(os.path.exists(self.decision))
        with open(self.notes, encoding="utf-8") as handle:
            notes = handle.read()
        self.assertIn("THESIS LEVEL", notes)
        self.assertIn("Revisit after earnings", notes)

    def test_a_hold_decision_is_also_recorded(self):
        _, decisions, _ = self.invoke(
            '{"thesis_assessment": "The thesis stands.", "claim_statuses": {},'
            ' "decision": {"action": "HOLD", "shares": null, "amount_usd": null,'
            ' "reasoning": "the selected exit level is far away", "falsifier": "below the selected exit level"}}')
        self.assertEqual(decisions[0]["action"], "HOLD")

    def test_an_invalid_action_produces_no_decision_but_still_writes_a_note(self):
        payload, decisions, _ = self.invoke(
            '{"thesis_assessment": "Unclear.", "claim_statuses": {"MU-1": "weakened"},'
            ' "decision": {"action": "YOLO", "reasoning": "?"}}')
        self.assertEqual(decisions, [])
        self.assertEqual(payload["MU"]["claims"][0]["status"], "unassessed")
        self.assertIn("Assessment failed", payload["MU"]["claims"][0]["trigger"])
        self.assertIn("price 905.40", payload["MU"]["claims"][0]["trigger"])
        self.assertTrue(os.path.exists(self.notes))
        self.assertFalse(os.path.exists(self.decision))

    def test_malformed_output_leaves_the_claim_alone_and_marks_the_note(self):
        payload, decisions, _ = self.invoke("this is not JSON")
        claim = payload["MU"]["claims"][0]
        self.assertEqual(decisions, [])
        self.assertEqual(claim["text"], OLD_TEXT)
        self.assertEqual(claim["status"], "unassessed")
        with open(self.notes, encoding="utf-8") as handle:
            self.assertIn("UNASSESSED", handle.read())

    def test_without_a_thesis_level_trigger_nothing_happens(self):
        ra._single_call = stub_http("should not have been called")[0]
        payload = theses()
        decisions, _ = ra.thesis_flow(payload, violations("claim"), PORTFOLIO, MOMENT,
                                      "m", "k", {"week": "x", "calls": 0}, False,
                                      self.notes, self.decision)
        self.assertEqual(decisions, [])
        self.assertEqual(payload["MU"]["claims"][0]["text"], OLD_TEXT)


class TriggerMergeTest(unittest.TestCase):
    """One claim tripped by several conditions: all of them must reach the prompt."""

    def setUp(self):
        self._real = ra._single_call
        self._sleep = ra.SLEEP
        ra.SLEEP = lambda seconds: None
        self.record = {"calls": 0, "prompts": []}

    def tearDown(self):
        ra._single_call = self._real
        ra.SLEEP = self._sleep

    def multi_trigger(self):
        return {
            "market_open": True,
            "data": violations()["data"],
            "triggered": [
                {"symbol": "MU", "claim_id": "MU-1", "severity": "claim",
                 "condition_type": "price_below", "measured": 905.4, "threshold": 941.62,
                 "trigger": "price 905.40"},
                {"symbol": "MU", "claim_id": "MU-1", "severity": "claim",
                 "condition_type": "volume_ratio_20d", "measured": 3.65, "threshold": 3.0,
                 "trigger": "volume 3.6x"},
                {"symbol": "MU", "claim_id": "MU-1", "severity": "claim",
                 "condition_type": "sector_etf_change_pct", "measured": -4.93,
                 "threshold": -4.0, "trigger": "SMH -4.9%"},
            ],
        }

    def test_the_merged_trigger_contains_all_of_them(self):
        merged = ra.merge_triggers(self.multi_trigger()["triggered"])
        for expected in ("price 905.40", "volume 3.6x", "SMH -4.9%"):
            self.assertIn(expected, merged["trigger"])
        self.assertIn("price_below", merged["condition_type"])
        self.assertIn("volume_ratio_20d", merged["condition_type"])

    def test_the_most_informative_trigger_is_not_overwritten(self):
        """Regression: triggers were stored in a dict keyed by claim id, so the last one
        (the sector ETF — the weakest) overwrote the price trigger."""
        stub, record = stub_http('{"text": "new", "status": "weakened"}')
        ra._single_call = stub
        ra.claim_flow(theses(), self.multi_trigger(), PORTFOLIO, MOMENT, "m", "k",
                      {"week": "x", "calls": 0}, 60, False, False)
        self.assertEqual(record["calls"], 1, "one call per claim")
        prompt = record["prompts"][0]
        for expected in ("price 905.40", "volume 3.6x", "SMH -4.9%"):
            self.assertIn(expected, prompt)


class DoubleRewriteTest(unittest.TestCase):
    """A claim handled at thesis level must not be rewritten by the fast model after."""

    def setUp(self):
        self._real = ra._single_call

    def tearDown(self):
        ra._single_call = self._real

    def test_the_skip_list_keeps_a_claim_out_of_the_claim_flow(self):
        ra._single_call = stub_http('{"text": "the fast model wrote this",'
                                    ' "status": "valid"}')[0]
        payload = theses()
        updated, _ = ra.claim_flow(payload, violations(), PORTFOLIO, MOMENT, "m", "k",
                                   {"week": "x", "calls": 0}, 60, False, False,
                                   skip={"MU-1"})
        self.assertEqual(updated, [])
        self.assertEqual(payload["MU"]["claims"][0]["text"], OLD_TEXT)

    def test_it_is_skipped_in_a_full_review_too(self):
        ra._single_call = stub_http('{"text": "the fast model wrote this",'
                                    ' "status": "valid"}')[0]
        payload = theses()
        updated, _ = ra.claim_flow(payload, violations(), PORTFOLIO, MOMENT, "m", "k",
                                   {"week": "x", "calls": 0}, 60, False, True,
                                   skip={"MU-1"})
        self.assertEqual(updated, [])


class RetryTest(unittest.TestCase):
    """A transient failure or malformed output does not deserve giving up on try one."""

    def setUp(self):
        self._real = ra._single_call
        self._sleep = ra.SLEEP
        self.waits = []
        ra.SLEEP = self.waits.append

    def tearDown(self):
        ra._single_call = self._real
        ra.SLEEP = self._sleep

    def call(self, *responses, sources=("price 905.4 $ · threshold 941.62",), scope=None):
        stub, record = stub_http(*responses)
        ra._single_call = stub
        payload, status = ra.call_llm("m", "system", "user", "key",
                                      audit_sources=sources, audit_scope=scope)
        return payload, status, record

    def test_success_after_a_transient_failure(self):
        payload, status, record = self.call((None, True), '{"text": "ok"}')
        self.assertEqual(status, "ok")
        self.assertEqual(payload, {"text": "ok"})
        self.assertEqual(record["calls"], 2)
        self.assertEqual(self.waits, [2.0], "backoff must be applied")

    def test_the_backoff_doubles(self):
        _, status, record = self.call((None, True))
        self.assertEqual(status, "unparseable")
        self.assertEqual(record["calls"], 3)
        self.assertEqual(self.waits, [2.0, 4.0])

    def test_a_permanent_failure_is_not_retried(self):
        _, status, record = self.call((None, False))
        self.assertEqual(status, "unparseable")
        self.assertEqual(record["calls"], 1, "a 4xx must not be retried")
        self.assertEqual(self.waits, [])

    def test_malformed_json_is_fixed_after_a_reminder(self):
        payload, status, record = self.call("not JSON", '{"text": "fixed"}')
        self.assertEqual(status, "ok")
        self.assertEqual(payload["text"], "fixed")
        self.assertEqual(record["calls"], 2)
        self.assertIn("not valid JSON", record["prompts"][1])
        self.assertEqual(self.waits, [], "a parse failure does not wait")

    def test_persistently_malformed_json_gives_up(self):
        payload, status, record = self.call("no JSON at all")
        self.assertIsNone(payload)
        self.assertEqual(status, "unparseable")
        self.assertEqual(record["calls"], 3)

    def test_weekly_semantic_correction_can_use_one_bounded_extra_attempt(self):
        stub, record = stub_http('{"draft": "corrected"}')
        ra._single_call = stub
        reviews = []
        def review(payload):
            reviews.append(payload)
            if len(reviews) < 4:
                raise ValueError('Remove unsupported historical claim')
        payload, status = ra.call_llm('m', 'system', 'user', 'key',
                                      semantic_validator=review, max_attempts=4)
        self.assertEqual((payload, status), ({'draft': 'corrected'}, 'ok'))
        self.assertEqual(record['calls'], 4)
        self.assertIn('Remove unsupported historical claim', record['prompts'][3])

    def test_unsourced_numbers_are_fixed_after_feedback(self):
        payload, status, record = self.call(
            '{"text": "The analyst target is 1350 $."}',
            '{"text": "Price 905.4 $, below the 941.62 threshold."}',
            scope=ra.claim_audit_scope)
        self.assertEqual(status, "ok")
        self.assertNotIn("1350", payload["text"])
        self.assertEqual(record["calls"], 2)
        self.assertIn("1350", record["prompts"][1])
        self.assertIn("unsourced numbers", record["prompts"][1])

    def test_persistently_unsourced_numbers_are_rejected(self):
        payload, status, record = self.call('{"text": "The analyst target is 1350 $."}',
                                            scope=ra.claim_audit_scope)
        self.assertIsNone(payload, "an insistently unsourced answer must not be used")
        self.assertEqual(status, "unsourced_numbers")
        self.assertEqual(record["calls"], 3)

    def test_without_audit_sources_no_number_check_runs(self):
        stub, record = stub_http('{"text": "The analyst target is 1350 $."}')
        ra._single_call = stub
        _, status = ra.call_llm("m", "s", "u", "k", audit_sources=None)
        self.assertEqual(status, "ok")
        self.assertEqual(record["calls"], 1)


class AuditScopeTest(unittest.TestCase):
    """Decision parameters are not market claims — they must not trip the gate."""

    def test_a_new_stop_and_share_count_are_not_audited(self):
        payload = {"thesis_assessment": "The thesis weakened.", "new_thesis_summary": "",
                   "saturday_note": "",
                   "decision": {"action": "TRIM", "shares": 8.5, "new_stop": 820,
                                "reasoning": "moving the stop to 820 $",
                                "falsifier": ""}}
        prose, extra = ra.thesis_audit_scope(payload)
        clean = na.unsourced_numbers(prose, "price 905.4 threshold 941.62", *extra)
        self.assertEqual(clean, [], "decision parameters must count as sources")

    def test_an_invented_number_in_the_prose_is_still_caught(self):
        payload = {"thesis_assessment": "Market share is around 80%.",
                   "new_thesis_summary": "", "saturday_note": "", "decision": {}}
        prose, extra = ra.thesis_audit_scope(payload)
        self.assertTrue(na.unsourced_numbers(prose, "price 905.4 threshold 941.62",
                                             *extra))

    def test_the_claim_scope_takes_only_the_text(self):
        prose, extra = ra.claim_audit_scope({"text": "abc 123", "status": "valid"})
        self.assertEqual(prose, "abc 123")
        self.assertEqual(extra, ())


class SubscriptionRoutingTest(unittest.TestCase):
    def test_no_http_endpoint_override_remains(self):
        self.assertFalse(hasattr(ra, 'api_url'))

    def test_models_are_the_actual_subscription_model(self):
        self.assertEqual(ra.DEFAULT_FAST_MODEL, 'gpt-6-astra')
        self.assertEqual(ra.DEFAULT_DEEP_MODEL, 'gpt-6-astra')


class PromptTest(unittest.TestCase):
    def test_the_claim_prompt_carries_the_data_and_the_trigger(self):
        payload = theses()
        prompt = ra.claim_prompt("MU", payload["MU"], payload["MU"]["claims"][0],
                                 violations()["triggered"][0], violations()["data"],
                                 PORTFOLIO["positions"][0], MOMENT)
        for expected in ("905.4", "941.62", "intraday_5m", "MU-1", "730"):
            self.assertIn(str(expected), prompt)

    def test_the_thesis_prompt_states_the_cash_limit(self):
        payload = theses()
        prompt = ra.thesis_prompt("MU", payload["MU"], violations("thesis")["triggered"],
                                  violations()["data"], PORTFOLIO["positions"][0],
                                  PORTFOLIO["cash_usd"], MOMENT)
        self.assertIn("CASH: 16421.0", prompt)
        self.assertIn("cannot exceed this", prompt)

    def test_the_system_prompts_forbid_inventing_numbers(self):
        for system in (ra.SYSTEM_CLAIM, ra.SYSTEM_THESIS):
            self.assertIn("NEVER INVENT A NUMBER", system)





# Existing flow fixtures isolate the new independent review service; its rejection
# and citation semantics are exercised separately in test_evidence_depth.py.
def setUpModule():
    from unittest.mock import patch
    global semantic_fixture
    semantic_fixture = patch('claim_evidence.semantic_review', return_value={'verdict':'supported'})
    semantic_fixture.start()


def tearDownModule():
    semantic_fixture.stop()

if __name__ == "__main__":
    unittest.main(verbosity=2)
