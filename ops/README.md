# Daily cloud watchdog

The production watchdog runs in `.github/workflows/watchdog.yml` on GitHub Actions,
once daily at 23:00 UTC (02:00 Europe/Istanbul). The owner's computer is not required.
A delayed run evaluates the last daily deadline. GitHub schedules are best effort,
so 02:00 is the planned trigger time, not a delivery-time guarantee.

Telegram is sent directly from the watchdog runner using existing repository secrets.
The failure-alert workflow also monitors the watchdog's own failures. No local chat
credentials or secret export are required. A complete GitHub scheduler/runner outage
can stop both detection and notification; this is not independent external monitoring.

State lives in `watchdog.json` on the dedicated `watchdog-state` branch. Repair intent
is checkpointed before dispatch; each write uses the previous file SHA as a precondition.
Missing/corrupt/unwritable state fails closed instead of resetting repair limits.
Workflow concurrency serializes runs. Portfolio files and the main branch are not used
for monitoring-state persistence. Migration begins at the recorded deployment time;
missing jobs before deployment are not treated as new incidents.

- Intraday: NYSE sessions and holidays, plus a separate closing-review deadline.
- Weekly: Saturday remains active, including Friday holidays; catch-up ends Sunday.
- A green calendar-only skip is not a successful measurement heartbeat.
- Missing jobs can be dispatched. Only dependency bootstrap failures before a successful
  decision/execution/commit can be rerun. Running jobs block new dispatches.
- At most two repairs per incident, two-hour cooldown, four per UTC day. Under the daily
  schedule, a subsequent observation/repair normally occurs on the next daily check.
- Data/schema/evidence, execution and commit failures are alerted without replaying trades.
- Telegram distinguishes a repair request from an observed successful recovery.

Manual verification:

```
gh workflow run watchdog.yml --ref main -f test_notification=true
gh run list --workflow watchdog.yml
```

The optional test sends a clearly labelled Telegram delivery message. It does not force
an investment round. The normal monitor still runs and may repair an eligible real incident.

The former local `ai-portfolio-watchdog.timer` is disabled after cloud migration to avoid
duplicate checks. `install_watchdog.py` remains available for an explicitly requested
future independent host: install `ops/requirements.txt`, then use `--env-file` for direct
Telegram or `--github-alerts` for notification dispatch. Do not enable both monitoring
installations concurrently with separate state.

References: [GitHub scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
and [conditional content updates](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents).
