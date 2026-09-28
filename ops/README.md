# Independent heartbeat and bounded recovery

`watchdog.py` runs outside GitHub Actions once daily at 23:00 UTC (02:00 Europe/Istanbul) using a systemd user timer.
This follows the closing-review deadline; there is no extra startup trigger.
It reads the authenticated GitHub CLI's Actions API and observes main-branch scheduled
and manually dispatched runs. It does not read or edit investment records.

- Intraday: NYSE sessions only, ninety-minute startup/staleness grace. Holidays are excluded. The scheduled
  close review has its own deadline after 21:15 UTC. Calendar-only skipped runs do not count.
- Weekly: Saturday at 06:00 UTC plus two-hour grace, even after a Friday holiday;
  automatic catch-up ends on Sunday. The executor uses the week's last actual session.
- A queued/running job blocks dispatch; a stuck job is alerted, not cancelled.
- Missing jobs can be dispatched. Failed jobs can be retried only when failure is
  confined to dependency bootstrap, before any successful decision/execution/commit step.
- Maximum two attempts per incident, two-hour cooldown, four repairs per UTC day.
  Intent is persisted before API calls. A file lock prevents concurrent local repairs.
- Data/schema/evidence rejection, execution, push and Telegram failures require inspection;
  they never trigger replay of investment decisions. No self-modifying code is allowed.
- Telegram distinguishes a repair request from a subsequently observed successful run.
  Alerts repeat at most every twelve hours while an incident remains unresolved.
- The existing `workflow_run` Telegram alarm continues to report failed Actions.

Install from a tested commit using the project venv (install `ops/requirements.txt` for the installer):

```
python ops/install_watchdog.py --env-file /absolute/path/to/private/.env
systemctl --user status ai-portfolio-watchdog.timer ai-portfolio-watchdog.service
journalctl --user -u ai-portfolio-watchdog.service
```

The installer copies only the four required scripts to a separate local runtime, records
the source commit, and writes only Telegram credentials to a private 0600 environment
file. GitHub authentication remains in the user's existing `gh` configuration. Reinstall
after reviewed code updates; the runtime never pulls arbitrary changes itself.

Read-only check: `python watchdog.py`. Stop: `systemctl --user disable --now
ai-portfolio-watchdog.timer`. This machine must be awake, online and running the user
service manager. `Persistent=true` checks on return; it cannot monitor while the machine
is off. For uninterrupted external monitoring deploy this timer on an always-on host
with its own credentials. This is independent of GitHub scheduling, not an uptime guarantee.


When Telegram credentials exist only in GitHub Secrets, install with
`python ops/install_watchdog.py --github-alerts`. The timer and detection remain local;
notifications dispatch the existing Telegram workflow, which uses its existing secrets.
No secret is exported. A dispatch acknowledgment is not Telegram delivery confirmation;
check the notification workflow result. This mode cannot deliver an alert during a
complete GitHub API/runner outage. Switch to direct delivery with `--env-file` when the
same bot's local token and target chat IDs are available.
