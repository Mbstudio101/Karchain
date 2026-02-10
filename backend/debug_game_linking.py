import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models

db = SessionLocal()
try:
    # Get LeBron's props
    lebron = db.query(models.Player).filter(models.Player.name.ilike("%lebron%")).first()
    if lebron:
        lebron_props = db.query(models.PlayerProps).filter(
            models.PlayerProps.player_id == lebron.id
        ).order_by(models.PlayerProps.timestamp.desc()).all()
        
        print(f"LeBron has {len(lebron_props)} total props")
        
        for i, prop in enumerate(lebron_props[:5]):  # Show first 5
            print(f"\nProp {i+1} (ID: {prop.id}):")
            print(f"  Timestamp: {prop.timestamp}")
            print(f"  Game ID: {prop.game_id}")
            print(f"  Prop type: {prop.prop_type}")
            print(f"  Line: {prop.line}")
            
            if prop.game_id:
                game = db.query(models.Game).filter(models.Game.id == prop.game_id).first()
                if game:
                    print(f"  Game: {game.home_team.name} vs {game.away_team.name}")
                    print(f"  Game date: {game.game_date}")
                else:
                    print(f"  Game not found!")
            else:
                print(f"  ⚠️  NO GAME LINKED!")
        
        # Check recent props (today)
        from datetime import datetime, timedelta
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_props = db.query(models.PlayerProps).filter(
            models.PlayerProps.player_id == lebron.id,
            models.PlayerProps.timestamp >= today_start
        ).all()
        
        print(f"\nToday's props: {len(today_props)}")
        for prop in today_props:
            print(f"  Prop {prop.id}: {prop.prop_type} {prop.line} - Game ID: {prop.game_id}")
    
finally:
    db.close()