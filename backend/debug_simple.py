import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import datetime, timedelta

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
                print(f"Game date: {game.game_date}")
                
                # Convert 3 AM UTC to ET (subtract 5 hours)
                utc_hour = game.game_date.hour
                et_hour = (utc_hour - 5) % 24
                
                print(f"UTC time: {utc_hour}:00")
                print(f"ET time: {et_hour}:00")
                
                # This is likely a 10 PM ET game (3 AM UTC = 10 PM previous day ET)
                if utc_hour == 3:
                    print("This is a 10 PM ET game from the previous day")
                
                # Check gameday ranges
                from app.date_utils import get_gameday_range
                from datetime import date
                
                today = date.today()
                yesterday = today - timedelta(days=1)
                
                start_today, end_today = get_gameday_range(today)
                start_yesterday, end_yesterday = get_gameday_range(yesterday)
                
                print(f"\nToday's range: {start_today} to {end_today}")
                print(f"Yesterday's range: {start_yesterday} to {end_yesterday}")
                
                # Check where the game falls
                in_today = start_today <= game.game_date < end_today
                in_yesterday = start_yesterday <= game.game_date < end_yesterday
                
                print(f"Game in today: {in_today}")
                print(f"Game in yesterday: {in_yesterday}")
                
                if in_yesterday:
                    print("\n🎯 FOUND THE ISSUE: LeBron's game is in yesterday's gameday!")
                    print("The game is a 10 PM ET game, which is 3 AM UTC next day")
                    print("But our gameday logic groups it with yesterday's games")
    
finally:
    db.close()