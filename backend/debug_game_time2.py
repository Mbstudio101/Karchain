import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import datetime, timezone, timedelta

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
            
            if game and game.game_date:
                print(f"Game ID: {game.id}")
                print(f"Game date (raw): {game.game_date}")
                print(f"Game date type: {type(game.game_date)}")
                
                # Convert to Eastern Time manually (UTC-5)
                game_datetime = game.game_date
                if game_datetime.hour == 3 and game_datetime.minute == 0:
                    # This is likely a 10 PM ET game (3 AM UTC = 10 PM previous day ET)
                    et_datetime = game_datetime - timedelta(hours=5)
                    print(f"Estimated ET time: {et_datetime}")
                    print(f"This would be a {et_datetime.strftime('%I:%M %p')} ET game")
                    
                    # Check gameday ranges
                    from app.date_utils import get_gameday_range
                    
                    # Current day range
                    today = datetime.now().date()
                    start_today, end_today = get_gameday_range(today)
                    print(f"\nToday's gameday range: {start_today} to {end_today}")
                    print(f"Game in today range: {start_today <= game_datetime < end_today}")
                    
                    # Previous day range  
                    yesterday = today - timedelta(days=1)
                    start_yesterday, end_yesterday = get_gameday_range(yesterday)
                    print(f"\nYesterday's gameday range: {start_yesterday} to {end_yesterday}")
                    print(f"Game in yesterday range: {start_yesterday <= game_datetime < end_yesterday}")
                    
                    # The issue is clear - the game is at 3 AM UTC which is 10 PM ET
                    # But our gameday logic starts at 10 AM UTC (5 AM ET)
                    # So this game falls in the "previous" gameday
                    
                    print(f"\nSOLUTION: The game is actually for yesterday's gameday!")
                    
finally:
    db.close()