"""
Migration script to populate headshot and logo URLs.
Uses NBA CDN and ESPN for imagery.
"""
import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

from app.database import SessionLocal
from app import models

# NBA Team abbreviations to ESPN logo mapping
TEAM_LOGOS = {
    "Atlanta Hawks": "atl",
    "Boston Celtics": "bos",
    "Brooklyn Nets": "bkn",
    "Charlotte Hornets": "cha",
    "Chicago Bulls": "chi",
    "Cleveland Cavaliers": "cle",
    "Dallas Mavericks": "dal",
    "Denver Nuggets": "den",
    "Detroit Pistons": "det",
    "Golden State Warriors": "gs",
    "Houston Rockets": "hou",
    "Indiana Pacers": "ind",
    "LA Clippers": "lac",
    "Los Angeles Lakers": "lal",
    "Memphis Grizzlies": "mem",
    "Miami Heat": "mia",
    "Milwaukee Bucks": "mil",
    "Minnesota Timberwolves": "min",
    "New Orleans Pelicans": "no",
    "New York Knicks": "ny",
    "Oklahoma City Thunder": "okc",
    "Orlando Magic": "orl",
    "Philadelphia 76ers": "phi",
    "Phoenix Suns": "phx",
    "Portland Trail Blazers": "por",
    "Sacramento Kings": "sac",
    "San Antonio Spurs": "sa",
    "Toronto Raptors": "tor",
    "Utah Jazz": "uta",
    "Washington Wizards": "wsh"
}

# NBA Player ID mapping (sample - would need full mapping)
# Using Basketball Reference ID format for CDN
PLAYER_IDS = {
    "LeBron James": "jamesle01",
    "Stephen Curry": "curryst01",
    "Kevin Durant": "duranke01",
    "Giannis Antetokounmpo": "antetgi01",
    "Luka Doncic": "doncilu01",
    "Jayson Tatum": "tatumja01",
    "Nikola Jokic": "jokicni01",
    "Joel Embiid": "embiijo01",
    "Anthony Davis": "davisan02",
    "Devin Booker": "bookede01"
}

def generate_headshot_url(player_name: str) -> str:
    """Generate headshot URL from player name."""
    # Use ESPN headshots (more reliable)
    # Format: first initial + last name
    parts = player_name.split()
    if len(parts) >= 2:
        slug = f"{parts[0].lower()}_{parts[-1].lower()}"
        return f"https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/{slug}.png&w=350&h=254"
    return None

def generate_logo_url(team_name: str) -> str:
    """Generate team logo URL."""
    abbr = TEAM_LOGOS.get(team_name)
    if abbr:
        return f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/{abbr}.png&h=200&w=200"
    return None

def run_migration():
    """Update all teams and players with image URLs."""
    db = SessionLocal()
    
    try:
        # Update Teams
        teams = db.query(models.Team).all()
        updated_teams = 0
        for team in teams:
            if not team.logo_url:
                logo_url = generate_logo_url(team.name)
                if logo_url:
                    team.logo_url = logo_url
                    updated_teams += 1
        
        # Update Players
        players = db.query(models.Player).all()
        updated_players = 0
        for player in players:
            if not player.headshot_url:
                # Use player ID from our mapping if available
                player_id = PLAYER_IDS.get(player.name)
                if player_id:
                    player.headshot_url = f"https://a.espncdn.com/i/headshots/nba/players/full/{player_id}.png"
                else:
                    # Fallback to generated URL
                    player.headshot_url = generate_headshot_url(player.name)
                updated_players += 1
        
        db.commit()
        print(f"✅ Updated {updated_teams} teams with logos")
        print(f"✅ Updated {updated_players} players with headshots")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
