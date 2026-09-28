#!/usr/bin/env python3
"""Propose an instruction amendment when the same fault keeps surviving consensus.

The loop this closes: `WEEKLY_INSTRUCTIONS.md`'s version history is a list of moments
where a human noticed a failure pattern and turned it into a rule. Versions 6, 7 and 8
all came from that. Nobody was doing it any more, so the patterns kept recurring and the
audit kept re-reporting them. This turns the noticing into a proposal.

**It proposes; it never applies.** Charter rule 4 reserves the edit for the owner, and a
pull request is exactly that shape: a branch, a diff, and a decision that is not the AI's.
Three guarantees make that real, and all three are enforced in code rather than asked for
in a prompt:

  1. **Only `WEEKLY_INSTRUCTIONS.md`.** Not `RULES.md` (the charter itself), not the code,
     not `portfolio.json`, not `theses.json`. A process that can rewrite the charter or
     the executor is not proposing, it is governing. The branch is cut from the REMOTE
     default branch, never from local HEAD — the first version of this module cut from
     HEAD and the resulting pull request quietly carried four unrelated files. The
     guarantee has to come from where the branch starts, not from which file is staged.
  2. **Insertion only — never deletion or replacement.** Removing a constraint is the one
     edit that can make the system less safe, and it is precisely the edit an AI under
     audit has an interest in making. The proposal can only add a check.
  3. **Never merged, never pushed to the default branch.** The branch is opened and left
     there.

A pattern is proposed once. Re-proposing the same amendment every week would train the
owner to close the tab, which is the same failure as an audit nobody reads.

Usage:
    python amend.py --dry-run     # show what would be proposed, touch nothing
    python amend.py               # write the branch and open the pull request
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

import reassess
import reviewers

BASE = os.path.dirname(os.path.abspath(__file__))
TARGET = "WEEKLY_INSTRUCTIONS.md"
TARGET_PATH = os.path.join(BASE, TARGET)
AUDIT_LOG_PATH = os.path.join(BASE, "AUDIT_LOG.md")

BRANCH_PREFIX = "audit/amend"
COMMITTER_NAME = "Finzora AI"
COMMITTER_EMAIL = "finzora-bot@users.noreply.github.com"

SYSTEM = """You propose ONE minimal amendment to the instructions of an autonomous
portfolio experiment, because the same reasoning fault has now survived independent
review three times. Writing the existing rule down again has not worked.

The experiment's own principle applies: **if writing a rule down is not enough, the rule
gets turned into data.** Prefer an amendment that makes the fault checkable — a required
line in the record, a number that must be written, a question that must be answered in
writing — over one that restates the prohibition more loudly.

HARD CONSTRAINTS, enforced in code after you answer:
- You may only ADD text. You cannot delete, weaken or replace an existing rule. If you
  believe an existing rule is wrong, say so in `rationale`; the owner decides, not you.
- You are amending the instructions only. You cannot touch the charter, the code, the
  portfolio or the theses.
- `anchor` must be a line copied EXACTLY from the instructions you were given, and it
  must appear there exactly once. Your text is inserted directly after it.
- Do not invent evidence. Quote only from the audit findings you were given.

