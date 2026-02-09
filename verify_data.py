from app.database import SessionLocal
from app.models import Player, Team, TeamStats, PlayerStats
from sqlalchemy import func

def verify_data():
    db = SessionLocal()
    try:
        player_count = db.query(Player).count()
        team_count = db.query(Team).count()
        team_stats_count = db.query(TeamStats).count()
        player_stats_count = db.query(PlayerStats).count()
        
        print(f"Total Players: {player_count}")
        print(f"Total Teams: {team_count}")
        print(f"Total Team Stats: {team_stats_count}")
        print(f"Total Player Stats: {player_stats_count}")
        
        print("\nSample Team Stats:")
        team_stats = db.query(TeamStats, Team).join(Team).limit(5).all()
        for stats, team in team_stats:
            print(f"{team.name}: {stats.wins}-{stats.losses}, PPG: {stats.ppg}, Opp PPG: {stats.opp_ppg}")
            
        print("\nSample Player Stats:")
        player_stats = db.query(PlayerStats, Player).join(Player).limit(5).all()
        for stats, player in player_stats:
            print(f"{player.name} vs {stats.opponent} on {stats.game_date}: {stats.points} PTS, {stats.rebounds} REB, {stats.assists} AST")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_data()
