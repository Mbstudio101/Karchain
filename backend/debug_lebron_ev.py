import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models
from datetime import date
from app.date_utils import get_gameday_range
from app.analytics.enhanced_genius_picks import EnhancedGeniusPicks

db = SessionLocal()
try:
    today = date.today()
    start_utc, end_utc = get_gameday_range(today)
    
    # Get LeBron's props
    lebron = db.query(models.Player).filter(models.Player.name.ilike("%lebron%")).first()
    if lebron:
        print(f"LeBron James (ID: {lebron.id}) - Team: {lebron.team.name if lebron.team else 'No team'}")
        
        lebron_props = db.query(models.PlayerProps).filter(
            models.PlayerProps.player_id == lebron.id,
            models.PlayerProps.timestamp >= start_utc,
            models.PlayerProps.timestamp < end_utc
        ).all()
        
        print(f"LeBron has {len(lebron_props)} props today")
        
        genius = EnhancedGeniusPicks()
        
        for prop in lebron_props[:3]:  # Test first 3 props
            print(f"\nTesting prop: {prop.prop_type} {prop.line}")
            print(f"  Over odds: {prop.over_odds}, Under odds: {prop.under_odds}")
            print(f"  Star rating: {prop.star_rating}, BP EV: {prop.bp_ev}, Performance: {prop.performance_pct}")
            
            # Test the enhanced probability calculation
            try:
                over_analysis = genius.calculate_enhanced_probability(lebron, prop.prop_type, prop.line)
                print(f"  Over probability: {over_analysis['probability']:.3f}")
                print(f"  Base probability: {over_analysis['base_probability']:.3f}")
                print(f"  Confidence interval: {over_analysis['confidence_interval']}")
                print(f"  Composite rating: {over_analysis['composite_rating']:.3f}")
                
                # Test EV calculation for over
                over_ev_data = genius.calculate_enhanced_ev(
                    over_analysis['probability'], 
                    prop.over_odds,
                    (over_analysis['confidence_interval'][1] - over_analysis['confidence_interval'][0]),
                    over_analysis['composite_rating']
                )
                
                print(f"  Over EV: ${over_ev_data['ev']:.2f}, Edge: {over_ev_data['edge']:.3f}")
                
                # Test under probability and EV
                under_analysis = genius.calculate_enhanced_probability(lebron, prop.prop_type, prop.line)
                under_ev_data = genius.calculate_enhanced_ev(
                    1 - under_analysis['probability'],  # Under probability
                    prop.under_odds,
                    (under_analysis['confidence_interval'][1] - under_analysis['confidence_interval'][0]),
                    under_analysis['composite_rating']
                )
                
                print(f"  Under EV: ${under_ev_data['ev']:.2f}, Edge: {under_ev_data['edge']:.3f}")
                
                # Check if either side meets the min_edge requirement (0.03 = 3%)
                min_edge = 0.03
                if over_ev_data['edge'] >= min_edge:
                    print(f"  ✓ OVER meets min_edge requirement!")
                elif under_ev_data['edge'] >= min_edge:
                    print(f"  ✓ UNDER meets min_edge requirement!")
                else:
                    print(f"  ✗ Neither side meets min_edge requirement of {min_edge}")
                    
            except Exception as e:
                print(f"  Error in calculation: {e}")
                import traceback
                traceback.print_exc()
    
finally:
    db.close()