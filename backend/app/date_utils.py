from datetime import datetime, timedelta, date, timezone
from zoneinfo import ZoneInfo
from fastapi import Request
from typing import Optional

DEFAULT_TIMEZONE = "America/New_York"
GAMEDAY_CUTOFF_HOUR = 5  # 5 AM local time


def _safe_zoneinfo(timezone_name: Optional[str]) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name or DEFAULT_TIMEZONE)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def get_client_timezone(request: Optional[Request] = None) -> str:
    if request is None:
        return DEFAULT_TIMEZONE
    tz = request.headers.get("X-Client-Timezone")
    return tz if tz else DEFAULT_TIMEZONE


def get_current_gameday(timezone_name: Optional[str] = None) -> date:
    """
    Returns the current active NBA gameday.

    NBA games in the US tip off between ~7 PM and 10:30 PM ET,
    with late West-coast games ending around 1 AM ET.

    We use US Eastern time (UTC-5) with a 5 AM ET cutoff:
    - Before 5 AM ET  → still "yesterday's" gameday (games still finishing)
    - After 5 AM ET   → today's gameday

    This ensures that at 11 PM ET you're still seeing tonight's games,
    and at 6 AM ET you flip to the new day.
    """
    tz = _safe_zoneinfo(timezone_name)
    local_now = datetime.now(timezone.utc).astimezone(tz)

    if local_now.hour < GAMEDAY_CUTOFF_HOUR:
        return (local_now - timedelta(days=1)).date()
    return local_now.date()


def get_gameday_range(target_date: date, timezone_name: Optional[str] = None) -> tuple:
    """
    Returns (start_datetime_utc, end_datetime_utc) for a gameday.

    NBA games on a given date (e.g. Feb 10) are stored in UTC,
    which means a 7:30 PM ET game on Feb 10 = 00:30 UTC Feb 11.

    So for gameday Feb 10, we need to search:
      from Feb 10 10:00 UTC  (5 AM ET — earliest possible game day start)
      to   Feb 11 10:00 UTC  (5 AM ET next day — captures all late games)

    This 24-hour window in UTC captures ALL games for the Eastern-time gameday.
    """
    tz = _safe_zoneinfo(timezone_name)
    start_local = datetime(
        target_date.year, target_date.month, target_date.day, GAMEDAY_CUTOFF_HOUR, 0, 0, tzinfo=tz
    )
    end_local = start_local + timedelta(hours=24)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


def game_datetime_to_gameday(game_dt: datetime, timezone_name: Optional[str] = None) -> date:
    """
    Convert stored UTC game datetime to user-local gameday using 5 AM cutoff.
    """
    tz = _safe_zoneinfo(timezone_name)
    if game_dt.tzinfo is None:
        game_dt = game_dt.replace(tzinfo=timezone.utc)
    local_dt = game_dt.astimezone(tz)
    shifted = local_dt - timedelta(hours=GAMEDAY_CUTOFF_HOUR)
    return shifted.date()
