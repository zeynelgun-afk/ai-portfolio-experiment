# Watchdog historical incidents

An unresolved incident retains its original `since` and repair counters. Current schedule deadlines are evaluated separately (`current_status`); a new deadline does not erase the historical failure. `verification: pending_production` means normal production has not yet verified recovery, not that an automatic replay is warranted.

Recovery requires a later completed main-branch schedule/workflow_dispatch run with overall success and the required successful core step (`1) Detector` or `3b) Structured decision`). Calendar-only skips and other workflows' smoke checks do not qualify. The newest actual failure outranks an older success. Once observed, `last_failure` retains the identity even if a subsequent list omits it. Active production is reported as running/waiting or stuck after two hours, and does not resolve a failure.

Each observation includes a SHA-256 `observation_id`, run ID/attempt, historical anchor, exact current deadline, current status, repair eligibility and its reason. Alerts deduplicate the same observation, rather than repeat every 12 hours. A changed failure run/attempt, running-to-stuck transition, eligibility/cooldown/limit transition, current status, new session/deadline phase, or verified recovery can alert. The intraday sliding deadline is grouped by UTC session date and intraday/close phase so five-minute checks do not create fresh alerts merely by moving the 90-minute lookback. Delivery failures do not checkpoint successful delivery and retry next time. Existing legacy `alerted` timestamps do not establish observation delivery; the first upgraded check can alert once.

Reason codes distinguish `outside_due_window`, `historical_rerun_disabled`, `unsafe_failure`, `production_running`, `production_stuck`, `repair_cooldown`, `incident_attempt_limit`, `daily_attempt_limit`, and `repair_eligible`. An incident with zero attempts is not described as having exhausted retries. Existing dependency-only rerun rules, local-Hermes historical rerun prohibition, cooldown and repair caps remain in force.

## Explicit operator acknowledgement

Acknowledgement changes only the exact observation's alert handling. It does not set `resolved`, clear attempts, grant repair authorization, or suppress a future observation. The helper `acknowledge(state, workflow, observation_id, evidence, operator, now)` validates an unresolved failed/stuck run and exact current observation identity. Evidence must identify the run **and attempt**, followed by a semicolon and concrete review evidence/findings. This validates specificity, not the truth of the human review.

The CLI provides a local-state-only acknowledgement path under the usual file lock. All four fields and an explicit state path are mandatory. It refuses `--apply` and `--remote-state`, runs no monitoring/API requests and sends no notification:

```bash
python watchdog.py --state /explicit/path/watchdog.json \
  --ack-workflow detector.yml \
  --ack-observation EXACT_OBSERVATION_SHA256 \
  --ack-evidence 'run:37082469299:attempt:1; /evidence/detector.log, reviewed failed partial-assessment step; awaiting normal production verification' \
  --ack-operator 'operator-name'
```

An exact GitHub attempt URL is also accepted as the first evidence token, e.g. `https://github.com/OWNER/REPO/actions/runs/37082469299/attempts/1; reviewed log ...`. A workflow-wide acknowledgement or an unrelated number in prose is rejected. Obtain the observation ID from a saved monitor observation/state; ordinary read-only monitoring does not persist state. Operators must arrange the authorized state checkpoint separately. Remote-state adoption is an operator/deployment responsibility; this command never writes GitHub state.

## Verification limits

The watchdog examines the latest 100 workflow runs and the jobs response as before. Persisted `last_failure` protects already observed identities against later omission, but an unseen failure outside the returned history cannot be inferred. GitHub-based Telegram dispatch confirms the notification request, not final Telegram delivery; existing notification-workflow failure reporting still applies. No local test proves production recovery or provider coverage.

Attempt ordering uses `run_started_at` (falling back to `created_at` for legacy records), never postprocessing `updated_at`. The failure watermark cannot regress and is captured even while a later run is active. A historical success cannot hide a missing current deadline. Verified recovery stores the exact successful run ID, attempt, SHA and verification time in `recovery`, and links that attempt in its message.

## Incident diagnosis and retained blockers

The investigated failures are detector [37082469299](https://github.com/zeynelgun-afk/ai-portfolio-experiment/actions/runs/37082469299) and weekly [37146723318](https://github.com/zeynelgun-afk/ai-portfolio-experiment/actions/runs/37146723318). Detector 37145865340 was green only because its core step was skipped; it is not recovery.

Current-code reproductions also found digit-check false positives for the known publisher alias `247 Wall St` and the parameter label `20-day average`. The latter is allowed only alongside a supplied volume-average reference; raw measured values and unknown references remain rejected. Proposers and semantic reviewers now share the bounded article selection/excerpts, with candidate source IDs required to exist in the review bundle. This fixes evidence omission, not an uncertain reviewer's verdict.

A read-only FMP check on 2026-10-05 still found incomplete target history for AMD, ANET, AVAV, FANG, NVDA and PPL, plus no target records for ATOM; all seven had available annual estimates. Firm/target inconsistencies and AVAV's same-day Goldman Sachs conflict remain quarantined. Missing/contradictory target data is **not** normalized to healthy, and annual estimates do not substitute for target-revision history. A provider correction or independently sourced reconciliation is needed. No current portfolio production run was manufactured to clear the incident.

Legacy deferral counting also lacks candidate-specific historical membership: it assumes participation in every parsed round. The rejected weekly draft is absent from its saved artifact, so the exact historical failing symbol cannot be reconstructed. Do not reset counters or invent past membership to unblock a proposal. Historical membership reconciliation remains separate; the documented REPORT-based threshold and financial guards are unchanged.
