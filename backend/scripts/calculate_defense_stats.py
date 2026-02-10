import sys
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import PlayerStats, Player, Team, TeamDefenseStats
from app.database import DATABASE_URL

def calculate_defense_stats():
    print("Connecting to DB...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    print("Fetching player stats...")
    # Get all player stats with position and opponent info
    # We join Player to get the position
    results = db.query(
        PlayerStats.points,
        PlayerStats.opponent,
        Player.position
    ).join(Player).all()

    if not results:
        print("No stats found.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(results, columns=["points", "opponent", "position"])
    
    # Clean position (some might be "G-F", etc.)
    # Simplify to PG, SG, SF, PF, C
    def simplify_pos(pos):
        if not pos: return "Unknown"
        if "G" in pos: return "PG" # broad simplification
        if "C" in pos: return "C"
        if "F" in pos: return "SF"
        return pos

    df["simple_pos"] = df["position"].apply(simplify_pos)
    
    # Group by Opponent (Team) and Position
    # Calculate Avg Points Allowed
    defense_stats = df.groupby(["opponent", "simple_pos"])["points"].mean().reset_index()
    
    # Pivot: Index=Opponent, Columns=Position, Values=Points
    pivot = defense_stats.pivot(index="opponent", columns="simple_pos", values="points")
    
    # Calculate Rankings (Ascending, lower points is better)
    rankings = pivot.rank(ascending=True)
    
    # Map Abbr to Full Name
    TEAM_ABBR_MAP = {
        "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets", "CHA": "Charlotte Hornets",
        "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers", "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets",
        "DET": "Detroit Pistons", "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
        "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies", "MIA": "Miami Heat",
        "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves", "NOP": "New Orleans Pelicans", "NYK": "New York Knicks",
        "OKC": "Oklahoma City Thunder", "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
        "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs", "TOR": "Toronto Raptors",
        "UTA": "Utah Jazz", "WAS": "Washington Wizards"
    }

    print("Saving defensive stats...")
    
    # Iterate through teams in DB and update/insert stats
    teams = db.query(Team).all()
    
    for team in teams:
        # Find abbreviation
        abbr = None
        for k, v in TEAM_ABBR_MAP.items():
            if v == team.name:
                abbr = k
                break
        
        if not abbr:
            continue
            
        if abbr not in pivot.index:
            continue
            
        # Get stats from pivot
        team_stats = pivot.loc[abbr]
        
        # Create or Update TeamDefenseStats
        defense_entry = db.query(TeamDefenseStats).filter(TeamDefenseStats.team_id == team.id).first()
        if not defense_entry:
            defense_entry = TeamDefenseStats(team_id=team.id)
            db.add(defense_entry)
            
        # Update columns (assuming we added these columns to model)
        # In models.py we added pg_points_rank etc.
        # But here we calculated raw points allowed.
        # We should probably store the RANK.
        
        # Let's get ranks
        rank_row = rankings.loc[abbr]
        
        # Map simple_pos to model columns
        # Model has: pg_points_rank, sg_points_rank, sf_points_rank, pf_points_rank, c_points_rank
        # simple_pos has: PG, SG, SF, PF, C (hopefully)
        
        if "PG" in rank_row: defense_entry.pg_points_rank = int(rank_row["PG"])
        if "SG" in rank_row: defense_entry.sg_points_rank = int(rank_row["SG"])
        if "SF" in rank_row: defense_entry.sf_points_rank = int(rank_row["SF"])
        if "PF" in rank_row: defense_entry.pf_points_rank = int(rank_row["PF"])
        if "C" in rank_row: defense_entry.c_points_rank = int(rank_row["C"])
        
    db.commit()
    print("Defensive stats calculation complete and saved.")

if __name__ == "__main__":
    calculate_defense_stats()
