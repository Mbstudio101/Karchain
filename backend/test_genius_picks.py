import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import date
from app.analytics.enhanced_genius_picks import get_enhanced_genius_picks

db = SessionLocal()
try:
    # Test the enhanced genius picks system
    print("Testing Enhanced Genius Picks System...")
    
    result = get_enhanced_genius_picks(target_date=date.today(), min_edge=0.03)
    
    print(f"\nFound {result['genius_count']} enhanced genius picks")
    print(f"Features used: {', '.join(result['enhanced_features_used'])}")
    print(f"Data source: {result['data_source']}")
    
    if result['picks']:
        print(f"\nTop 5 picks:")
        for i, pick in enumerate(result['picks'][:5]):
            print(f"{i+1}. {pick['player']} - {pick['pick']} {pick['line']} {pick['prop']}")
            print(f"   EV: {pick['ev']} | Edge: {pick['edge']} | Hit Rate: {pick['hit_rate']}")
            print(f"   Grade: {pick['grade']} | Kelly: {pick['kelly_bet']}")
            print()
    else:
        print("No genius picks found!")
        
    # Let's also check what props exist and their EV calculations
    from app.date_utils import get_gameday_range
    from datetime import datetime
    
    today = date.today()
    start_utc, end_utc = get_gameday_range(today)
    
    props = db.query(models.PlayerProps).join(models.Game).filter(
        models.Game.game_date >= start_utc,
        models.Game.game_date < end_utc
    ).all()
    
    print(f"\nTotal props found for today: {len(props)}")
    
    # Check a few specific players
    lebron_props = [p for p in props if p.player and 'lebron' in p.player.name.lower()]
    luka_props = [p for p in props if p.player and 'luka' in p.player.name.lower()]
    
    print(f"LeBron props: {len(lebron_props)}")
    print(f"Luka props: {len(luka_props)}")
    
    if lebron_props:
        print("\nLeBron props details:")
        for prop in lebron_props[:3]:  # Show first 3
            print(f"  {prop.prop_type}: {prop.line} (Over: {prop.over_odds}, Under: {prop.under_odds})")
            print(f"    Star Rating: {prop.star_rating}, EV: {prop.bp_ev}, Performance: {prop.performance_pct}")
    
finally:
    db.close()