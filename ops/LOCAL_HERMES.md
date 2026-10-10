# Local Hermes execution

## Ownership and inference

GitHub remains the **scheduler and artifact store**, not the inference host. Weekly
and intraday jobs require repository variable `PORTFOLIO_EXECUTOR=local-hermes`
and the dedicated `portfolio-hermes` runner label. There is no hosted/paid fallback.
The existing UTC schedules and shared `portfolio-round` concurrency are retained.
The watchdog remains hosted, checking Actions runs and requesting bounded retries;
it cannot bypass the local runner's unresolved-attempt journal.

Every inference call launches Hermes with `--safe-mode --provider openai-codex
--model gpt-6-astra --toolsets none --max-turns 1 --source tool`. It uses the existing
local subscription connection; no OAuth tokens are copied to GitHub or this repo.
Safe mode ignores configured provider fallback, plugins, MCP, memory and project
rules. Each invocation has a new context. Requests below 100,000 UTF-8 prompt bytes
have a 180-second run budget and a 195-second parent timeout; larger research
requests have a 600-second run budget and a 615-second parent timeout. This retains
the complete research evidence without repeatedly cutting off the weekly decision.
Provider/CLI errors stop rather than invoking a paid provider.
Existing semantic correction loops remain bounded at their existing limits.
JSON is parsed strictly; supplied JSON Schema is validated locally, NOT claimed to
be provider-enforced structured decoding. Existing citation, number, semantic,
market-session, freshness and paper-trade arithmetic gates are unchanged.

Auditors now use independent contexts of the **same model**, not different model
families. This loses provider/model diversity and retains correlated blind spots.
Historical audit records describe the models used at their historical run times.
All trading remains simulated accounting: no broker credentials or order APIs.

## Local installation contract

- Managed runtime: `~/.local/share/ai-portfolio-runner/`
- Actions checkout: `actions/_work/ai-portfolio-experiment/ai-portfolio-experiment`
  beneath that runtime; never the user's dirty development checkout.
- Python 3.12 virtualenv: `venv/`; install the full `requirements-dev.txt`
  (includes production dependencies, pytest and PyYAML) before any smoke dispatch:
  `uv pip install --python ~/.local/share/ai-portfolio-runner/venv/bin/python -r requirements-dev.txt`.
  Verify `venv/bin/python -c 'import pytest, yaml'` in the managed runtime.
  The smoke intentionally does not install packages or invoke inference by default.
- Existing `hermes` and `uv` executables must be on the service PATH.
- Install `ops/local_runner_guard.py` OUTSIDE the Actions checkout as
  `~/.local/share/ai-portfolio-runner/local_runner_guard.py`.
- Register a repository runner with **no default labels**, only `portfolio-hermes`.
- Set `ACTIONS_RUNNER_HOOK_JOB_STARTED` to a fixed executable shell script that
  runs the installed guard's `start` command. It only accepts schedule/manual
  main-branch jobs in this repo with an approved workflow name.
- Run the listener under a systemd user service and `flock` held for its entire
  lifetime. Exactly one listener is allowed. Do not run a second copy manually.
- Persistent private receipts and exact root JSON/Markdown, `state/`, `output/`
  snapshots: `~/.local/state/ai-portfolio-runner/`. Unresolved failure retains
  `active.json`; later jobs are refused, including watchdog retry requests.
  Only the guard's narrowly verified persisted source-gap cases release the claim
  automatically; the failed receipt and exact archive remain intact.
- A success receipt prevents re-executing the same GitHub run ID. This is not a
  global business-event deduper; existing domain execution/recovery gates remain.

This public repo's runner executes trusted main-branch code as the local user.
A pre-job guard is NOT a sandbox against malicious main-branch code. Do not merge
untrusted workflows/code. PR test workflows remain GitHub-hosted. No runner label
may be used for pull-request jobs. The service does not expose an HTTP proxy.

## Safe cutover / rollback

