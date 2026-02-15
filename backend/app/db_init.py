
import logging
from sqlalchemy.orm import Session
from app import models
from app.database import SessionLocal, engine
from app.player_identity_sync import backfill_player_identity_and_media

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session):
    """
    Initialize the database with required data.
    """
    logger.info("Initializing database...")
    
    # Check if teams exist
    teams_count = db.query(models.Team).count()
    if teams_count == 0:
        logger.info("No teams found. Creating NBA teams...")
        create_nba_teams(db)
    else:
        logger.info(f"Found {teams_count} teams in database.")

    # Backfill player identity/media once data exists.
    players_count = db.query(models.Player).count()
    if players_count > 0:
        missing_headshots = db.query(models.Player).filter(
            (models.Player.headshot_url.is_(None)) | (models.Player.headshot_url == "")
        ).count()
        missing_team_ids = db.query(models.Player).filter(models.Player.team_id.is_(None)).count()
        external_team_ids = db.query(models.Player).filter(models.Player.team_id >= 1000000000).count()

        if missing_headshots > 0 or missing_team_ids > 0 or external_team_ids > 0:
            logger.info(
                "Running player identity/media backfill (missing_headshots=%s, missing_team_ids=%s, external_team_ids=%s)...",
                missing_headshots,
                missing_team_ids,
                external_team_ids,
            )
            result = backfill_player_identity_and_media(db)
            logger.info("Player backfill done: %s", result)

def create_nba_teams(db: Session):
    """
    Populate the database with NBA teams.
    """
    nba_teams = [
        'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
        'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
        'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
        'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
        'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
        'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
        'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
        'Utah Jazz', 'Washington Wizards'
    ]
    
    count = 0
    for team_name in nba_teams:
        existing = db.query(models.Team).filter(models.Team.name == team_name).first()
        if not existing:
            team = models.Team(name=team_name, sport='NBA')
            db.add(team)
            count += 1
    
    db.commit()
    logger.info(f"Created {count} new teams.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
