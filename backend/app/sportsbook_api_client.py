"""
Sportsbook API Client - Aggregates odds from multiple sportsbooks
Provides real-time odds comparison and best line selection
"""
import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SportsbookOdds:
    """Represents odds from a specific sportsbook"""
    sportsbook: str
    over_odds: float
    under_odds: float
    timestamp: datetime

class SportsbookAggregator:
    """Aggregates odds from multiple sportsbook APIs"""
    
    def __init__(self):
        self.sportsbooks = {
            'draftkings': self.get_draftkings_odds,
            'fanduel': self.get_fanduel_odds,
            'betmgm': self.get_betmgm_odds,
            'caesars': self.get_caesars_odds,
            'pointsbet': self.get_pointsbet_odds
        }
        
    def get_draftkings_odds(self, player_name: str, prop_type: str, line: float) -> Optional[SportsbookOdds]:
        """Get DraftKings odds for a player prop"""
        try:
            # This would be a real API call to DraftKings
            # For now, using simulated data based on market standards
            base_over = -110
            base_under = -110
            
            # Adjust based on line movement and player popularity
            if 'lebron' in player_name.lower() or 'doncic' in player_name.lower():
                base_over = -115  # Popular players get worse odds
                base_under = -105
            
            return SportsbookOdds(
                sportsbook='DraftKings',
                over_odds=base_over,
                under_odds=base_under,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting DraftKings odds for {player_name}: {e}")
            return None
    
    def get_fanduel_odds(self, player_name: str, prop_type: str, line: float) -> Optional[SportsbookOdds]:
        """Get FanDuel odds for a player prop"""
        try:
            # Simulated FanDuel odds
            base_over = -112
            base_under = -108
            
            # FanDuel often has slightly different lines for stars
            if 'jokic' in player_name.lower() or 'giannis' in player_name.lower():
                base_over = -118
                base_under = -102
            
            return SportsbookOdds(
                sportsbook='FanDuel',
                over_odds=base_over,
                under_odds=base_under,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting FanDuel odds for {player_name}: {e}")
            return None
    
    def get_betmgm_odds(self, player_name: str, prop_type: str, line: float) -> Optional[SportsbookOdds]:
        """Get BetMGM odds for a player prop"""
        try:
            # Simulated BetMGM odds
            base_over = -108
            base_under = -112
            
            # BetMGM often has competitive odds
            return SportsbookOdds(
                sportsbook='BetMGM',
                over_odds=base_over,
                under_odds=base_under,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting BetMGM odds for {player_name}: {e}")
            return None
    
    def get_caesars_odds(self, player_name: str, prop_type: str, line: float) -> Optional[SportsbookOdds]:
        """Get Caesars odds for a player prop"""
        try:
            # Simulated Caesars odds
            base_over = -110
            base_under = -110
            
            return SportsbookOdds(
                sportsbook='Caesars',
                over_odds=base_over,
                under_odds=base_under,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting Caesars odds for {player_name}: {e}")
            return None
    
    def get_pointsbet_odds(self, player_name: str, prop_type: str, line: float) -> Optional[SportsbookOdds]:
        """Get PointsBet odds for a player prop"""
        try:
            # Simulated PointsBet odds
            base_over = -105
            base_under = -115
            
            return SportsbookOdds(
                sportsbook='PointsBet',
                over_odds=base_over,
                under_odds=base_under,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting PointsBet odds for {player_name}: {e}")
            return None
    
    def get_all_odds(self, player_name: str, prop_type: str, line: float) -> Dict[str, SportsbookOdds]:
        """Get odds from all available sportsbooks"""
        all_odds = {}
        
        for sportsbook_name, odds_func in self.sportsbooks.items():
            odds = odds_func(player_name, prop_type, line)
            if odds:
                all_odds[sportsbook_name] = odds
        
        return all_odds
    
    def get_best_odds(self, player_name: str, prop_type: str, line: float) -> Optional[Dict[str, SportsbookOdds]]:
        """Get the best over and under odds across all sportsbooks"""
        all_odds = self.get_all_odds(player_name, prop_type, line)
        
        if not all_odds:
            return None
        
        best_over = None
        best_under = None
        best_over_odds = float('-inf')
        best_under_odds = float('-inf')
        
        for sportsbook_name, odds in all_odds.items():
            # For over bets, we want the highest (least negative) odds
            if odds.over_odds > best_over_odds:
                best_over_odds = odds.over_odds
                best_over = odds
            
            # For under bets, we want the highest (least negative) odds
            if odds.under_odds > best_under_odds:
                best_under_odds = odds.under_odds
                best_under = odds
        
        if best_over and best_under:
            return {
                'over': best_over,
                'under': best_under
            }
        
        return None
    
    def get_all_player_props(self) -> Dict[str, Dict]:
        """Get all available player props from all sportsbooks"""
        # This would aggregate all available props from all sportsbooks
        # For now, returning empty dict - would be populated by real API calls
        return {}

# Global instance
_sportsbook_aggregator = None

def get_sportsbook_aggregator() -> SportsbookAggregator:
    """Get the global sportsbook aggregator instance"""
    global _sportsbook_aggregator
    if _sportsbook_aggregator is None:
        _sportsbook_aggregator = SportsbookAggregator()
    return _sportsbook_aggregator