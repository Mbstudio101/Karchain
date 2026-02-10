import logging
import sys
import os
from datetime import datetime, timedelta
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import boxscoretraditionalv3
from sqlalchemy.orm import Session
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Game, Team, Player, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_official_scoreboard():
    """
    Syncs today's games using the official NBA Live API.
    """
    logger.info("Starting official NBA scoreboard sync...")
    db = SessionLocal()
    try:
        # 1. Fetch Today's Scoreboard
        board = scoreboard.ScoreBoard()
        data = board.get_dict()
        games_data = data.get('scoreboard', {}).get('games', [])

        if not games_data:
            logger.info("No games found on the official scoreboard for today.")
            return

        for game_entry in games_data:
            game_id_official = game_entry.get('gameId')
            home_team_data = game_entry.get('homeTeam', {})
            away_team_data = game_entry.get('awayTeam', {})
            
            home_name = home_team_data.get('teamName')
            away_name = away_team_data.get('teamName')
            
            home_score = home_team_data.get('score', 0)
            away_score = away_team_data.get('score', 0)
            
            status_text = game_entry.get('gameStatusText', 'Scheduled')
            period = game_entry.get('period', 0)
            
            # Map status
            final_status = "Scheduled"
            if "Final" in status_text:
                final_status = "Final"
            elif period > 0:
                final_status = "Live"
                
            # Find teams in DB
            def find_team(name):
                # Official API usually gives just the team name (e.g. "Celtics")
                return db.query(Team).filter(Team.name.ilike(f"%{name}%")).first()

            db_home_team = find_team(home_name)
            db_away_team = find_team(away_name)
            
            if db_home_team and db_away_team:
                now = datetime.utcnow()
                start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                game = db.query(Game).filter(
                    Game.home_team_id == db_home_team.id,
                    Game.away_team_id == db_away_team.id,
                    Game.game_date >= start_of_day,
                    Game.game_date < end_of_day
                ).first()
                
                if not game:
                    logger.info(f"Creating NEW game: {away_name} @ {home_name}")
                    # Use a default time if entry doesn't have it, but scoreboard usually has today's games
                    game = Game(
                        home_team_id=db_home_team.id,
                        away_team_id=db_away_team.id,
                        game_date=now, 
                        sport="NBA",
                        status=final_status
                    )
                    db.add(game)
                    db.flush()

                logger.info(f"Updating game {game.id}: {away_name} @ {home_name} -> {final_status} ({away_score}-{home_score})")
                game.status = final_status
                game.home_score = home_score
                game.away_score = away_score
                game.quarter = f"Q{period}" if period > 0 else None
                if status_text == "Halftime":
                    game.quarter = "HT"
                
                # If game is Final or Live, we could fetch boxscore, but boxscoretraditionalv3 needs gameId
                # Note: nba_api stats endpoints often use the official 10-digit game IDs (e.g. '0022300001')
                if final_status in ["Final", "Live"] and game_id_official:
                    try:
                        sync_official_boxscore(db, game, game_id_official)
                    except Exception as e:
                        logger.error(f"Failed to sync boxscore for game {game.id}: {e}")

        db.commit()
        logger.info("Official scoreboard sync complete.")
        
    except Exception as e:
        logger.error(f"Error during official sync: {e}")
        db.rollback()
    finally:
        db.close()

def sync_official_boxscore(db: Session, game: Game, official_game_id: str):
    """
    Syncs player stats for a specific game using BoxScoreTraditionalV3.
    """
    logger.info(f"Fetching boxscore for official game ID: {official_game_id}")
    box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=official_game_id)
    data = box.get_dict()
    
    # Structure for V3 is typically: data['boxScoreTraditional']
    box_data = data.get('boxScoreTraditional', {})
    home_players = box_data.get('homeTeam', {}).get('players', [])
    away_players = box_data.get('awayTeam', {}).get('players', [])
    
    all_players = home_players + away_players
    
    for p_data in all_players:
        player_name = f"{p_data.get('firstName')} {p_data.get('familyName')}"
        stats = p_data.get('statistics', {})
        
        if not stats: continue
        
        # Find or create player
        db_player = db.query(Player).filter(Player.name == player_name).first()
        if not db_player:
            # We skip for now as we should have players from the daily scrape
            continue
            
        # Find or update stat entry
        stat_entry = db.query(PlayerStats).filter(
            PlayerStats.player_id == db_player.id,
            PlayerStats.game_id == game.id
        ).first()
        
        if not stat_entry:
            # Get opponent name
            is_home = (db_player.team_id == game.home_team_id)
            opp_team_id = game.away_team_id if is_home else game.home_team_id
            opp_team = db.query(Team).get(opp_team_id)
            
            stat_entry = PlayerStats(
                player_id=db_player.id,
                game_id=game.id,
                game_date=game.game_date.date(),
                opponent=opp_team.name if opp_team else "Unknown"
            )
            db.add(stat_entry)
            
        # Update stats
        try:
            # V3 uses keys like 'points', 'reboundsTotal', 'assists', etc.
            stat_entry.points = float(stats.get('points', 0))
            stat_entry.rebounds = float(stats.get('reboundsTotal', 0))
            stat_entry.assists = float(stats.get('assists', 0))
            stat_entry.steals = float(stats.get('steals', 0))
            stat_entry.blocks = float(stats.get('blocks', 0))
            
            # Minutes is usually a string like "PT24M30S" or "24:30"
            min_str = stats.get('minutes', '0:00')
            if 'PT' in min_str:  # ISO duration format PT24M30S
                import re
                m_match = re.search(r'(\d+)M', min_str)
                s_match = re.search(r'(\d+)S', min_str)
                mins = int(m_match.group(1)) if m_match else 0
                secs = int(s_match.group(1)) if s_match else 0
                stat_entry.minutes_played = float(mins) + round(secs / 60, 2)
            elif ':' in min_str:
                parts = min_str.split(':')
                stat_entry.minutes_played = float(parts[0]) + round(float(parts[1]) / 60, 2) if len(parts) > 1 else float(parts[0])
            else:
                stat_entry.minutes_played = float(min_str)
        except Exception as e:
            logger.warning(f"Error parsing stats for {player_name}: {e}")

if __name__ == "__main__":
    sync_official_scoreboard()
