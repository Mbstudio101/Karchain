import requests
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Game, Team, Player, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ESPN NBA Scoreboard API
ESPN_SCOREBOARD_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

def sync_espn_data(date_str: str = None):
    """
    Fetches real-time NBA game data from ESPN for a specific date and updates the local database.
    date_str format: YYYYMMDD
    """
    url = ESPN_SCOREBOARD_URL
    if date_str:
        url += f"?dates={date_str}"
        
    logger.info(f"Starting ESPN status sync for {date_str if date_str else 'today'}...")
    db = SessionLocal()
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        events = data.get("events", [])
        if not events:
            logger.info(f"No NBA events found on ESPN for {date_str}.")
            return

        for event in events:
            status_data = event.get("status", {})
            type_data = status_data.get("type", {})
            status_desc = type_data.get("description", "Scheduled")
            
            # Map ESPN status to our DB status
            final_status = status_desc
            if status_desc == "In Progress":
                final_status = "Live"
            elif status_desc == "Scheduled":
                final_status = "Scheduled"
            elif "Final" in status_desc:
                final_status = "Final"
            
            # Get competition info
            competitions = event.get("competitions", [{}])[0]
            competitors = competitions.get("competitors", [])
            venue_data = competitions.get("venue", {})
            venue_name = venue_data.get("fullName")
            
            home_team_data = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away_team_data = next((c for c in competitors if c.get("homeAway") == "away"), {})
            
            home_score = int(home_team_data.get("score", 0))
            away_score = int(away_team_data.get("score", 0))
            
            home_name = home_team_data.get("team", {}).get("displayName")
            away_name = away_team_data.get("team", {}).get("displayName")
            
            # Period and Clock
            period = status_data.get("period")
            clock = status_data.get("displayClock")
            
            # Game Date
            event_date_str = event.get("date")
            event_date = datetime.strptime(event_date_str, "%Y-%m-%dT%H:%MZ") if event_date_str else datetime.utcnow()

            # Find teams in DB - we must have teams to save games
            # Find teams in DB - we must have teams to save games
            def find_team(name):
                # Try exact match
                t = db.query(Team).filter(Team.name.ilike(name)).first()
                if t: return t
                
                # Try prefix/suffix match (e.g. "LA Clippers" vs "Clippers")
                t = db.query(Team).filter(Team.name.ilike(f"%{name}%")).first()
                if t: return t
                
                # Special cases for NBA naming
                special_cases = {
                    "LA Clippers": "Los Angeles Clippers",
                    "Clippers": "Los Angeles Clippers",
                    "LA Lakers": "Los Angeles Lakers",
                    "Lakers": "Los Angeles Lakers",
                    "Portland": "Portland Trail Blazers",
                    "Phila": "Philadelphia 76ers",
                    "Sixers": "Philadelphia 76ers"
                }
                if name in special_cases:
                    return db.query(Team).filter(Team.name.ilike(special_cases[name])).first()
                
                return None

            db_home_team = find_team(home_name)
            db_away_team = find_team(away_name)
            
            if db_home_team and db_away_team:
                # Look for a game between these teams on this specific day
                start_of_day = event_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                game = db.query(Game).filter(
                    Game.home_team_id == db_home_team.id,
                    Game.away_team_id == db_away_team.id,
                    Game.game_date >= start_of_day,
                    Game.game_date < end_of_day
                ).first()
                
                if not game:
                    logger.info(f"Creating NEW game: {away_name} @ {home_name} for {event_date}")
                    game = Game(
                        home_team_id=db_home_team.id,
                        away_team_id=db_away_team.id,
                        game_date=event_date,
                        venue=venue_name,
                        sport="NBA",
                        status=final_status
                    )
                    db.add(game)
                    db.flush() # Get ID

                # Update status and scores
                logger.info(f"Updating game {game.id}: {away_name} @ {home_name} -> {final_status} ({away_score}-{home_score})")
                game.status = final_status
                game.home_score = home_score
                game.away_score = away_score
                game.quarter = f"Q{period}" if period else None
                if status_desc == "Halftime":
                    game.quarter = "HT"
                game.clock = clock
                # Always update the date to the official ESPN time
                game.game_date = event_date
                
                # 4. If game is FINAL or LIVE, sync player stats
                if final_status in ["Final", "Live"]:
                    try:
                        espn_id = event.get("id")
                        if espn_id:
                            _sync_player_boxscore(db, game, espn_id)
                    except Exception as e:
                        logger.error(f"Player stats sync failed for game {game.id}: {e}")
                    
        db.commit()
        logger.info(f"ESPN status sync complete for {date_str}.")
        
    except Exception as e:
        logger.error(f"Error during ESPN sync for {date_str}: {e}")
        db.rollback()
    finally:
        db.close()
