#!/usr/bin/env python3
"""The adversarial review layer — two auditors, two model families, consensus only.

An auditor that reads the same data as the decision-maker produces a correlated second
guess. Two things are done about that here:

  1. The auditors are fed the deterministic scorecard (`audit.py`) first. They argue from
     what happened, not from the same prose the decision-maker wrote.
  2. They run on two different model families, and **a finding is recorded only when both
     report the same pattern**. One model's idiosyncratic reading is not a finding; the
     same fault seen from two directions is.

The auditors judge REASONING, never outcomes, and they may not propose trades — that is
the decision-maker's job, and an auditor that starts trading is no longer an auditor. A
good decision can have a bad outcome; the scorecard supplies the outcome so the auditor
does not have to guess at it, and the prompt forbids scoring the decision by it.

Findings use a closed taxonomy. Free text cannot be matched across two models, so
consensus would be impossible to compute and the second auditor would be decoration.

Usage (normally invoked by audit.py --review):
    python reviewers.py --dry-run     # print both prompts, make no calls
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import reassess

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE, "DECISION_LOG.md")
AUDIT_LOG_PATH = os.path.join(BASE, "AUDIT_LOG.md")

# Verified against OpenRouter's live catalogue and exercised with a real call against this
# schema. Two families on purpose: the same family shares the same blind spots.
DEFAULT_AUDITOR_A = "anthropic/claude-opus-5.5"
DEFAULT_AUDITOR_B = "openai/gpt-5.6-sol"

# How many recent rounds of the decision log each auditor reads. Enough for the reasoning
# to be judged in context, bounded so the call stays cheap and repeatable.
ROUNDS_IN_CONTEXT = 3
# A pattern seen in this many separate audits is no longer an incident; it is a hole in
# the instructions. The number matches the charter's own lesson-calibration rule.
AMENDMENT_THRESHOLD = 3

SEVERITIES = ("low", "medium", "high")
# A finding whose severity is missing or unrecognised is still a finding — two auditors
# agreed on the fault. Dropping it over a missing label would throw away the signal to
# protect the formatting, so it is recorded at the neutral middle instead.
DEFAULT_SEVERITY = "medium"

PATTERNS = {
    "label_action_mismatch": "the thesis label and the action taken disagree",
    "deferred_decision": "a decision postponed again without new information",
    "unsourced_reasoning": "a factual claim with no source in the data provided",
    "outcome_fitted_rationale": "the rationale was bent to fit the outcome",
    "silent_departure": "departed from the previous round's stated plan without saying so",
    "threshold_miscalibrated": "a validity condition set at a number that cannot inform",
    "phantom_rule": "a removed or invented rule cited as if binding",
    "wish_as_thesis": "a hope stated where a thesis was required",
    "concentration_unexamined": "the theme concentration asserted as accepted, not examined",
    "commentary_stale": "commentary that no longer matches the data it describes",
}

SYSTEM = """You are an independent auditor of an autonomous portfolio experiment. You are
not the decision-maker and you never will be.

WHAT YOU JUDGE: the quality of the REASONING. Not the outcome. A sound decision can lose
money and a reckless one can make it; you are scoring whether the reasoning was honest,
whether it followed the experiment's own rules, and whether it would hold up if the
outcome had gone the other way. The scorecard you are given already contains the
outcomes, precisely so you do not have to infer them — use them as evidence about the
reasoning, never as the verdict.

WHAT YOU MAY NOT DO:
- Do not propose a trade, a position size, or a price target. That is the decision-maker's
  job. An auditor that starts trading has stopped auditing.
- Do not invent numbers. Every figure you cite must appear in the material you were given.
- Do not report a finding you cannot quote evidence for.
- Do not soften. If the record is clean, say it is clean and report nothing.

FINDINGS use this closed taxonomy — use the exact key, never invent one:
{patterns}

