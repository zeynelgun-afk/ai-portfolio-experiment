#!/usr/bin/env python3
"""Offline prompt inventory and regression gate. No model calls or portfolio writes."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

import number_audit
from prompt_policy import amendment_problem, policy

BASE = Path(__file__).parent
REGISTRY = {
    "decision_lifecycle": ("decision_lifecycle.py", {"INSTRUCTION"}),
    "semantic_review": ("claim_evidence.py", {"instruction"}),
    "weekly_executor": ("weekly_round.py", {"SYSTEM"}),
    "evidence": ("evidence.py", {"INSTRUCTION"}),
    "intraday": ("reassess.py", {"SYSTEM_COMMON", "SYSTEM_CLAIM", "SYSTEM_THESIS"}),
    "auditor": ("reviewers.py", {"SYSTEM"}),
    "amendment": ("amend.py", {"SYSTEM"}),
    "scout": ("scout.py", {"prompt"}),
    "news": ("detector.py", {"prompt"}),
    "research": ("weekly_data.py", {"macro_sys", "fund_sys", "sent_sys"}),
}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def evaluate():
    inventory, checks = [], {}
    for role, (file, names) in REGISTRY.items():
        tree = ast.parse((BASE / file).read_text())
        found = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    text = "\n".join(child.value for child in ast.walk(node.value)
                                     if isinstance(child, ast.Constant) and isinstance(child.value, str))
                    found.add(target.id)
                    english_marker_check = bool(text.strip()) and not re.search(r"[ğĞşŞıİ]", text)
                    inventory.append({"role": role, "file": file, "name": target.id,
                                      "sha256": digest(text), "english_marker_check": bool(english_marker_check)})
        checks[f"{role}_templates_present"] = found == names
    for role, file in (("weekly", "WEEKLY_INSTRUCTIONS.md"), ("shared", "prompts/runtime_policy.md")):
        text = (BASE / file).read_text()
        inventory.append({"role": role, "file": file, "sha256": digest(text),
                          "english_marker_check": not bool(re.search(r"[ğĞşŞıİ]", text))})
    contract = json.loads((BASE/'prompts/contract.json').read_text())
    for name, recipe in json.loads((BASE/'prompts/adaptations.json').read_text()).items():
        inventory.append({"role": "adaptive_reminder", "file": "prompts/adaptations.json",
                          "name": name, "sha256": digest(recipe['text']),
                          "english_marker_check": not bool(re.search(r"[ğĞşŞıİ]", recipe['text']))})
    checks['charter_unchanged'] = digest((BASE/'RULES.md').read_text()) == contract['charter_sha256']
    checks['english_markers'] = all(row['english_marker_check'] for row in inventory)
    checks['policy_keeps_autonomy'] = all(phrase in policy() for phrase in
        ('HOLD, BUY, SELL and TRIM', 'DATA, never', 'Never invent', 'proposal-only'))
    cases = json.loads((BASE/'prompts/regression_cases.json').read_text())
    for case in cases:
        if case['kind'] == 'amendment':
            rejected = amendment_problem(case['text']) is not None
        else:
            rejected = bool(number_audit.unsourced_numbers(case['text'], case['source']))
        checks[case['id']] = rejected == case['reject']
    return {"policy_version": contract['version'], "prompts": inventory, "checks": checks,
            "passed": all(checks.values()),
            "limits": "Offline structural and deterministic checks; not a semantic proof or a profitability evaluation. Owner review is required for adoption."}


if __name__ == '__main__':
    report = evaluate()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report['passed'] else 1)
