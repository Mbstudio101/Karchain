"""
Test the EnhancedGeniusPicks system with the new EnhancedNBAApiClient
"""

import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

from app.analytics.enhanced_genius_picks import EnhancedGeniusPicks
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_genius_picks():
    """Test the enhanced genius picks system"""
    print("🚀 Testing Enhanced Genius Picks System...")
    
    try:
        # Initialize the system
        genius_picks = EnhancedGeniusPicks()
        print("✅ EnhancedGeniusPicks initialized successfully")
        
        # Test with LeBron James (ID: 2544)
        player_id = "2544"
        print(f"\n📊 Testing player analytics for LeBron James (ID: {player_id})")
        
        analytics = genius_picks.get_enhanced_player_analytics(player_id)
        print(f"✅ Got analytics for LeBron James:")
        print(f"   - Clutch Score: {analytics['clutch_score']:.3f}")
        print(f"   - Athletic Score: {analytics['athletic_score']:.3f}")
        print(f"   - Defensive Score: {analytics['defensive_score']:.3f}")
        print(f"   - Composite Rating: {analytics['composite_rating']:.3f}")
        
        # Show data source
        if 'season_stats' in analytics:
            season_stats = analytics['season_stats']
            print(f"   - Season Stats (PPG/RPG/APG): {season_stats.get('ppg', 0):.1f}/{season_stats.get('rpg', 0):.1f}/{season_stats.get('apg', 0):.1f}")
            print(f"   - Data Source: {season_stats.get('data_source', 'unknown')}")
        
        print("\n✅ Enhanced Genius Picks system is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_genius_picks()