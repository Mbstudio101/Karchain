
import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import PlayerProps, Player, Team, Game
from app.analytics.advanced_stats import analyze_prop, BetConfidence
from datetime import datetime, timedelta

# Check today's props in database
today = datetime.utcnow().date()
tomorrow = today + timedelta(days=1)

db = SessionLocal()

def test_analysis(player_name):
    print(f"\nAnalyzing props for {player_name}...")
    
    props = db.query(PlayerProps).join(Player).filter(
        Player.name.ilike(f"%{player_name}%"),
        PlayerProps.timestamp >= today,
        PlayerProps.timestamp < tomorrow
    ).all()
    
    if not props:
        print("No props found.")
        return

    for prop in props:
        print(f"\n--- {prop.prop_type} line: {prop.line} ---")
        
        # We need historical stats to run analysis
        # For this debug script, we'll just check if we can even get the stats
        # The analyze_prop function needs 'historical_stats' which is a list of values
        
        # Let's try to simulate what the recommendation engine does
        # It fetches stats from PlayerStats
        
        # This is a simplified check - we just want to see if the prop would pass the filter
        print(f"  Odds: Over {prop.over_odds}, Under {prop.under_odds}")
        
        # Check if odds are valid
        if prop.over_odds == 0 or prop.under_odds == 0:
            print("  ❌ INVALID ODDS (0)")
            continue
            
        # Check if we have a game attached
        if not prop.game_id:
            print("  ❌ NO GAME ID")
            continue
            
        print(f"  Game ID: {prop.game_id}")
        
        # We can't easily run the full analyze_prop here without mocking a lot of data
        # But we can check if the data required for analysis exists
        
        # Check player stats count
        stats_count = len(prop.player.stats)
        print(f"  Historical stats available: {stats_count} games")
        
        if stats_count < 5:
            print("  ⚠️ LOW DATA: Less than 5 games of history")

try:
    test_analysis("LeBron")
    test_analysis("Luka")
    
finally:
    db.close()