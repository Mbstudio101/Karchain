"""
Player Props Generator
Generates realistic player props based on actual player stats averages.
"""
import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

from app.database import SessionLocal
from app import models
from datetime import datetime
import random

def generate_props_for_players():
    """Generate player props based on their actual stats averages."""
    db = SessionLocal()
    
    try:
        # Get all players with stats
        players = db.query(models.Player).all()
        props_created = 0
        
        # Clear existing props
        db.query(models.PlayerProps).delete()
        db.commit()
        
        for player in players:
            if not player.stats:
                continue
            
            # Calculate averages
            stats = player.stats[:10]  # Use last 10 games
            if len(stats) < 3:
                continue
                
            avg_pts = sum(s.points for s in stats) / len(stats)
            avg_reb = sum(s.rebounds for s in stats) / len(stats)
            avg_ast = sum(s.assists for s in stats) / len(stats)
            
            # Only create props for players with meaningful averages
            if avg_pts < 2 and avg_reb < 2 and avg_ast < 1:
                continue
            
            # Generate props with realistic lines (usually 0.5 increments)
            prop_types = []
            
            if avg_pts >= 5:
                # Points prop
                line = round(avg_pts * 2) / 2  # Round to nearest 0.5
                prop_types.append(('points', line))
            
            if avg_reb >= 3:
                # Rebounds prop
                line = round(avg_reb * 2) / 2
                prop_types.append(('rebounds', line))
            
            if avg_ast >= 2:
                # Assists prop
                line = round(avg_ast * 2) / 2
                prop_types.append(('assists', line))
            
            # PRA (Points + Rebounds + Assists) combo
            pra = avg_pts + avg_reb + avg_ast
            if pra >= 15:
                line = round(pra * 2) / 2
                prop_types.append(('pts+reb+ast', line))
            
            # Create props
            for prop_type, line in prop_types:
                # Generate realistic odds (usually around -110/-110 for balanced props)
                variance = random.randint(-8, 8)
                over_odds = -110 + variance
                under_odds = -110 - variance
                
                prop = models.PlayerProps(
                    player_id=player.id,
                    prop_type=prop_type,
                    line=line,
                    over_odds=over_odds,
                    under_odds=under_odds,
                    timestamp=datetime.utcnow()
                )
                db.add(prop)
                props_created += 1
        
        db.commit()
        print(f"✅ Generated {props_created} player props")
        
    except Exception as e:
        print(f"❌ Props generation failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_props_for_players()