Answer with VALID JSON ONLY:
{"title": "<a short pull-request title, imperative mood>",
 "anchor": "<the exact existing line to insert after>",
 "insertion": "<the new text, markdown, matching the surrounding style>",
 "rationale": "<why this amendment catches the fault the old wording missed>",
 "makes_checkable": <true if the amendment turns the rule into something mechanically
                     verifiable rather than restating it>}"""


def env(name, default=""):
    return (os.environ.get(name) or default).strip()


def now_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def run(command, **kwargs):
    return subprocess.run(command, capture_output=True, text=True, cwd=BASE, **kwargs)


def pending_patterns(state_path):
    """Patterns at the threshold that have not been proposed yet."""
    if not os.path.exists(state_path):
        return {}, []
    try:
        with open(state_path, encoding="utf-8") as handle:
            counts = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}, []
    pending = [
        {"pattern": name, **entry} for name, entry in sorted(counts.items())
        if entry.get("count", 0) >= reviewers.AMENDMENT_THRESHOLD
        and not entry.get("proposed_at")
    ]
    return counts, pending


def evidence_for(pattern, audit_log_text, limit=6):
    """Every recorded finding for one pattern, as quoted in the audit log."""
    blocks = re.split(r"^### ", audit_log_text, flags=re.MULTILINE)
    found = []
    for block in blocks:
        if not block.startswith(pattern):
            continue
        quotes = re.findall(r"^- \*\*(.+?)\*\* at (.+?): (.+)$", block, re.MULTILINE)
        for model, where, rest in quotes:
            found.append(f"  [{model}] at {where}: {rest.strip()}")
    return "\n".join(found[:limit]) or "  (no quoted evidence found in the audit log)"


def build_prompt(pattern, count, since, evidence, instructions):
    return "\n".join([
        f"PATTERN: {pattern} — {reviewers.PATTERNS.get(pattern, 'unknown')}",
        f"It has survived independent two-auditor consensus {count} times since {since}.",
        "",
        "THE RECORDED EVIDENCE (both auditors, across those audits):",
        evidence,
        "",
        f"=== CURRENT {TARGET} ===",
        instructions,
        "",
        "Propose one minimal amendment that would catch this fault. Remember: you may "
        "only add, and `anchor` must be an exact line from the file above.",
    ])


def validate(proposal, instructions):
    """Every guarantee the module promises is checked here, not asked for in the prompt."""
    for field in ("title", "anchor", "insertion", "rationale"):
        if not str(proposal.get(field, "")).strip():
            return None, f"the proposal has no {field}"

    anchor = str(proposal["anchor"]).rstrip("\n")
    occurrences = instructions.count(anchor)
    if occurrences == 0:
        return None, "the anchor line does not appear in the file — nothing to insert after"
    if occurrences > 1:
        return None, (f"the anchor line appears {occurrences} times — the insertion point "
                      "is ambiguous")

    insertion = str(proposal["insertion"]).strip("\n")
    if not insertion:
        return None, "the insertion is empty"

    amended = instructions.replace(anchor, anchor + "\n\n" + insertion, 1)
    # Insertion only: every byte of the original must survive, and the file must grow.
    if len(amended) <= len(instructions):
        return None, "the amendment does not add text"
    stripped = amended.replace("\n\n" + insertion, "", 1)
    if stripped != instructions:
        return None, ("the amendment changes existing text — only additions are allowed, "
                      "because removing a constraint is the one edit that can make the "
                      "system less safe")
    return amended, None


def default_branch():
    """The remote's default branch — the only base a proposal may be cut from."""
    result = run(["gh", "repo", "view", "--json", "defaultBranchRef",
                  "--jq", ".defaultBranchRef.name"])
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    result = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"])
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().split("/", 1)[-1]
    return "main"


def working_tree_is_clean():
    result = run(["git", "status", "--porcelain"])
    return result.returncode == 0 and not result.stdout.strip()


def open_pull_request(branch, title, body, dry_run=False):
    """Create the branch, commit the amended file, push and open the PR."""
    if dry_run:
        print(f"[dry-run] would open branch {branch} and a pull request titled: {title}")
        return True
    base = default_branch()
    steps = [
        ["git", "config", "user.name", COMMITTER_NAME],
        ["git", "config", "user.email", COMMITTER_EMAIL],
        ["git", "add", TARGET],
        ["git", "commit", "-m", title, "-m", body],
        ["git", "push", "--set-upstream", "origin", branch],
    ]
    for command in steps:
        result = run(command)
        if result.returncode != 0:
            print(f"ERROR: {' '.join(command)} failed: {result.stderr.strip()[:200]}")
            run(["git", "checkout", "-"])
            return False
    created = run(["gh", "pr", "create", "--base", base, "--head", branch,
                   "--title", title, "--body", body, "--label", "audit"])
    if created.returncode != 0:
        # The label may not exist in a fresh repository; retry without it rather than
        # losing the proposal over a piece of metadata.
        created = run(["gh", "pr", "create", "--base", base, "--head", branch,
                       "--title", title, "--body", body])
    run(["git", "checkout", "-"])
    if created.returncode != 0:
        print(f"ERROR: gh pr create failed: {created.stderr.strip()[:200]}")
        return False
    print(f"Pull request opened: {created.stdout.strip()}")
    return True


def abandon_branch(branch):
    """Leave no half-made proposal behind: drop the edit and the branch, return home."""
    run(["git", "checkout", "--", TARGET])
    run(["git", "checkout", "-"])
    run(["git", "branch", "-D", branch])


