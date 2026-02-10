import sqlite3

# Connect to the correct database
conn = sqlite3.connect('/Users/marvens/Desktop/Karchain/karchain.db')
cursor = conn.cursor()

# Check if games are now in the database
cursor.execute("SELECT COUNT(*) FROM games")
games_count = cursor.fetchone()[0]

print(f"📊 Games in database after ESPN sync: {games_count}")

if games_count > 0:
    cursor.execute("SELECT id, home_team_id, away_team_id, game_date, venue FROM games ORDER BY id")
    games = cursor.fetchall()
    
    print("\n🎯 All games in database:")
    for game in games:
        game_id, home_id, away_id, game_date, venue = game
        print(f"Game {game_id}: Home={home_id}, Away={away_id}, Date={game_date}, Venue={venue}")

# Check if odds are saved
cursor.execute("SELECT COUNT(*) FROM betting_odds")
odds_count = cursor.fetchone()[0]
print(f"\n📊 Betting odds in database: {odds_count}")

conn.close()