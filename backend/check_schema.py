import sqlite3

# Connect to the database
conn = sqlite3.connect('/Users/marvens/Desktop/Karchain/karchain.db')
cursor = conn.cursor()

# Check the games table schema
cursor.execute("PRAGMA table_info(games)")
columns = cursor.fetchall()

print("📊 Games table schema:")
for col in columns:
    print(f"  {col[1]}: {col[2]}")

# Check if game 35 exists
cursor.execute("SELECT * FROM games WHERE id = 35")
game = cursor.fetchone()

if game:
    print(f"\n🎯 Game 35 found:")
    for i, col in enumerate(columns):
        print(f"  {col[1]}: {game[i]}")
else:
    print("\n❌ Game 35 not found")
    
    # Check what games we have
    cursor.execute("SELECT id FROM games ORDER BY id")
    game_ids = cursor.fetchall()
    print(f"Available game IDs: {[g[0] for g in game_ids]}")

conn.close()