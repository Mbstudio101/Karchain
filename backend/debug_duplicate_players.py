
import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import Player, PlayerStats
from sqlalchemy import func

db = SessionLocal()

def check_duplicate_players(name_pattern):
    print(f"\nChecking for players matching '{name_pattern}'...")
    players = db.query(Player).filter(Player.name.ilike(f"%{name_pattern}%")).all()
    
    print(f"Found {len(players)} players:")
    for p in players:
        stats_count = db.query(PlayerStats).filter(PlayerStats.player_id == p.id).count()
        print(f"  ID: {p.id}, Name: '{p.name}', Team ID: {p.team_id}, Stats count: {stats_count}")

try:
    check_duplicate_players("Luka")
    check_duplicate_players("LeBron")
    check_duplicate_players("Davis") # Anthony Davis
    
finally:
    db.close()