Answer with VALID JSON ONLY:
{{"findings": [
  {{"pattern": "<one key from the taxonomy>",
    "where": "<round number, claim id, or symbol>",
    "evidence": "<a short quote from the material>",
    "severity": "low" | "medium" | "high",
    "why": "<one sentence: why this is a reasoning fault, not a bad outcome>"}}
 ],
 "clean": <true if you found nothing worth reporting>}}"""


def env(name, default=""):
    return (os.environ.get(name) or default).strip()


def now_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def recent_rounds(text, count=ROUNDS_IN_CONTEXT):
    """The last `count` weekly rounds plus every intraday entry after them."""
    import audit
    rounds = audit.read_rounds(text)
    if not rounds:
        return "(the decision log is empty)"
    keep = rounds[-count:]
    start = text.find(f"## #{keep[0][0]} —")
    return text[start:] if start >= 0 else "\n\n".join(body for _, _, body in keep)


def build_prompt(scorecard, log_text, theses):
    claims = []
    for symbol, position in theses.items():
        if symbol.startswith("_"):
            continue
        claims.append(f"  {symbol}: {position.get('thesis_summary', '-')}")
        for claim in position.get("claims", []):
            claims.append(f"    [{claim['id']}] ({claim.get('status')}) "
                          f"{claim.get('text')}")
    return "\n".join([
        "=== DETERMINISTIC SCORECARD (computed from the record; no model wrote these) ===",
        json.dumps(scorecard, ensure_ascii=False, indent=2),
        "",
        "=== CURRENT THESES ===",
        "\n".join(claims) or "  (none)",
        "",
        f"=== THE LAST {ROUNDS_IN_CONTEXT} DECISION ROUNDS ===",
        log_text,
        "",
        "Audit the reasoning in these rounds against the scorecard. Report only what you "
        "can quote. If the record is clean, say so.",
    ])


def run_auditor(model, prompt, api_key, dry_run=False):
    """One auditor. Returns a list of findings, or None when the call was unusable."""
    system = SYSTEM.format(patterns="\n".join(
        f"  {key}: {description}" for key, description in sorted(PATTERNS.items())))
    if dry_run:
        print(f"--- auditor prompt ({model}) ---\n{system}\n\n{prompt[:1500]}…\n")
        return []
    payload, status = reassess.call_llm(model, system, prompt, api_key)
    if not payload or not isinstance(payload.get("findings"), list):
        print(f"WARNING auditor {model}: unusable output ({status}) — its findings are "
              "dropped, which means no consensus can form from this run")
        return None
    findings = []
    for item in payload["findings"]:
        pattern = str(item.get("pattern", "")).strip()
        if pattern not in PATTERNS:
            print(f"  {model}: discarding a finding with an unknown pattern "
                  f"({pattern!r}) — the taxonomy is closed so consensus stays computable")
            continue
        severity = str(item.get("severity", "")).strip().lower()
        findings.append({
            "pattern": pattern,
            "where": str(item.get("where", "")).strip(),
            "evidence": str(item.get("evidence", "")).strip(),
            "severity": severity if severity in SEVERITIES else DEFAULT_SEVERITY,
            "why": str(item.get("why", "")).strip(),
            "model": model,
        })
    return findings


def find_consensus(findings_a, findings_b):
    """A finding is recorded only when both auditors report the same pattern.

    Matching is on the pattern key alone, not on `where`: two models often describe the
    same fault at different granularity (one names the round, the other the claim). The
    evidence from both is kept so a reader can judge whether they really saw the same
    thing.
    """
    if findings_a is None or findings_b is None:
        return [], "one auditor produced unusable output — no consensus possible"

    by_pattern_b = {}
    for item in findings_b:
        by_pattern_b.setdefault(item["pattern"], []).append(item)

    agreed, seen = [], set()
    for item in findings_a:
        matches = by_pattern_b.get(item["pattern"])
        if not matches or item["pattern"] in seen:
            continue
        seen.add(item["pattern"])
        partner = matches[0]
        severities = [item["severity"], partner["severity"]]
        rank = {name: index for index, name in enumerate(SEVERITIES)}
        agreed.append({
            "pattern": item["pattern"],
            "description": PATTERNS[item["pattern"]],
            # The lower of the two severities: consensus is the floor of the agreement,
            # not the louder of the two opinions.
            "severity": min(severities, key=lambda s: rank.get(s, 0)),
            "auditor_a": {"where": item["where"], "evidence": item["evidence"],
                          "why": item["why"], "model": item["model"]},
            "auditor_b": {"where": partner["where"], "evidence": partner["evidence"],
                          "why": partner["why"], "model": partner["model"]},
        })
    solo = ([item["pattern"] for item in findings_a if item["pattern"] not in seen]
            + [item["pattern"] for item in findings_b if item["pattern"] not in seen])
    note = (f"{len(agreed)} agreed; {len(set(solo))} reported by one auditor only and "
            "therefore not recorded")
    return agreed, note


def update_pattern_counts(path, agreed):
    """Count how many audits each pattern has survived consensus in.

    A pattern that keeps recurring is not an incident; it is a hole in the instructions.
    At AMENDMENT_THRESHOLD the audit says so — the charter reserves the actual edit for
    the owner, so this proposes and never applies.
    """
    counts = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as handle:
                counts = json.load(handle)
        except (json.JSONDecodeError, OSError):
            counts = {}
    recurring = []
    for finding in agreed:
        entry = counts.setdefault(finding["pattern"], {"count": 0, "first_seen": None})
        entry["count"] += 1
        entry["first_seen"] = entry["first_seen"] or now_stamp()
        entry["last_seen"] = now_stamp()
        if entry["count"] >= AMENDMENT_THRESHOLD:
            recurring.append({"pattern": finding["pattern"], "count": entry["count"],
                              "since": entry["first_seen"]})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(counts, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return recurring


def append_audit_log(path, stamp, agreed, note, recurring, models):
    fresh = not os.path.exists(path)
    lines = []
    if fresh:
        lines += [
            "# Audit log — adversarial review",
            "",
            "Two independent auditors on two model families review each round's "
            "reasoning against the deterministic scorecard in `AUDIT.md`. **A finding is "
            "recorded here only when both auditors report the same pattern** — one "
            "model's idiosyncratic reading is not evidence.",
            "",
            "The auditors judge reasoning, never outcomes, and cannot propose trades. "
            "When the same pattern survives consensus three times it stops being an "
            "incident and becomes a gap in the instructions; the audit says so and the "
            "owner decides, exactly as charter rule 4 requires.",
            "",
        ]
    lines += [f"\n## {stamp}", "",
              f"Auditors: {models[0]} · {models[1]}", f"Consensus: {note}", ""]
    if not agreed:
        lines.append("No finding was reported by both auditors.")
    for finding in agreed:
        lines += [
            f"### {finding['pattern']} ({finding['severity']})",
            "",
            f"*{finding['description']}*",
            "",
            f"- **{finding['auditor_a']['model']}** at {finding['auditor_a']['where']}: "
            f"\"{finding['auditor_a']['evidence']}\" — {finding['auditor_a']['why']}",
            f"- **{finding['auditor_b']['model']}** at {finding['auditor_b']['where']}: "
            f"\"{finding['auditor_b']['evidence']}\" — {finding['auditor_b']['why']}",
            "",
        ]
    if recurring:
        lines += ["### Instruction amendment warranted", ""]
        for item in recurring:
            lines.append(f"- `{item['pattern']}` has survived consensus "
                         f"{item['count']} times since {item['since']}. Writing the rule "
                         "down again has not worked; it belongs in "
                         "`WEEKLY_INSTRUCTIONS.md` as a check, or in `theses.json` as a "
                         "condition. **The owner decides — this proposes only.**")
        lines.append("")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def review(scorecard, state_dir, dry_run=False):
    api_key = env("OPENROUTER_API_KEY")
    if not api_key and not dry_run:
        print("No OPENROUTER_API_KEY — adversarial review skipped (the scorecard in "
              "AUDIT.md is unaffected; it needs no model)")
        return []

    model_a = env("OPENROUTER_MODEL_AUDIT_A", DEFAULT_AUDITOR_A)
    model_b = env("OPENROUTER_MODEL_AUDIT_B", DEFAULT_AUDITOR_B)
    text = open(LOG_PATH, encoding="utf-8").read() if os.path.exists(LOG_PATH) else ""
    theses = reassess.read_json(os.path.join(BASE, "theses.json"), {})
    prompt = build_prompt(scorecard, recent_rounds(text), theses)

    findings_a = run_auditor(model_a, prompt, api_key, dry_run)
    findings_b = run_auditor(model_b, prompt, api_key, dry_run)
    if dry_run:
        return []

    agreed, note = find_consensus(findings_a, findings_b)
    recurring = update_pattern_counts(
        os.path.join(state_dir, "audit_patterns.json"), agreed)
    append_audit_log(AUDIT_LOG_PATH, now_stamp(), agreed, note, recurring,
                     (model_a, model_b))
    print(f"Review: {note}")
    for finding in agreed:
        print(f"  [{finding['severity']}] {finding['pattern']} — "
              f"{finding['auditor_a']['where']}")
    for item in recurring:
        print(f"  RECURRING: {item['pattern']} ×{item['count']} — instruction amendment "
              "warranted")
    return agreed


def main():
    parser = argparse.ArgumentParser(description="Run the adversarial review")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--state-dir", default=os.path.join(BASE, "state"))
    args = parser.parse_args()

    import audit
    scorecard = audit.build_scorecard(args.state_dir, fetch_prices=not args.dry_run)
    review(scorecard, args.state_dir, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
