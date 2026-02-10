
import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import PlayerProps, Player

db = SessionLocal()

def fix_duplicate_luka():
    print("Fixing duplicate Luka entries...")
    
    correct_luka = db.query(Player).filter(Player.name == "Luka Dončić").first()
    incorrect_luka = db.query(Player).filter(Player.name == "Luka Doncic").first()
    
    if not correct_luka or not incorrect_luka:
        print("Could not find both player entries. Aborting.")
        return
        
    print(f"Correct player: ID {correct_luka.id} ('{correct_luka.name}')")
    print(f"Incorrect player: ID {incorrect_luka.id} ('{incorrect_luka.name}')")
    
    # 1. Update props
    props_to_update = db.query(PlayerProps).filter(PlayerProps.player_id == incorrect_luka.id).all()
    print(f"Found {len(props_to_update)} props to update.")
    
    for prop in props_to_update:
        prop.player_id = correct_luka.id
        print(f"  Updated prop {prop.id} ({prop.prop_type}) to player ID {correct_luka.id}")
    
    # 2. Delete incorrect player
    print(f"Deleting incorrect player ID {incorrect_luka.id}...")
    db.delete(incorrect_luka)
    
    # Commit changes
    try:
        db.commit()
        print("✅ Database fixed successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error committing changes: {e}")

if __name__ == "__main__":
    fix_duplicate_luka()
    db.close()