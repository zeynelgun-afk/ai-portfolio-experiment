#!/usr/bin/env python3
"""Install the independent user timer from a verified checkout; never prints secrets."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from dotenv import dotenv_values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--github-alerts', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    home = Path.home()
    target = home/'.local/share/ai-portfolio-watchdog'
    state = home/'.local/state/ai-portfolio'
    config = home/'.config/ai-portfolio'
    units = home/'.config/systemd/user'
    for path in (target,state,config,units):
        path.mkdir(parents=True,exist_ok=True)
    os.chmod(config,0o700)
    environment_line = ''
    if not args.github_alerts:
        if not args.env_file:
            raise RuntimeError('--env-file is required for direct Telegram delivery')
        credentials = dotenv_values(args.env_file)
        keys = ('TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID','TELEGRAM_CHAT_ID_DM')
        if not credentials.get(keys[0]) or not any(credentials.get(k) for k in keys[1:]):
            raise RuntimeError('Telegram configuration missing')
        secret_path = config/'watchdog.env'
        fd = os.open(secret_path, os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        os.chmod(secret_path,0o600)
        with os.fdopen(fd,'w') as handle:
            for key in keys:
                value = credentials.get(key) or ''
                if '\n' in value or '\r' in value:
                    raise ValueError('Invalid multiline credential')
                handle.write(key+'='+json.dumps(value)+'\n')
        environment_line = 'EnvironmentFile=' + str(secret_path)
    for file in ('watchdog.py','market_time.py','execute_trade.py','notify_failure.py'):
        shutil.copy2(source/file,target/file)
    sha = subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    (target/'SOURCE_COMMIT').write_text(sha+'\n')
    service = f'''[Unit]
Description=AI portfolio independent heartbeat and bounded recovery
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory={target}
{environment_line}
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart={sys.executable} {target}/watchdog.py --apply --state {state}/watchdog.json {"--github-alerts" if args.github_alerts else ""}
TimeoutStartSec=240
NoNewPrivileges=yes
UMask=0077
'''
    timer = '''[Unit]
Description=Check AI portfolio schedules independently of GitHub Actions

[Timer]
OnCalendar=*-*-* 23:00:00 UTC
Persistent=true
RandomizedDelaySec=30
Unit=ai-portfolio-watchdog.service

[Install]
WantedBy=timers.target
'''
    (units/'ai-portfolio-watchdog.service').write_text(service)
    (units/'ai-portfolio-watchdog.timer').write_text(timer)
    subprocess.run(['systemctl','--user','daemon-reload'],check=True)
    subprocess.run(['systemctl','--user','enable','--now','ai-portfolio-watchdog.timer'],check=True)
    subprocess.run(['systemctl','--user','start','ai-portfolio-watchdog.service'],check=True)
    print('Independent watchdog timer installed; secrets were not logged.')


if __name__=='__main__':main()
