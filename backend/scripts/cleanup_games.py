from app.database import SessionLocal
from app.models import Game, Team
from datetime import datetime
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_duplicates():
    db = SessionLocal()
    try:
        # Find games on the same day with same teams
        # We'll use a simple approach: iterate through all games for the last 7 days
        recent_games = db.query(Game).filter(Game.game_date >= datetime(2026, 2, 5)).all()
        
        seen = {} # (home_team_id, away_team_id, date) -> list of games
        
        for game in recent_games:
            key = (game.home_team_id, game.away_team_id, game.game_date.date())
            if key not in seen:
                seen[key] = []
            seen[key].append(game)
            
        for key, games in seen.items():
            if len(games) > 1:
                logger.info(f"Checking duplicates for {key} | Count: {len(games)}")
                # Sort games: keep the one with scores/status "Final"
                # If all 0-0, keep the one with official ESPN time (if we track it) or lowest ID
                games.sort(key=lambda x: (x.status == "Final", x.home_score > 0), reverse=True)
                
                keep = games[0]
                to_delete = games[1:]
                
                for game_to_del in to_delete:
                    logger.info(f"  Deleting duplicate ID: {game_to_del.id} (Keeping ID: {keep.id})")
                    # Move odds if any
                    for odds in game_to_del.odds:
                        odds.game_id = keep.id
                    db.delete(game_to_del)
        
        db.commit()
        logger.info("Cleanup complete.")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicates()