def propose(state_dir, dry_run=False):
    state_path = os.path.join(state_dir, "audit_patterns.json")
    counts, pending = pending_patterns(state_path)
    if not pending:
        print("No pattern has reached the amendment threshold without already being "
              "proposed")
        return 0

    api_key = env("OPENROUTER_API_KEY")
    if not api_key and not dry_run:
        print("No OPENROUTER_API_KEY — the amendment text cannot be written; the "
              "recurring patterns stay flagged in AUDIT_LOG.md")
        return 0

    if not dry_run and not working_tree_is_clean():
        print("REFUSING: the working tree has uncommitted changes. A proposal branch cut "
              "over a dirty tree carries whatever happens to be lying around — commit or "
              "stash first.")
        return 1

    model = env("OPENROUTER_MODEL_DEEP", reassess.DEFAULT_DEEP_MODEL)
    audit_log = (open(AUDIT_LOG_PATH, encoding="utf-8").read()
                 if os.path.exists(AUDIT_LOG_PATH) else "")
    opened = 0
    base = default_branch() if not dry_run else "(dry-run)"

    for item in pending:
        pattern = item["pattern"]
        branch = f"{BRANCH_PREFIX}/{pattern}-{datetime.now(timezone.utc):%Y%m%d}"

        if dry_run:
            instructions = open(TARGET_PATH, encoding="utf-8").read()
            prompt = build_prompt(pattern, item["count"],
                                  item.get("first_seen", "unknown"),
                                  evidence_for(pattern, audit_log), instructions)
            print(f"--- amendment prompt for {pattern} ({model}) ---")
            print(prompt[:1200] + "…\n")
            continue

        # Cut the branch from the REMOTE default branch first, then read the file from
        # it. Reading locally and pushing to a branch cut elsewhere would validate one
        # version and commit another.
        run(["git", "fetch", "origin", base])
        checkout = run(["git", "checkout", "-b", branch, f"origin/{base}"])
        if checkout.returncode != 0:
            print(f"ERROR {pattern}: could not branch from origin/{base}: "
                  f"{checkout.stderr.strip()[:160]}")
            continue

        instructions = open(TARGET_PATH, encoding="utf-8").read()
        prompt = build_prompt(pattern, item["count"], item.get("first_seen", "unknown"),
                              evidence_for(pattern, audit_log), instructions)
        proposal, status = reassess.call_llm(model, SYSTEM, prompt, api_key)
        if not proposal:
            print(f"WARNING {pattern}: the amendment could not be written ({status}) — "
                  "the pattern stays flagged and will be retried next week")
            abandon_branch(branch)
            continue

        amended, problem = validate(proposal, instructions)
        if amended is None:
            print(f"REJECTED {pattern}: {problem}")
            abandon_branch(branch)
            continue

        with open(TARGET_PATH, "w", encoding="utf-8") as handle:
            handle.write(amended)

        checkable = (
            "**yes**" if proposal.get("makes_checkable") else
            "**no** — it restates the rule, which is what already failed. Consider "
            "whether a condition in `theses.json` would serve better."
        )
        title = f"[audit] {str(proposal['title']).strip()}"
        body = "\n".join([
            "An automated proposal from the audit layer. **It proposes; it does not "
            "apply** — merging is the owner's decision, as charter rule 4 requires.",
            "",
            "## Why",
            "",
            f"`{pattern}` — {reviewers.PATTERNS.get(pattern, '')} — has survived "
            f"independent two-auditor consensus **{item['count']} times** since "
            f"{item.get('first_seen', 'unknown')}. Every one of those findings was "
            "reported by two auditors running on two different model families; a fault "
            "only one of them saw never reaches the audit log.",
            "",
            "Writing the existing rule down again has not worked. The experiment's own "
            "principle applies: *if writing a rule down is not enough, the rule gets "
            "turned into data.*",
            "",
            "## The reasoning behind this wording",
            "",
            str(proposal["rationale"]).strip(),
            "",
            "## Recorded evidence",
            "",
            "```",
            evidence_for(pattern, audit_log),
            "```",
            "",
            "## What this change can and cannot be",
            "",
            f"- It touches `{TARGET}` only — not the charter, not the code, not the "
            "portfolio or the theses.",
            "- It only **adds** text. The insertion-only rule is enforced in `amend.py`, "
            "not requested in a prompt: removing a constraint is the one edit that could "
            "make the system less safe, and it is exactly the edit an AI under audit has "
            "an interest in making.",
            "- Turns the rule into something mechanically checkable: " + checkable,
            "",
            f"Proposed {now_stamp()} by `amend.py` using {model}.",
        ])
        if open_pull_request(branch, title, body):
            opened += 1
            counts[pattern]["proposed_at"] = now_stamp()
        else:
            abandon_branch(branch)

    if not dry_run and opened:
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(counts, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    print(f"{opened} amendment proposal(s) opened")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Propose an instruction amendment for a recurring audit pattern")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--state-dir", default=os.path.join(BASE, "state"))
    args = parser.parse_args()
    return propose(args.state_dir, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
