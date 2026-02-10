import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import date, timedelta

db = SessionLocal()
try:
    # Check all Lakers games in the last 2 days
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    lakers_games = db.query(models.Game).join(models.Team, models.Game.home_team_id == models.Team.id).filter(
        models.Team.name == "Los Angeles Lakers",
        models.Game.game_date >= yesterday
    ).all()
    
    print("All Lakers games in last 2 days:")
    for game in lakers_games:
        print(f"\nGame {game.id}: {game.away_team.name} @ {game.home_team.name}")
        print(f"  Date: {game.game_date}")
        print(f"  Status: {game.status}")
        
        # Check props for this game
        game_props = db.query(models.PlayerProps).filter(
            models.PlayerProps.game_id == game.id
        ).all()
        
        print(f"  Total props: {len(game_props)}")
        
        # Check LeBron props specifically
        lebron_props = [p for p in game_props if p.player and 'lebron' in p.player.name.lower()]
        print(f"  LeBron props: {len(lebron_props)}")
        
        if lebron_props:
            print("  LeBron props found:")
            for prop in lebron_props[:3]:
                print(f"    - {prop.prop_type}: {prop.line}")
    
    # Also check away games
    lakers_away_games = db.query(models.Game).join(models.Team, models.Game.away_team_id == models.Team.id).filter(
        models.Team.name == "Los Angeles Lakers",
        models.Game.game_date >= yesterday
    ).all()
    
    print(f"\nLakers away games: {len(lakers_away_games)}")
    for game in lakers_away_games:
        print(f"Game {game.id}: {game.away_team.name} @ {game.home_team.name} on {game.game_date}")
    
finally:
    db.close()