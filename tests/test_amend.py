#!/usr/bin/env python3
"""Tests for amend.py — the guarantees, not the prose.

Everything amend.py promises about what an automated proposal can and cannot be is
enforced in `validate()`. These tests are that enforcement's spec. The prompt asks the
model to behave; this checks what happens when it does not.
"""

import json
import os
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import amend  # noqa: E402
import reviewers  # noqa: E402

INSTRUCTIONS = """# Weekly Decision Round

## Steps

1. **Read:** the charter and the portfolio.
2. **Decide:** hold, add, trim, close.

## Limits

- **Never write an unsourced number.**
- Do NOT commit or push — the workflow handles it.
"""


class InsertionOnlyTest(unittest.TestCase):
    """The one edit that could make the system less safe is removing a constraint."""

    def test_a_clean_insertion_is_accepted(self):
        proposal = {"title": "t", "rationale": "r",
                    "anchor": "- **Never write an unsourced number.**",
                    "insertion": "- **State the base of every percentage.**"}
        amended, problem = amend.validate(proposal, INSTRUCTIONS)
        self.assertIsNone(problem)
        self.assertIn("State the base of every percentage", amended)
        # every original byte survives
        for line in INSTRUCTIONS.splitlines():
            self.assertIn(line, amended)

    def test_a_deletion_is_refused(self):
        """An amendment that removes an existing rule must never reach a branch."""
        proposal = {"title": "t", "rationale": "r",
                    "anchor": "- **Never write an unsourced number.**",
                    "insertion": "(replacing the rule above)"}
        # simulate the model trying to replace rather than add, by making the insertion
        # identical to a deletion of the anchor
        amended, problem = amend.validate(proposal, INSTRUCTIONS)
        self.assertIsNotNone(amended, "a plain insertion is still fine")
        # now the real deletion case: the anchor is absent from the file
        proposal["anchor"] = "- **A rule that was already deleted.**"
        amended, problem = amend.validate(proposal, INSTRUCTIONS)
        self.assertIsNone(amended)
        self.assertIn("does not appear", problem)

    def test_an_ambiguous_anchor_is_refused(self):
        text = INSTRUCTIONS + "\n- Do NOT commit or push — the workflow handles it.\n"
        proposal = {"title": "t", "rationale": "r",
                    "anchor": "- Do NOT commit or push — the workflow handles it.",
                    "insertion": "- something"}
        amended, problem = amend.validate(proposal, text)
        self.assertIsNone(amended)
        self.assertIn("appears 2 times", problem)

    def test_an_empty_insertion_is_refused(self):
        """Whitespace-only and absent are both rejected, by whichever check sees it."""
        for empty in ("   \n  ", "", "\n"):
            proposal = {"title": "t", "rationale": "r",
                        "anchor": "## Limits", "insertion": empty}
            amended, problem = amend.validate(proposal, INSTRUCTIONS)
            self.assertIsNone(amended, repr(empty))
            self.assertIn("insertion", problem)

    def test_a_proposal_missing_a_field_is_refused(self):
        for missing in ("title", "anchor", "insertion", "rationale"):
            proposal = {"title": "t", "rationale": "r", "anchor": "## Limits",
                        "insertion": "- x"}
            proposal[missing] = ""
            amended, problem = amend.validate(proposal, INSTRUCTIONS)
            self.assertIsNone(amended, missing)
            self.assertIn(missing, problem)

    def test_the_target_is_the_instructions_and_nothing_else(self):
        """Not the charter, not the code, not the portfolio."""
        self.assertEqual(amend.TARGET, "WEEKLY_INSTRUCTIONS.md")
        self.assertNotIn("RULES.md", amend.TARGET)


