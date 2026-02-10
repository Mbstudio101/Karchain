import sqlite3

# Connect to the database
conn = sqlite3.connect('/Users/marvens/Desktop/Karchain/karchain.db')
cursor = conn.cursor()

# Check what teams are in the database
cursor.execute("SELECT id, name FROM teams ORDER BY name")
teams = cursor.fetchall()

print("🎯 Teams in database:")
for team in teams:
    print(f"  ID {team[0]}: {team[1]}")

print(f"\n📊 Total teams: {len(teams)}")

# Check if Rockets and Clippers exist
rockets = next((t for t in teams if 'Rockets' in t[1]), None)
clippers = next((t for t in teams if 'Clippers' in t[1]), None)

if rockets:
    print(f"✅ Rockets found: ID {rockets[0]}")
else:
    print("❌ Rockets not found")

if clippers:
    print(f"✅ Clippers found: ID {clippers[0]}")
else:
    print("❌ Clippers not found")

conn.close()