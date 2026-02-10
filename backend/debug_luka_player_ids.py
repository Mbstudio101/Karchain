
import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import PlayerProps, Player

db = SessionLocal()

def check_luka_props():
    print("Checking which Luka player IDs are used in props...")
    
    # Get all Luka props
    luka_props = db.query(PlayerProps).join(Player).filter(
        Player.name.ilike("%luka%")
    ).all()
    
    print(f"Found {len(luka_props)} props for players with 'luka' in name:")
    
    player_ids_used = set()
    for prop in luka_props:
        player_name = prop.player.name
        player_id = prop.player_id
        player_ids_used.add(player_id)
        print(f"  Prop ID {prop.id}: '{player_name}' (Player ID: {player_id}) - {prop.prop_type}: {prop.line}")
    
    print(f"\nPlayer IDs used: {player_ids_used}")
    
    # Check each player ID
    for player_id in player_ids_used:
        player = db.query(Player).filter(Player.id == player_id).first()
        if player:
            stats_count = len(player.stats)
            print(f"Player ID {player_id}: '{player.name}' - {stats_count} stats")
    
    # Check if we can fix the issue by updating the player_id
    correct_luka = db.query(Player).filter(Player.name == "Luka Dončić").first()
    incorrect_luka = db.query(Player).filter(Player.name == "Luka Doncic").first()
    
    if correct_luka and incorrect_luka:
        print(f"\n--- SOLUTION ---")
        print(f"Correct player: ID {correct_luka.id} ('{correct_luka.name}') - {len(correct_luka.stats)} stats")
        print(f"Incorrect player: ID {incorrect_luka.id} ('{incorrect_luka.name}') - {len(incorrect_luka.stats)} stats")
        
        # Find props linked to incorrect player
        bad_props = db.query(PlayerProps).filter(PlayerProps.player_id == incorrect_luka.id).all()
        print(f"Props linked to incorrect player: {len(bad_props)}")
        
        if bad_props:
            print("These props need to be updated to use the correct player ID.")

try:
    check_luka_props()
finally:
    db.close()