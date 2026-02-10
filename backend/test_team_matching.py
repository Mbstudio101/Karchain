import sys
sys.path.append('/Users/marvens/Desktop/Karchain/backend')

from datetime import date, datetime
import sqlite3
from app.database import SessionLocal
from app.models import Game, Team
from scrapers.espn_sync import sync_espn_data

# Test the team matching logic
db = SessionLocal()

# Test team matching
def find_team(name):
    print(f"🔍 Looking for team: '{name}'")
    # Try exact match
    t = db.query(Team).filter(Team.name.ilike(name)).first()
    if t: 
        print(f"✅ Found exact match: {t.name} (ID: {t.id})")
        return t
    
    # Try prefix/suffix match (e.g. "LA Clippers" vs "Clippers")
    t = db.query(Team).filter(Team.name.ilike(f"%{name}%")).first()
    if t: 
        print(f"✅ Found partial match: {t.name} (ID: {t.id})")
        return t
    
    # Special cases for NBA naming
    special_cases = {
        "LA Clippers": "Los Angeles Clippers",
        "Clippers": "Los Angeles Clippers",
        "LA Lakers": "Los Angeles Lakers",
        "Lakers": "Los Angeles Lakers",
        "Portland": "Portland Trail Blazers",
        "Phila": "Philadelphia 76ers",
        "Sixers": "Philadelphia 76ers"
    }
    if name in special_cases:
        t = db.query(Team).filter(Team.name.ilike(special_cases[name])).first()
        if t:
            print(f"✅ Found special case match: {t.name} (ID: {t.id})")
            return t
    
    print(f"❌ No match found for: '{name}'")
    return None

# Test with the actual team names from ESPN
print("🧪 Testing team matching:")
test_names = ["LA Clippers", "Houston Rockets"]
for name in test_names:
    team = find_team(name)
    if team:
        print(f"Team '{name}' -> {team.name} (ID: {team.id})")
    else:
        print(f"Team '{name}' -> NOT FOUND")

db.close()