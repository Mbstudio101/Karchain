import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models

db = SessionLocal()
try:
    # Get LeBron's props and game
    lebron = db.query(models.Player).filter(models.Player.name.ilike("%lebron%")).first()
    if lebron:
        lebron_props = db.query(models.PlayerProps).filter(
            models.PlayerProps.player_id == lebron.id
        ).all()
        
        print(f"LeBron has {len(lebron_props)} props")
        
        if lebron_props:
            prop = lebron_props[0]
            print(f"First prop ID: {prop.id}")
            print(f"Prop timestamp: {prop.timestamp}")
            print(f"Game ID: {prop.game_id}")
            
            if prop.game_id:
                game = db.query(models.Game).filter(models.Game.id == prop.game_id).first()
                if game:
                    print(f"Game found!")
                    print(f"Game date: {game.game_date}")
                    print(f"Game date type: {type(game.game_date)}")
                    
                    # Check the hour
                    if hasattr(game.game_date, 'hour'):
                        print(f"Hour: {game.game_date.hour}")
                        print(f"This is a {game.game_date.hour}:00 UTC game")
                        
                        # Convert to ET
                        et_hour = (game.game_date.hour - 5) % 24
                        print(f"ET time: {et_hour}:00")
                        
                        if game.game_date.hour == 3:
                            print("This is a 10 PM ET game (3 AM UTC)")
                        elif game.game_date.hour >= 19:
                            print("This is an evening game")
                        elif game.game_date.hour >= 12:
                            print("This is an afternoon game")
                        else:
                            print("This is a morning game")
    
finally:
    db.close()