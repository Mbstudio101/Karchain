from app.database import SessionLocal
from app import models

# Check the database structure
db = SessionLocal()

# Check player props with their relationships
props = db.query(models.PlayerProps).limit(5).all()
for prop in props:
    print(f'Prop ID: {prop.id}')
    print(f'  Player ID: {prop.player_id}')
    print(f'  Game ID: {prop.game_id}')
    print(f'  Prop Type: {prop.prop_type}')
    print(f'  Line: {prop.line}')
    
    # Check if player exists
    if prop.player:
        print(f'  Player Name: {prop.player.name}')
        print(f'  Player Headshot: {prop.player.headshot_url}')
    else:
        print(f'  Player: None (this is the issue!)')
    
    # Check if game exists
    if prop.game:
        print(f'  Game: {prop.game.home_team.name} vs {prop.game.away_team.name}')
    else:
        print(f'  Game: None')
    print()

db.close()