
import logging
from sqlalchemy.orm import Session
from app import models
from app.database import SessionLocal, engine

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