def _sync_player_boxscore(db: Session, game: Game, espn_event_id: str):
    """
    Fetches box score data from ESPN and updates PlayerStats for a game.
    """
    summary_url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={espn_event_id}"
    resp = requests.get(summary_url, timeout=10)
    resp.raise_for_status()
    summary_data = resp.json()
    
    boxscore = summary_data.get("boxscore", {})
    players_data = boxscore.get("players", [])
    
    for team_idx, team_data in enumerate(players_data):
        espn_team_name = team_data.get("team", {}).get("displayName", "")
        statistics = team_data.get("statistics", [])
        if not statistics: continue

        # Determine which DB team this ESPN team corresponds to
        # ESPN boxscore lists away team first (index 0), home team second (index 1)
        if team_idx == 0:
            team_id = game.away_team_id
            opponent_id = game.home_team_id
        else:
            team_id = game.home_team_id
            opponent_id = game.away_team_id

        opponent_team = db.query(Team).get(opponent_id)
        opponent_name = opponent_team.name if opponent_team else "Unknown"

        # Usually the first statistics entry contains the 'athletes' list
        athletes = statistics[0].get("athletes", [])
        for athlete_entry in athletes:
            athlete = athlete_entry.get("athlete", {})
            name = athlete.get("displayName")
            if not name: continue

            # Find or create player
            db_player = db.query(Player).filter(Player.name == name).first()
            if not db_player:
                position = athlete.get("position", {}).get("abbreviation") if isinstance(athlete.get("position"), dict) else None
                db_player = Player(
                    name=name,
                    sport="NBA",
                    position=position,
                    team_id=team_id,
                    active_status=True
                )
                db.add(db_player)
                db.flush()
                logger.info(f"Created new player: {name} (team_id={team_id})")

            # Parse stats
            stats_values = athlete_entry.get("stats", [])
            # ESPN NBA Boxscore stats order is usually:
            # MIN, FG, 3PT, FT, OREB, DREB, REB, AST, STL, BLK, TO, PF, +/-, PTS
            if len(stats_values) < 14:
                logger.warning(f"Incomplete stats for {name} in game {game.id}: only {len(stats_values)} values")
                continue

            # Find or update stat entry for this game
            stat_entry = db.query(PlayerStats).filter(
                PlayerStats.player_id == db_player.id,
                PlayerStats.game_id == game.id
            ).first()

            if not stat_entry:
                stat_entry = PlayerStats(
                    player_id=db_player.id,
                    game_id=game.id,
                    game_date=game.game_date.date(),
                    opponent=opponent_name
                )
                db.add(stat_entry)

            try:
                stat_entry.minutes_played = float(stats_values[0]) if stats_values[0] != "--" else 0
                stat_entry.rebounds = float(stats_values[6]) if stats_values[6] != "--" else 0
                stat_entry.assists = float(stats_values[7]) if stats_values[7] != "--" else 0
                stat_entry.steals = float(stats_values[8]) if stats_values[8] != "--" else 0
                stat_entry.blocks = float(stats_values[9]) if stats_values[9] != "--" else 0
                stat_entry.points = float(stats_values[13]) if stats_values[13] != "--" else 0
            except Exception as e:
                logger.error(f"Error parsing stats for {name} in game {game.id}: {e}")

    db.flush()

def sync_upcoming_games(days: int = 3):
    """
    Syncs games for today and the next few days.
    """
    now = datetime.utcnow()
    for i in range(days):
        date_to_sync = (now + timedelta(days=i)).strftime("%Y%m%d")
        sync_espn_data(date_to_sync)

if __name__ == "__main__":
    sync_upcoming_games(3)
