from app.database import SessionLocal
from app.models import Team, Game, BettingOdds
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def merge_teams(source_id, target_id):
    db = SessionLocal()
    try:
        source = db.query(Team).get(source_id)
        target = db.query(Team).get(target_id)
        
        if not source or not target:
            logger.error(f"Team not found: {source_id} or {target_id}")
            return
            
        logger.info(f"Merging Team '{source.name}' (ID: {source_id}) into '{target.name}' (ID: {target_id})")
        
        # 1. Update Games where source is home team
        home_games = db.query(Game).filter(Game.home_team_id == source_id).all()
        for g in home_games:
            g.home_team_id = target_id
            
        # 2. Update Games where source is away team
        away_games = db.query(Game).filter(Game.away_team_id == source_id).all()
        for g in away_games:
            g.away_team_id = target_id
            
        # 3. Delete source team
        db.delete(source)
        
        db.commit()
        logger.info("Merge complete.")
        
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Merge "LA Clippers" (20) into "Los Angeles Clippers" (32)
    merge_teams(20, 32)
