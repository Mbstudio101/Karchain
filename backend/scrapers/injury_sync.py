import requests
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Player, Injury, Team

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_nba_injuries():
    """
    Scrapes NBA injury data from ESPN's public API and updates the database.
    """
    logger.info("Starting NBA injury sync...")
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        db = SessionLocal()
        try:
            # ESPN Structure: { "injuries": [ { "displayName": "Atlanta Hawks", "injuries": [ { "athlete": {...} }, ... ] }, ... ] }
            injuries_data = data.get('injuries', [])
            logger.info(f"Found {len(injuries_data)} team blocks in injury data")
            
            for team_entry in injuries_data:
                team_name = team_entry.get('displayName', 'Unknown Team')
                team_injuries = team_entry.get('injuries', [])
                
                logger.info(f"Syncing {len(team_injuries)} injuries for {team_name}...")
                
                for inj in team_injuries:
                    player_data = inj.get('athlete', {})
                    player_name = player_data.get('displayName')
                    injury_status = inj.get('status', 'Unknown')
                    injury_type = inj.get('shortComment', 'N/A')
                    
                    if not player_name:
                        continue
                        
                    # Find player in DB (case-insensitive and partial match to handle suffixes like 'Jr.')
                    player = db.query(Player).filter(Player.name.ilike(f"%{player_name}%")).first()
                    
                    if player:
                        # Update or create injury record
                        injury_record = db.query(Injury).filter(Injury.player_id == player.id).first()
                        
                        if not injury_record:
                            injury_record = Injury(player_id=player.id)
                            db.add(injury_record)
                        
                        injury_record.status = injury_status
                        injury_record.injury_type = injury_type
                        injury_record.updated_date = datetime.utcnow()
                        
                        logger.info(f"✅ Updated injury for {player_name} (DB: {player.name}): {injury_status}")
                    else:
                        logger.warning(f"❌ Player not found in DB: {player_name}")
            
            db.commit()
            logger.info("NBA injury sync complete.")
            
        except Exception as e:
            logger.error(f"Error updating injury database: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to fetch injury data from ESPN: {e}")

if __name__ == "__main__":
    sync_nba_injuries()
