import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import date, datetime
from app.date_utils import get_gameday_range

db = SessionLocal()
try:
    today = date.today()
    start_utc, end_utc = get_gameday_range(today)
    
    print(f"Date range: {start_utc} to {end_utc}")
    
    # Check the exact query from enhanced_genius_picks
    props = db.query(models.PlayerProps).join(models.Game).filter(
        models.Game.game_date >= start_utc,
        models.Game.game_date < end_utc
    ).all()
    
    print(f"Props found with Game join: {len(props)}")
    
    # Check if props have game_id but games might not exist
    all_props = db.query(models.PlayerProps).filter(
        models.PlayerProps.timestamp >= start_utc,
        models.PlayerProps.timestamp < end_utc
    ).all()
    
    print(f"Props found with timestamp filter: {len(all_props)}")
    
    # Check LeBron specifically
    lebron = db.query(models.Player).filter(models.Player.name.ilike("%lebron%")).first()
    if lebron:
        lebron_props_timestamp = db.query(models.PlayerProps).filter(
            models.PlayerProps.player_id == lebron.id,
            models.PlayerProps.timestamp >= start_utc,
            models.PlayerProps.timestamp < end_utc
        ).all()
        
        print(f"LeBron props with timestamp: {len(lebron_props_timestamp)}")
        
        lebron_props_game = db.query(models.PlayerProps).join(models.Game).filter(
            models.PlayerProps.player_id == lebron.id,
            models.Game.game_date >= start_utc,
            models.Game.game_date < end_utc
        ).all()
        
        print(f"LeBron props with Game join: {len(lebron_props_game)}")
        
        # Check if the issue is with the game_date vs timestamp mismatch
        if lebron_props_timestamp:
            for prop in lebron_props_timestamp[:2]:
                print(f"\nProp ID {prop.id}:")
                print(f"  Timestamp: {prop.timestamp}")
                print(f"  Game ID: {prop.game_id}")
                if prop.game_id:
                    game = db.query(models.Game).filter(models.Game.id == prop.game_id).first()
                    if game:
                        print(f"  Game date: {game.game_date}")
                        print(f"  In range? {start_utc <= game.game_date < end_utc}")
                    else:
                        print(f"  Game not found!")
    
finally:
    db.close()