import sqlite3
import os

# Check all database files
db_files = [
    '/Users/marvens/Desktop/Karchain/backend/app.db',
    '/Users/marvens/Desktop/Karchain/backend/database.db', 
    '/Users/marvens/Desktop/Karchain/backend/karchain.db',
    '/Users/marvens/Desktop/Karchain/karchain.db'
]

for db_path in db_files:
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if games table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='games'")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Found games table in: {db_path}")
                
                # Check the game
                cursor.execute("SELECT id, home_team_id, away_team_id, game_date FROM games WHERE id = 35")
                game = cursor.fetchone()
                
                if game:
                    print(f"Game 35: Home={game[1]}, Away={game[2]}, Date={game[3]}")
                else:
                    print("Game 35 not found")
                    
                # Show all games
                cursor.execute("SELECT id, home_team_id, away_team_id, game_date FROM games ORDER BY game_date LIMIT 10")
                games = cursor.fetchall()
                print("Recent games:")
                for g in games:
                    print(f"  Game {g[0]}: {g[1]} vs {g[2]} on {g[3]}")
                    
            conn.close()
        except Exception as e:
            print(f"❌ Error with {db_path}: {e}")
    else:
        print(f"❌ File not found: {db_path}")