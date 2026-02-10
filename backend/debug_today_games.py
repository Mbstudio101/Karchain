import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import date
from app.date_utils import get_gameday_range

db = SessionLocal()
try:
    today = date.today()
    start_utc, end_utc = get_gameday_range(today)
    
    print(f"Today's date: {today}")
    print(f"Gameday range: {start_utc} to {end_utc}")
    
    # Get today's scheduled games
    today_games = db.query(models.Game).filter(
        models.Game.game_date >= start_utc,
        models.Game.game_date < end_utc,
        models.Game.status == "Scheduled"
    ).all()
    
    print(f"\nScheduled games for today: {len(today_games)}")
    
    for game in today_games:
        print(f"\nGame: {game.away_team.name} @ {game.home_team.name}")
        print(f"  Date: {game.game_date}")
        print(f"  Status: {game.status}")
        
        # Check if there are props for this game
        game_props = db.query(models.PlayerProps).filter(
            models.PlayerProps.game_id == game.id
        ).all()
        
        print(f"  Props: {len(game_props)}")
        
        # Check if LeBron should be in this game
        if game.home_team.name == "Los Angeles Lakers" or game.away_team.name == "Los Angeles Lakers":
            print(f"  🟡 Lakers game - should have LeBron props!")
            
            lebron_props = [p for p in game_props if p.player and 'lebron' in p.player.name.lower()]
            print(f"  LeBron props in this game: {len(lebron_props)}")
            
            if lebron_props:
                for prop in lebron_props[:3]:
                    print(f"    - {prop.prop_type}: {prop.line}")
            else:
                print(f"    ❌ No LeBron props found!")
        
        # Check for Dallas
        if game.home_team.name == "Dallas Mavericks" or game.away_team.name == "Dallas Mavericks":
            print(f"  🟡 Mavericks game - should have Luka props!")
            
            luka_props = [p for p in game_props if p.player and 'luka' in p.player.name.lower()]
            print(f"  Luka props in this game: {len(luka_props)}")
            
            if luka_props:
                for prop in luka_props[:3]:
                    print(f"    - {prop.prop_type}: {prop.line}")
            else:
                print(f"    ❌ No Luka props found!")
    
    # Also check yesterday's games for LeBron
    from datetime import timedelta
    yesterday = today - timedelta(days=1)
    start_yesterday, end_yesterday = get_gameday_range(yesterday)
    
    yesterday_games = db.query(models.Game).filter(
        models.Game.game_date >= start_yesterday,
        models.Game.game_date < end_yesterday,
        models.Game.status == "Scheduled"
    ).all()
    
    print(f"\n\nScheduled games for yesterday: {len(yesterday_games)}")
    
    for game in yesterday_games:
        if game.home_team.name == "Los Angeles Lakers" or game.away_team.name == "Los Angeles Lakers":
            print(f"\n🟢 Lakers game from yesterday: {game.away_team.name} @ {game.home_team.name}")
            print(f"  Date: {game.game_date}")
            
            game_props = db.query(models.PlayerProps).filter(
                models.PlayerProps.game_id == game.id
            ).all()
            
            lebron_props = [p for p in game_props if p.player and 'lebron' in p.player.name.lower()]
            print(f"  LeBron props: {len(lebron_props)}")
            
            if lebron_props:
                for prop in lebron_props[:3]:
                    print(f"    - {prop.prop_type}: {prop.line}")
    
finally:
    db.close()