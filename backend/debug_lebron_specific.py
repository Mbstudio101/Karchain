import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import date
from app.date_utils import get_gameday_range

db = SessionLocal()
try:
    today = date.today()
    start_utc, end_utc = get_gameday_range(today)
    
    # Get all players with "LeBron" in name
    lebron_players = db.query(models.Player).filter(
        models.Player.name.ilike("%lebron%")
    ).all()
    
    print(f"Players with 'LeBron' in name: {len(lebron_players)}")
    for player in lebron_players:
        print(f"  ID: {player.id}, Name: '{player.name}', Team: {player.team.name if player.team else 'No team'}")
        
        # Check if this player has props
        props = db.query(models.PlayerProps).filter(
            models.PlayerProps.player_id == player.id,
            models.PlayerProps.timestamp >= start_utc,
            models.PlayerProps.timestamp < end_utc
        ).all()
        
        print(f"    Props today: {len(props)}")
        if props:
            for prop in props[:2]:  # Show first 2
                print(f"      {prop.prop_type}: {prop.line} (Over: {prop.over_odds}, Under: {prop.under_odds})")
                print(f"        Game ID: {prop.game_id}, Timestamp: {prop.timestamp}")
        print()
    
    # Let's also check the NBA data integration
    try:
        from app.analytics.enhanced_genius_picks import EnhancedGeniusPicks
        genius = EnhancedGeniusPicks()
        
        if lebron_players:
            lebron = lebron_players[0]
            print(f"Testing NBA data integration for {lebron.name} (ID: {lebron.id}):")
            
            # Check if NBA data integration can find this player
            try:
                analytics = genius.get_enhanced_player_analytics(str(lebron.id))
                print(f"  Found analytics data: {len(analytics)} features")
                print(f"  Clutch score: {analytics.get('clutch_score', 'N/A')}")
                print(f"  Composite rating: {analytics.get('composite_rating', 'N/A')}")
            except Exception as e:
                print(f"  Error getting analytics: {e}")
    
    except ImportError as e:
        print(f"Could not import NBA data integration: {e}")
    
finally:
    db.close()