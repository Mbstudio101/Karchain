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
    
    # Check if games were created
    import sqlite3
    conn = sqlite3.connect('/Users/marvens/Desktop/Karchain/karchain.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM games")
    games_count = cursor.fetchone()[0]
    print(f"📊 Games in database after sync: {games_count}")
    
    if games_count > 0:
        cursor.execute("SELECT id, home_team_id, away_team_id, game_date, status FROM games ORDER BY id")
        games = cursor.fetchall()
        print("\n🎯 Games in database:")
        for game in games:
            print(f"Game {game[0]}: Home={game[1]}, Away={game[2]}, Date={game[3]}, Status={game[4]}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ ESPN sync failed: {e}")
    import traceback
    traceback.print_exc()