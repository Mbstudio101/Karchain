
import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import PlayerProps, Player
from datetime import datetime, timedelta

db = SessionLocal()

today = datetime.utcnow().date()
tomorrow = today + timedelta(days=1)

def check_luka_after_fix():
    print("Checking Luka props after fix...")
    
    # Get all Luka props
    luka_props = db.query(PlayerProps).join(Player).filter(
        Player.name.ilike("%luka%"),
        PlayerProps.timestamp >= today,
        PlayerProps.timestamp < tomorrow
    ).all()
    
    print(f"Found {len(luka_props)} props for Luka today:")
    
    for prop in luka_props:
        print(f"  Prop ID {prop.id}: '{prop.player.name}' (Player ID: {prop.player_id}) - {prop.prop_type}: {prop.line}")
        print(f"  Historical stats: {len(prop.player.stats)} games")

if __name__ == "__main__":
    check_luka_after_fix()
    db.close()