1. Run offline tests and real `python smoke_llm.py` (no market/portfolio writes).
2. Register/install the runner; leave production ownership variable unset.
3. Pause `weekly.yml`, `detector.yml` and `watchdog.yml`; drain/cancel old queued or
   running jobs and verify none remain. Old hosted jobs do not share local locks.
4. Merge reviewed migration, verify main SHA, start the single guarded listener.
5. For initial inference cutover, dispatch `local-hermes-smoke.yml` on main with
   explicit `offline_only=false`. Require actual runner success,
   structured subscription response, populated data/notification secret names,
   and persisted success receipt before enabling production ownership.
   For incident lifecycle checks use `offline_only=true` instead; inference is
   skipped and a successful smoke is not evidence of financial assessment recovery.
6. Set `PORTFOLIO_EXECUTOR=local-hermes`, re-enable the three schedules, and read
   back runner, variable and workflow states. Do not trigger a portfolio run merely
   to prove installation. Normal future runs retain all validation and notifications.

When this computer/session is unavailable, inference cannot execute. GitHub may
queue a scheduled run while the runner is offline; its normal exchange/session and
weekly-window checks still apply when it resumes. There is no always-on guarantee.
A user service starts with the user session; do not assume boot-time availability
unless user lingering has explicitly been configured.

To stop: unset/change `PORTFOLIO_EXECUTOR`, disable weekly/detector/watchdog, drain
jobs, and stop the user service. Never re-enable old paid workflows as an automatic
rollback. Retain private receipts and artifacts for reconciliation.

## Failure reconciliation

Do not delete `active.json` just to turn the dashboard green. Inspect the exact
Actions run, archived outputs, local checkout and remote persisted commits first.
Determine which paper accounting/notifications already happened. Only the operator
may archive the unresolved claim with a written reconciliation and authorize a NEW
run; same-run replay remains blocked by its durable receipt. If the process died
before the final preservation step, preserve the existing checkout before any new
checkout. Missing successful finalization is a blocker, never implicit success.

## Verification

`python -m pytest -q` is offline (live inference forbidden in fixtures).
`python smoke_llm.py` makes exactly one real subscription request.
`python ops/local_runner_guard.py plan` needs no secrets and touches no portfolio.
Runner tests include real simultaneous subprocess claims and private artifact
readback. Tests do not place broker orders or invoke paid OpenRouter inference.

## Recovery behavior

Invalid JSON/schema output and parent timeouts retry the same subscription at most
three times through the existing assessment loop. Protocol violations, tool activity,
wrong models and process failures stop immediately. No paid fallback is enabled.
Auditors receive an explicit JSON schema and a clean/findings consistency check.
Auditors select code-owned source-span IDs; code attaches the original quotations,
so literal source quotes cannot corrupt the model's JSON. Scout choices use the
measured discovery universe, unique-symbol/schema checks and bounded corrections.
The weekly valuation is committed before inference, so a failed review cannot hide
an otherwise valid measured valuation. Completed audits are checkpointed before
dependent research. Missing news bodies are fetched with bounded
article extraction; unavailable text and contradictory analyst records remain gaps,
never fabricated evidence or silently successful assessments.
The pending-note queue is supplied in full rather than losing older unanswered notes
to a history-tail limit. Section F must explicitly adopt, reject or defer each note;
an honest unresolved-data explanation is an answer, not a claim the gap is resolved.
Only section F may reproduce exact valid ISO timestamps found in those supplied
accountability records. These identify old notes/audit entries; all other raw dates
and financial figures still require ledger references. The independent reviewer sees
the prior records as accountability context, not proof of current business facts.

For a weekly run whose only failure is analyst-source completeness, the installed
guard may release the next NEW run after proving that the pending research plan,
input checksum, notifications and evidence were persisted remotely. It also requires
unchanged portfolio accounting, live theses and decision log, no executable pending
transaction, and a clean checkout. Model, execution, push and notification failures
remain blockers. This release is not workflow success or permission to replay an
old run; the next session must collect fresh evidence and reconsider the plan.
