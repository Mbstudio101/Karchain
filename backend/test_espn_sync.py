import sys
sys.path.append('/Users/marvens/Desktop/Karchain/backend')

from datetime import date, datetime
from scrapers.espn_sync import sync_espn_data

# Sync today's games
today = date.today()
date_str = today.strftime("%Y%m%d")

print(f"🔄 Running ESPN sync for {today} ({date_str})")
try:
    result = sync_espn_data(date_str)
    print(f"✅ ESPN sync completed: {result}")
except Exception as e:
    print(f"❌ ESPN sync failed: {e}")
    import traceback
    traceback.print_exc()