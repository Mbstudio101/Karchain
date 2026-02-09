from datetime import datetime, timedelta, date

def get_current_gameday() -> date:
    """
    Returns the current active gameday (YYYY-MM-DD).
    Uses a 4 AM UTC cutoff (midnight EST) to handle late-night NBA games.
    """
    now = datetime.utcnow()
    # Before 4 AM UTC (approx midnight EST), we are still on "yesterday's" gameday
    if now.hour < 4:
        return (now - timedelta(days=1)).date()
    return now.date()
