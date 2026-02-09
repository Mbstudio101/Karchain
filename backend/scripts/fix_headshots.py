"""
Migration script to fix headshot URLs using NBA CDN.
"""
import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

from app.database import SessionLocal
from app import models

def generate_nba_headshot(player_name: str) -> str:
    """Generate NBA CDN headshot URL from player name."""
    # NBA CDN uses format: https://cdn.nba.com/headshots/nba/latest/260x190/PLAYER_ID.png
    # But we don't have player IDs, so use ui-avatars as fallback with initials
    # This generates a clean avatar with the player's initials
    
    parts = player_name.split()
    if len(parts) >= 2:
        initials = f"{parts[0][0]}{parts[-1][0]}"
    else:
        initials = player_name[:2]
    
    # Use a high-quality avatar service with player initials
    return f"https://ui-avatars.com/api/?name={player_name.replace(' ', '+')}&size=256&background=1a1a2e&color=10b981&bold=true&format=png"

def run_migration():
    """Update all players with working headshot URLs."""
    db = SessionLocal()
    
    try:
        players = db.query(models.Player).all()
        updated = 0
        
        for player in players:
            player.headshot_url = generate_nba_headshot(player.name)
            updated += 1
        
        db.commit()
        print(f"✅ Updated {updated} players with avatar headshots")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
