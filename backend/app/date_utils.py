from datetime import datetime, timedelta, date, timezone


def get_current_gameday() -> date:
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
    # US Eastern is UTC-5 (ignoring DST for simplicity; EDT is UTC-4)
    # For a more robust solution use pytz, but this covers NBA season well
    utc_now = datetime.now(timezone.utc)
    eastern_offset = timedelta(hours=-5)
    eastern_now = utc_now + eastern_offset

    if eastern_now.hour < 5:
        return (eastern_now - timedelta(days=1)).date()
    return eastern_now.date()


def get_gameday_range(target_date: date) -> tuple:
    """
    Returns (start_datetime_utc, end_datetime_utc) for a gameday.

    NBA games on a given date (e.g. Feb 10) are stored in UTC,
    which means a 7:30 PM ET game on Feb 10 = 00:30 UTC Feb 11.

    So for gameday Feb 10, we need to search:
      from Feb 10 10:00 UTC  (5 AM ET — earliest possible game day start)
      to   Feb 11 10:00 UTC  (5 AM ET next day — captures all late games)

    This 24-hour window in UTC captures ALL games for the Eastern-time gameday.
    """
    # 5 AM ET = 10 AM UTC (EST, UTC-5)
    start_utc = datetime(target_date.year, target_date.month, target_date.day, 10, 0, 0)
    end_utc = start_utc + timedelta(hours=24)
    return start_utc, end_utc