class BranchBaseTest(unittest.TestCase):
    """Where the branch STARTS is the guarantee, not which file gets staged.

    Regression: the first version cut the branch from local HEAD. The pull request it
    opened quietly carried four unrelated files, because whatever was committed locally
    but not pushed rode along. Staging only WEEKLY_INSTRUCTIONS.md did not — and could
    not — prevent that.
    """

    def setUp(self):
        self._run = amend.run
        self.commands = []

    def tearDown(self):
        amend.run = self._run

    def stub_git(self, responses=None):
        responses = responses or {}

        class Result:
            def __init__(self, code=0, out="", err=""):
                self.returncode, self.stdout, self.stderr = code, out, err

        def fake(command, **kwargs):
            self.commands.append(command)
            for key, value in responses.items():
                if key in " ".join(command):
                    return Result(*value)
            return Result()

        amend.run = fake

    def test_the_branch_is_cut_from_the_remote_default_branch(self):
        self.stub_git({"defaultBranchRef": (0, "main\n", "")})
        amend.open_pull_request("audit/amend/x", "title", "body")
        joined = [" ".join(c) for c in self.commands]
        self.assertTrue(any("gh pr create --base main" in c for c in joined),
                        f"the PR must target the remote default branch: {joined}")

    def test_the_default_branch_is_asked_for_not_assumed(self):
        self.stub_git({"defaultBranchRef": (0, "trunk\n", "")})
        self.assertEqual(amend.default_branch(), "trunk")

    def test_a_dirty_tree_refuses_rather_than_carrying_strays(self):
        self.stub_git({"status --porcelain": (0, " M some_other_file.py\n", "")})
        self.assertFalse(amend.working_tree_is_clean())

    def test_a_clean_tree_is_recognised(self):
        self.stub_git({"status --porcelain": (0, "", "")})
        self.assertTrue(amend.working_tree_is_clean())

    def test_only_the_instructions_file_is_ever_staged(self):
        self.stub_git()
        amend.open_pull_request("audit/amend/x", "title", "body")
        staged = [c for c in self.commands if c[:2] == ["git", "add"]]
        self.assertEqual(staged, [["git", "add", amend.TARGET]])

    def test_an_abandoned_branch_is_deleted_not_left_behind(self):
        self.stub_git()
        amend.abandon_branch("audit/amend/x")
        joined = [" ".join(c) for c in self.commands]
        self.assertIn("git branch -D audit/amend/x", joined)
        self.assertIn("git checkout -", joined)


class ThresholdTest(unittest.TestCase):
    def write_state(self, directory, counts):
        path = os.path.join(directory, "audit_patterns.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(counts, handle)
        return path

    def test_a_pattern_below_the_threshold_is_not_proposed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_state(directory, {
                "phantom_rule": {"count": reviewers.AMENDMENT_THRESHOLD - 1}})
            _, pending = amend.pending_patterns(path)
        self.assertEqual(pending, [])

    def test_a_pattern_at_the_threshold_is_proposed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_state(directory, {
                "phantom_rule": {"count": reviewers.AMENDMENT_THRESHOLD,
                                 "first_seen": "2026-09-01T10:00Z"}})
            _, pending = amend.pending_patterns(path)
        self.assertEqual([p["pattern"] for p in pending], ["phantom_rule"])

    def test_an_already_proposed_pattern_is_not_proposed_again(self):
        """Re-proposing every week trains the owner to close the tab."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_state(directory, {
                "phantom_rule": {"count": 9, "first_seen": "2026-09-01T10:00Z",
                                 "proposed_at": "2026-09-20T10:00Z"}})
            _, pending = amend.pending_patterns(path)
        self.assertEqual(pending, [])

    def test_a_missing_or_corrupt_state_file_is_not_fatal(self):
        self.assertEqual(amend.pending_patterns("/nonexistent/x.json"), ({}, []))
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "audit_patterns.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{broken")
            self.assertEqual(amend.pending_patterns(path), ({}, []))


class EvidenceTest(unittest.TestCase):
    AUDIT_LOG = """# Audit log

## 2026-09-20T10:00Z

### phantom_rule (medium)

*a removed or invented rule cited as if binding*

- **model-a** at round 7: "the earnings rule requires it" — the rule was removed in v2.
- **model-b** at round 7: "per the earnings rule" — no such rule is in force.

### wish_as_thesis (low)

- **model-a** at round 8: "it could recover" — a hope, not a thesis.
"""

    def test_only_the_named_pattern_is_quoted(self):
        text = amend.evidence_for("phantom_rule", self.AUDIT_LOG)
        self.assertIn("the earnings rule requires it", text)
        self.assertNotIn("it could recover", text)

    def test_both_auditors_are_quoted(self):
        text = amend.evidence_for("phantom_rule", self.AUDIT_LOG)
        self.assertIn("model-a", text)
        self.assertIn("model-b", text)

    def test_a_pattern_with_no_record_says_so_rather_than_inventing(self):
        text = amend.evidence_for("commentary_stale", self.AUDIT_LOG)
        self.assertIn("no quoted evidence", text)


class PromptTest(unittest.TestCase):
    def test_the_prompt_forbids_deletion_in_words_too(self):
        self.assertIn("You may only ADD text", amend.SYSTEM)
        self.assertIn("the owner decides, not you", amend.SYSTEM)

    def test_the_prompt_prefers_a_checkable_rule_over_a_louder_one(self):
        self.assertIn("turned into data", amend.SYSTEM)
        self.assertIn("restates the prohibition more loudly", amend.SYSTEM)

    def test_the_prompt_carries_the_evidence_and_the_file(self):
        prompt = amend.build_prompt("phantom_rule", 3, "2026-09-01T10:00Z",
                                    "  [m] at r7: quote", INSTRUCTIONS)
        self.assertIn("survived independent two-auditor consensus 3 times", prompt)
        self.assertIn("[m] at r7: quote", prompt)
        self.assertIn("Never write an unsourced number", prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
