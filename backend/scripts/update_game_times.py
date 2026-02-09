"""
Update existing games with correct dates/times from ESPN NBA schedule.
"""
import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

import requests
from datetime import datetime, timedelta
from app.database import SessionLocal
from app import models

# ESPN API for today's games
def get_espn_schedule():
    """Fetch today's NBA schedule from ESPN API."""
    today = datetime.now().strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        games = []
        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])
            
            home_team = None
            away_team = None
            for c in competitors:
                team_name = c.get("team", {}).get("displayName", "")
                if c.get("homeAway") == "home":
                    home_team = team_name
                else:
                    away_team = team_name
            
            # Parse date from ISO format
            date_str = event.get("date", "")
            game_time = None
            if date_str:
                try:
                    game_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    game_time = datetime.utcnow()
            
            if home_team and away_team:
                games.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "game_time": game_time,
                    "venue": competition.get("venue", {}).get("fullName", ""),
                    "status": event.get("status", {}).get("type", {}).get("description", "")
                })
        
        return games
    except Exception as e:
        print(f"Error fetching ESPN schedule: {e}")
        return []

def update_game_times():
    """Update game times in database from ESPN schedule."""
    db = SessionLocal()
    
    try:
        espn_games = get_espn_schedule()
        print(f"Fetched {len(espn_games)} games from ESPN")
        
        updated = 0
        for eg in espn_games:
            # Find matching game in DB
            home_team = db.query(models.Team).filter(
                models.Team.name.ilike(f"%{eg['home_team'].split()[-1]}%")
            ).first()
            away_team = db.query(models.Team).filter(
                models.Team.name.ilike(f"%{eg['away_team'].split()[-1]}%")
            ).first()
            
            if not home_team or not away_team:
                print(f"  Team not found: {eg['away_team']} @ {eg['home_team']}")
                continue
            
            game = db.query(models.Game).filter(
                models.Game.home_team_id == home_team.id,
                models.Game.away_team_id == away_team.id
            ).first()
            
            if game:
                old_time = game.game_date
                game.game_date = eg['game_time']
                if eg['venue']:
                    game.venue = eg['venue']
                db.commit()
                print(f"  Updated: {eg['away_team']} @ {eg['home_team']}")
                print(f"    Old: {old_time} -> New: {eg['game_time']}")
                updated += 1
            else:
                print(f"  Game not in DB: {eg['away_team']} @ {eg['home_team']}")
        
        print(f"\nUpdated {updated} games with correct times")
        
    finally:
        db.close()

if __name__ == "__main__":
    update_game_times()
