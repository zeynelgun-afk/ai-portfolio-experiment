# Failed local attempt reconciliation

A failed attempt is not a successful portfolio assessment. Never automatically
release `active.json`, replay the old run, overwrite its receipt/archive, or
reinterpret a skipped core step as recovery.

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
