import sqlite3

# Connect to the database
conn = sqlite3.connect('/Users/marvens/Desktop/Karchain/karchain.db')
cursor = conn.cursor()

# Check betting_odds table
cursor.execute("SELECT COUNT(*) FROM betting_odds")
odds_count = cursor.fetchone()[0]

print(f"📊 Betting odds in database: {odds_count}")

if odds_count > 0:
    cursor.execute("SELECT * FROM betting_odds LIMIT 5")
    odds = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(betting_odds)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print("\n🎯 Sample betting odds:")
    for odd in odds:
        for i, col_name in enumerate(column_names):
            print(f"  {col_name}: {odd[i]}")
        print()

# Check if there are any games at all
cursor.execute("SELECT COUNT(*) FROM games")
games_count = cursor.fetchone()[0]
print(f"\n📊 Games in database: {games_count}")

conn.close()