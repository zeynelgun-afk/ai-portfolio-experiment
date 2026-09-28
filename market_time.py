"""US equity sessions and timestamp checks shared by measurement and execution."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo
import os

import pandas_market_calendars as calendars


@lru_cache(maxsize=32)
def session(day):
    schedule = calendars.get_calendar("NYSE").schedule(start_date=day, end_date=day)
    if schedule.empty:
        return None
    row = schedule.iloc[0]
    return row["market_open"].to_pydatetime(), row["market_close"].to_pydatetime()


def market_open(moment=None):
    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        return False
    bounds = session(moment.astimezone(ZoneInfo("America/New_York")).date())
    return bool(bounds and bounds[0] <= moment < bounds[1])


def recent(stamp, moment, seconds=1800):
    try:
        parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        return parsed.tzinfo is not None and 0 <= (moment - parsed).total_seconds() <= seconds
    except (ValueError, TypeError):
        return False


def should_run(moment, full_review=False):
    bounds = session(moment.astimezone(ZoneInfo("America/New_York")).date())
    return bool(bounds and (market_open(moment) or (full_review and moment >= bounds[1])))


def weekly_slot(moment):
    saturday = (moment - timedelta(days=(moment.weekday() - 5) % 7)).replace(hour=6, minute=0, second=0, microsecond=0)
    if moment < saturday:
        saturday -= timedelta(days=7)
    return saturday



if __name__ == "__main__":
    allowed = should_run(datetime.now(timezone.utc), os.environ.get("FULL_REVIEW") == "true")
    print("Session calendar: " + ("run allowed" if allowed else "closed — skipping data, AI and trades"))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"run={'true' if allowed else 'false'}\n")
