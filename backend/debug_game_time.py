import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import datetime, timezone

db = SessionLocal()
try:
    # Get LeBron's game
    lebron = db.query(models.Player).filter(models.Player.name.ilike("%lebron%")).first()
    if lebron:
        lebron_props = db.query(models.PlayerProps).filter(
            models.PlayerProps.player_id == lebron.id
        ).all()
        
        if lebron_props:
            game_id = lebron_props[0].game_id
            game = db.query(models.Game).filter(models.Game.id == game_id).first()
            
            if game:
                print(f"Game ID: {game.id}")
                print(f"Game date (UTC): {game.game_date}")
                print(f"Game date (naive): {game.game_date.replace(tzinfo=None) if game.game_date else 'None'}")
                
                # Convert to different timezones
                if game.game_date:
                    utc_time = game.game_date.replace(tzinfo=timezone.utc)
                    
                    # Convert to Eastern Time (ET)
                    et_time = utc_time.astimezone(timezone.utc).replace(hour=utc_time.hour-5)
                    print(f"Estimated ET time: {et_time}")
                    
                    # Check if this is a reasonable game time
                    if et_time.hour >= 19:  # 7 PM or later
                        print("This looks like a normal evening game time")
                    elif et_time.hour >= 12:  # Noon or later
                        print("This looks like an afternoon game")
                    else:
                        print("This looks like a morning game or date issue")
                        
                    # Show what our gameday range would be
                    from app.date_utils import get_gameday_range
                    start_utc, end_utc = get_gameday_range(datetime.now().date())
                    print(f"\nCurrent gameday range: {start_utc} to {end_utc}")
                    print(f"Game in current range? {start_utc <= game.game_date < end_utc}")
                    
                    # Check previous day
                    from datetime import timedelta
                    yesterday = datetime.now().date() - timedelta(days=1)
                    start_yesterday, end_yesterday = get_gameday_range(yesterday)
                    print(f"\nYesterday's range: {start_yesterday} to {end_yesterday}")
                    print(f"Game in yesterday's range? {start_yesterday <= game.game_date < end_yesterday}")
    
finally:
    db.close()