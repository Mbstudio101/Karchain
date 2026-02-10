import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('/Users/marvens/Desktop/Karchain/karchain.db')
cursor = conn.cursor()

# Check the Rockets vs Clippers game details
cursor.execute("""
SELECT id, home_team_id, away_team_id, game_date, status, venue 
FROM games 
WHERE id = 35
""")
game = cursor.fetchone()

if game:
    print("🎯 Rockets vs Clippers Game Details:")
    print(f"Game ID: {game[0]}")
    print(f"Home Team ID: {game[1]}")
    print(f"Away Team ID: {game[2]}")
    print(f"Game Date: {game[3]}")
    print(f"Status: {game[4]}")
    print(f"Venue: {game[5]}")

    # Get team names
    cursor.execute("SELECT name FROM teams WHERE id IN (?, ?)", (game[1], game[2]))
    teams = cursor.fetchall()
    print(f"Teams: {teams[0][0]} vs {teams[1][0]}")

    # Check what date the game is scheduled for
    game_date = datetime.fromisoformat(game[3].replace('Z', '+00:00'))
    today = datetime.now().date()
    print(f"\n📅 Game Date Analysis:")
    print(f"Game Date: {game_date.date()}")
    print(f"Today: {today}")
    print(f"Is Today: {game_date.date() == today}")
else:
    print("❌ Game ID 35 not found")
    # Let's check what games we have
    cursor.execute("SELECT COUNT(*) FROM games")
    total_games = cursor.fetchone()[0]
    print(f"Total games in database: {total_games}")
    
    if total_games > 0:
        cursor.execute("SELECT id, home_team_id, away_team_id, game_date FROM games ORDER BY id LIMIT 5")
        games = cursor.fetchall()
        print("First 5 games:")
        for g in games:
            print(f"  Game {g[0]}: Home={g[1]}, Away={g[2]}, Date={g[3]}")

conn.close()