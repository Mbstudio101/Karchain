
import asyncio
import aiohttp
import logging
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models import Game

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ESPN API Endpoint
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

async def fetch_live_scores():
    """Fetches live scores from ESPN and updates the database."""
    async with aiohttp.ClientSession() as session:
        try:
            logger.info(f"Fetching live scores from {ESPN_SCOREBOARD_URL}...")
            async with session.get(ESPN_SCOREBOARD_URL) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch scores: HTTP {response.status}")
                    return

                data = await response.json()
                events = data.get('events', [])
                
                logger.info(f"Found {len(events)} games in ESPN feed.")
                
                db = SessionLocal()
                try:
                    update_games(db, events)
                finally:
                    db.close()

        except Exception as e:
            logger.error(f"Error fetching scores: {e}")

def update_games(db: Session, events: list):
    """Updates game status and scores in the database."""
    updated_count = 0
    
    # Get all games scheduled for today/yesterday/tomorrow window
    window_start = datetime.utcnow() - timedelta(hours=24)
    window_end = datetime.utcnow() + timedelta(hours=24)
    
    db_games = db.query(Game).filter(
        Game.game_date >= window_start,
        Game.game_date <= window_end
    ).all()
    
    logger.info(f"Found {len(db_games)} games in DB to potentially update.")

    for event in events:
        try:
            competition = event['competitions'][0]
            competitors = competition['competitors']
            
            home_team_data = next(c for c in competitors if c['homeAway'] == 'home')
            away_team_data = next(c for c in competitors if c['homeAway'] == 'away')
            
            home_score = int(home_team_data.get('score', 0))
            away_score = int(away_team_data.get('score', 0))
            
            status_type = event['status']['type']['name'] # STATUS_SCHEDULED, STATUS_IN_PROGRESS, STATUS_FINAL
            clock = event['status'].get('displayClock', "0:00")
            period = event['status'].get('period', 0)
            
            # Map ESPN status to our model
            status_map = {
                "STATUS_SCHEDULED": "Scheduled",
                "STATUS_IN_PROGRESS": "Live",
                "STATUS_HALFTIME": "Live",
                "STATUS_FINAL": "Final",
                "STATUS_POSTPONED": "Postponed",
                "STATUS_DELAYED": "Postponed"
            }
            game_status = status_map.get(status_type, "Scheduled")
            
            quarter_display = f"Q{period}" if period > 0 else None
            if status_type == "STATUS_FINAL":
                quarter_display = "Final"
            elif status_type == "STATUS_HALFTIME":
                quarter_display = "Half"
            
            # ESPN Name normalization
            espn_home_name = home_team_data['team']['displayName']
            espn_away_name = away_team_data['team']['displayName']
            
            # Identify game in DB
            target_game = None
            for g in db_games:
                # Check if team names loosely match
                # ESPN: "Los Angeles Lakers" vs DB: "Lakers" or "Los Angeles Lakers"
                db_home = g.home_team.name
                db_away = g.away_team.name
                
                # Check if names contain each other
                home_match = (db_home in espn_home_name) or (espn_home_name in db_home)
                away_match = (db_away in espn_away_name) or (espn_away_name in db_away)
                
                if home_match and away_match:
                    target_game = g
                    break
            
            if target_game:
                target_game.home_score = home_score
                target_game.away_score = away_score
                target_game.status = game_status
                target_game.clock = clock
                target_game.quarter = quarter_display
                updated_count += 1
                logger.info(f"Updated: {espn_away_name} @ {espn_home_name} -> {game_status} {away_score}-{home_score}")
        except Exception as e:
            logger.error(f"Error processing game event: {e}")
            continue

    db.commit()
    logger.info(f"Successfully updated {updated_count} games.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fetch_live_scores())
