# Failed local attempt reconciliation

A failed attempt is not a successful portfolio assessment. Never blindly
release `active.json`, replay the old run, overwrite its receipt/archive, or
reinterpret a skipped core step as recovery. Unknown failures require the operator
procedure below; only the narrowly verified no-trade partial case is automatic.

## Completed no-trade partial assessments

The intraday finalizer receives **every step's** outcome and conclusion via
`toJSON(steps)`, including the runner's synthetic pre-job hook. Runner 2.337.0
creates its context from a random GUID (`JobExtension.cs`, pre-job CreateChild),
and `JobHookProvider.cs` processes its `GITHUB_OUTPUT` file commands. The installed
start guard durably records a per-attempt random `hook_claim` before emitting
`local_runner_claim` through that file. Finalization accepts exactly one extra
successful GUID-context step with exactly that output and journal binding; GUID
shape alone, empty outputs, duplicate bindings and all other extras are rejected.
The original complete step context is retained in partial evidence. This is an
identity binding within the trusted runner/workflow boundary, not a sandbox
against malicious code running as the same OS user. Legacy receipts without a
binding are never retroactively upgraded; this incident needs operator audit.

The workflow's explicit step set remains closed. The installed guard may release a new run's claim
when the only failures are the explicit news/reassessment health gates, all
persistence/evidence steps succeeded, and all other steps succeeded or were skipped.
It refuses continued-on-error, cancellation, unknown/missing step identities,
corporate changes, weekly execution, any trades, pending decisions/transactions or
pending weekly plans. It also checks that the working tree is clean, portfolio bytes
have not changed from the journal-bound actual checkout SHA (not the queued event SHA),
and a fresh read of remote main matches
the exact local HEAD. Missing/ambiguous evidence or failed readback keeps the lock.

The archive and **failure** receipt (with `release_reason=persisted-no-trade-partial`
and exact step/readback evidence) are fsynced before releasing the active claim.
The workflow stays red, incomplete source coverage stays partial, and the receipt
still bans every replay attempt of the original run. Only a **new scheduled run ID**
may collect fresh evidence. A crash during finalization still requires manual review.
This path does not process old receipts or automatically reconcile financial changes.

Cached analyst quarantine remains incomplete on every assessment, even after the
first daily alert. Failed news cursors are not advanced and source standards are
unchanged. Partial checks are persisted even when no investment threshold changed;
otherwise the no-change commit optimization could discard the current blocker.
Public provider failures can persist: this is graceful fail-closed operation, not a
guarantee of complete market data or a promise that the strategy will trade.

## Deployment order for the checkout-baseline contract

Repository merge alone does not update the installed guard. Wait for the current
worker to finish; verify idle, stop the listener and hold its listener flock.
Back up journal, guard and hook. Merge only the independently reviewed exact-head
CI-green change, then install `ops/local_runner_guard.py` from that merged SHA
outside the checkout, verifying identical SHA256 bytes before restarting. Do not
let the new workflow call `checkout` against an older installed guard. Existing
failed claims still require the exact operator audit below; this release never
reclassifies or retries them. Exercise the installed lifecycle only with a NEW
explicit offline smoke and verify inference is skipped, archive/receipt persisted,
active claim absent. Synthetic git/journal regression tests establish the partial
release contract; they are not financial-data recovery evidence.

## Investigate before release

1. Save exact run + attempt jobs, full logs, artifact metadata and downloaded
   evidence. Compare archive members to the commit actually pushed, not merely
   the workflow's starting SHA. Compare portfolio, decision log, decision history,
   pending decisions/weekly plans and notification HTTP results. Resolve every
   trade/commit/delivery ambiguity before proceeding.
2. Keep genuine provider/coverage errors recorded as failures. Releasing a fully
   accounted-for attempt permits only a **new run ID**; it does not correct bad
   provider evidence or certify assessment recovery.
3. Make a private backup of the entire journal, installed guard and hook. Preserve
   evidence outside the checkout (checkout removes ignored output files).
4. Verify the runner is idle locally and through GitHub's runner `busy` field;
   stop its user service, verify no worker remains, and hold its `listener.lock`
   with `flock -n` throughout installation/reconciliation. Do not stop a worker
   mid-job. Keep one writer. The reconcile CLI is operator-only and cannot infer
   whether external side effects are safe from hashes alone.
5. Prepare an `expected.json` containing the exact original active JSON object.
   Prepare private `audit.json` with:
   - `resolution`: `persisted-no-replay`
   - `reason`: specific evidence-backed explanation (not a success claim)
   - `receipt_sha256` and `archive_sha256`: hashes of original bytes
   - `evidence`: nonempty list of `{path, sha256}` for private investigation files
   - `checks`: nonempty explanations for `commit`, `trades`, `pending`,
     `notifications`; these are reviewed operator attestations, not automatic
     external verification.
6. Install only independently reviewed, CI-green merged code, then execute:

   ```sh
   python local_runner_guard.py reconcile --state /absolute/journal \
     --expected /private/expected.json --audit /private/audit.json
   ```

   It requires exact active/receipt identity, a finished failure/cancellation,
   matching original/evidence digests, and no pre-existing reconciliation. It
   durably writes `<run>-reconciliation.json` **before** unlinking active. The
   original receipt and archive remain byte-identical and block every attempt
   number of that historical run. If an audit already exists after a crash,
   stop for manual review; do not overwrite it or retry blindly.
7. Read back all state and installed code hashes; test replay rejection only
   against a **copy** of the journal. Release maintenance flock, restart service,
   verify idle/online. Optional fresh `Local Hermes Smoke` dispatch with explicit
   `offline_only=true` runs offline tests, no inference/trades/delivery. Verify
   its exact SHA/attempt/core steps and released claim. A green smoke is runner
   lifecycle evidence, **not** a recovered financial assessment.

## Rejected setup behavior

The pre-job hook remains fail-closed. Workflow artifact/provider consumers require
successful checkout so a rejected setup cannot upload the prior pinned workspace
under a new run. Cleanup runs only after checkout was attempted. The guard also
makes failure/cancelled cleanup a no-op for a never-claimed run; it still rejects
success, existing receipts, and wrong exact owner identities. No failed job is
converted into a successful job. Failed/cancelled/unknown checkout snapshots use
`<run>-unverified-workspace.tar.gz` and explicit receipt provenance; they are not
current-attempt outputs. A success release requires successful checkout. Terminal
receipts or existing archives cannot be finalized again, including interrupted
finalization with divergent active/receipt records. Successful claim removal is
directory-fsynced before returning.
