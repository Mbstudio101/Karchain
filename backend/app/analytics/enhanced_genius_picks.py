"""
Enhanced Genius Picks with Reconstructed NBA Data Integration
Uses advanced analytics including clutch performance, tracking metrics, and ML-enhanced predictions.
"""
import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

from app.database import SessionLocal
from app import models
from datetime import datetime, date
from typing import List, Dict, Optional
import numpy as np
from scipy.stats import norm
import math

# Import our reconstructed data integration
try:
    from backend.models.nba_data_integration import NBADataIntegration
except ImportError:
    # Fallback for when running from backend root
    from models.nba_data_integration import NBADataIntegration

class EnhancedGeniusPicks:
    def __init__(self):
        self.nba_integration = NBADataIntegration()
        
    def get_enhanced_player_analytics(self, player_id: str) -> Dict[str, float]:
        """Get comprehensive player analytics including reconstructed data."""
        # Get all features from NBADataIntegration
        features = self.nba_integration.get_player_prediction_features(player_id)
        
        # Extract clutch and tracking data from features
        clutch_score = features.get('clutch_rating', 0.5)
        athletic_score = features.get('athletic_performance', 0.5)
        defensive_score = features.get('defensive_impact', 0.45)
        
        # Calculate consistency score based on clutch usage and efficiency
        clutch_usage = features.get('clutch_pts_per_game', 0.0) / 20.0  # Normalize
        clutch_efg = features.get('clutch_shooting_efficiency', 0.5)
        consistency_score = (clutch_usage * 0.3) + (clutch_efg * 0.7)
        
        return {
            **features,
            'clutch_score': clutch_score,
            'athletic_score': athletic_score,
            'defensive_score': defensive_score,
            'consistency_score': consistency_score,
            'clutch_usage': clutch_usage,
            'clutch_efg': clutch_efg,
            'composite_rating': (clutch_score * 0.4 + athletic_score * 0.3 + defensive_score * 0.2 + consistency_score * 0.1)
        }
    
    def calculate_enhanced_probability(self, player: models.Player, prop_type: str, 
                                     line: float, game_context: Dict = None) -> Dict[str, float]:
        """Calculate enhanced probability using reconstructed data."""
        player_id = str(player.id)
        analytics = self.get_enhanced_player_analytics(player_id)
        
        # Base probability from historical data
        if not player.stats:
            base_prob = 0.5
        else:
            stats = player.stats[:25]  # Larger sample for stability
            hits = 0
            
            for stat in stats:
                if prop_type == 'points':
                    value = stat.points or 0
                elif prop_type == 'rebounds':
                    value = stat.rebounds or 0
                elif prop_type == 'assists':
                    value = stat.assists or 0
                elif prop_type == 'pts+reb+ast':
                    value = (stat.points or 0) + (stat.rebounds or 0) + (stat.assists or 0)
                else:
                    value = 0
                
                if value > line:
                    hits += 1
            
            base_prob = hits / len(stats) if stats else 0.5
        
        # Apply reconstructed data adjustments
        clutch_adjustment = 0.0
        athletic_adjustment = 0.0
        defensive_adjustment = 0.0
        consistency_adjustment = 0.0
        
        # Clutch adjustments
        clutch_score = analytics['clutch_score']
        if game_context and game_context.get('is_close_game', False):
            clutch_adjustment = (clutch_score - 0.5) * 0.15
        
        # Athletic adjustments
        athletic_score = analytics['athletic_score']
        if prop_type in ['points', 'rebounds', 'pts+reb+ast']:
            athletic_adjustment = (athletic_score - 0.5) * 0.10
        
        # Defensive adjustments
        defensive_score = analytics['defensive_score']
        if prop_type in ['points', 'pts+reb+ast']:
            defensive_adjustment = (0.5 - defensive_score) * 0.08  # Better defense = lower probability
        
        # Consistency adjustments
        consistency_score = analytics['consistency_score']
        consistency_adjustment = (consistency_score - 0.5) * 0.05
        
        # Calculate enhanced probability
        enhanced_prob = base_prob + clutch_adjustment + athletic_adjustment + defensive_adjustment + consistency_adjustment
        enhanced_prob = max(0.05, min(0.95, enhanced_prob))  # Bound between 5% and 95%
        
        # Calculate confidence interval using Wilson score
        sample_size = len(player.stats) if player.stats else 1
        z_score = 1.96  # 95% confidence
        
        wilson_ci_low, wilson_ci_high = self.wilson_confidence_interval(
            hits if player.stats else int(base_prob * sample_size), 
            sample_size, 
            z_score
        )
        
        return {
            'probability': enhanced_prob,
            'confidence_interval': (wilson_ci_low, wilson_ci_high),
            'base_probability': base_prob,
            'clutch_adjustment': clutch_adjustment,
            'athletic_adjustment': athletic_adjustment,
            'defensive_adjustment': defensive_adjustment,
            'consistency_adjustment': consistency_adjustment,
            'composite_rating': analytics['composite_rating']
        }
    
    def wilson_confidence_interval(self, successes: int, trials: int, z: float = 1.96) -> tuple:
        """Calculate Wilson confidence interval."""
        if trials == 0:
            return (0.0, 1.0)
        
        p = successes / trials
        n = trials
        
        # Wilson score interval
        center = (p + z*z/(2*n)) / (1 + z*z/n)
        margin = z * math.sqrt((p*(1-p) + z*z/(4*n)) / n) / (1 + z*z/n)
        
        ci_low = max(0.0, center - margin)
        ci_high = min(1.0, center + margin)
        
        return (ci_low, ci_high)
    
    def calculate_enhanced_ev(self, probability: float, odds: int, 
                            confidence: float, composite_rating: float) -> Dict[str, float]:
        """Calculate enhanced expected value with confidence adjustments."""
        # Handle invalid odds
        if odds == 0:
            return {'ev': 0.0, 'edge': 0.0, 'kelly_fraction': 0.0, 'base_ev': 0.0, 'enhanced_ev': 0.0, 'confidence_multiplier': 0.5, 'rating_multiplier': 0.7}
            
        # Base EV calculation
        if odds > 0:
            decimal_odds = 1 + (odds / 100)
        else:
            decimal_odds = 1 + (100 / abs(odds))
        
        base_ev = (probability * decimal_odds * 100) - 100
        
        # Confidence adjustment
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5 to 1.0
        
        # Composite rating adjustment (quality of player)
        rating_multiplier = 0.7 + (composite_rating * 0.3)  # 0.7 to 1.0
        
        # Calculate enhanced EV
        enhanced_ev = base_ev * confidence_multiplier * rating_multiplier
        
        # Calculate edge (EV as percentage of stake)
        edge = enhanced_ev / 100
        
        # Kelly criterion calculation
        kelly_fraction = self.kelly_criterion(probability, odds, confidence)
        
        return {
            'ev': enhanced_ev,
            'edge': edge,
            'kelly_fraction': kelly_fraction,
            'base_ev': base_ev,
            'confidence_multiplier': confidence_multiplier,
            'rating_multiplier': rating_multiplier
        }
    
    def kelly_criterion(self, probability: float, odds: int, confidence: float = 1.0) -> float:
        """Calculate Kelly criterion with confidence adjustment."""
        if probability <= 0 or probability >= 1:
            return 0.0
        
        # Convert American odds to decimal
        if odds > 0:
            decimal = 1 + (odds / 100)
        else:
            decimal = 1 + (100 / abs(odds))
        
        b = decimal - 1  # Net odds
        q = 1 - probability
        
        # Kelly formula with confidence adjustment
        kelly = (b * probability - q) / b
        adjusted_kelly = kelly * confidence * 0.5  # Half Kelly for safety
        
        return max(0, min(adjusted_kelly, 0.05))  # Cap at 5%
    
    def get_enhanced_genius_picks(self, target_date: date = None, min_edge: float = 0.03) -> Dict:
        """Get enhanced genius picks using reconstructed NBA data."""
        if target_date is None:
            target_date = date.today()
        
        db = SessionLocal()
        
        try:
            from ..date_utils import get_gameday_range
            
            start_utc, end_utc = get_gameday_range(target_date)
            
            # Get all props for the date
            props = db.query(models.PlayerProps).join(models.Game).filter(
                models.Game.game_date >= start_utc,
                models.Game.game_date < end_utc
            ).all()
            
            genius_picks = []
            
            for prop in props:
                player = db.query(models.Player).filter(models.Player.id == prop.player_id).first()
                if not player or not player.stats or len(player.stats) < 5:
                    continue
                
                # Get game context
                game_context = {}
                if prop.game_id:
                    game = db.query(models.Game).filter(models.Game.id == prop.game_id).first()
                    if game:
                        # Determine if it's expected to be a close game
                        home_team_stats = db.query(models.TeamStats).filter(
                            models.TeamStats.team_id == game.home_team_id
                        ).first()
                        away_team_stats = db.query(models.TeamStats).filter(
                            models.TeamStats.team_id == game.away_team_id
                        ).first()
                        
                        if home_team_stats and away_team_stats:
                            point_diff = abs(home_team_stats.ppg - away_team_stats.ppg)
                            game_context['is_close_game'] = point_diff < 5
                
                # Calculate enhanced probability for both sides
                over_analysis = self.calculate_enhanced_probability(
                    player, prop.prop_type, prop.line, game_context
                )
                under_analysis = self.calculate_enhanced_probability(
                    player, prop.prop_type, prop.line, game_context
                )
                
                # Calculate EV for both sides
                over_ev_data = self.calculate_enhanced_ev(
                    over_analysis['probability'], 
                    prop.over_odds,
                    (over_analysis['confidence_interval'][1] - over_analysis['confidence_interval'][0]),
                    over_analysis['composite_rating']
                )
                
                under_ev_data = self.calculate_enhanced_ev(
                    1 - under_analysis['probability'],  # Under probability
                    prop.under_odds,
                    (under_analysis['confidence_interval'][1] - under_analysis['confidence_interval'][0]),
                    under_analysis['composite_rating']
                )
                
                # Determine best side
                if over_ev_data['ev'] > under_ev_data['ev'] and over_ev_data['edge'] >= min_edge:
                    best_side = 'OVER'
                    best_odds = prop.over_odds
                    best_ev = over_ev_data
                    best_analysis = over_analysis
                elif under_ev_data['ev'] > over_ev_data['ev'] and under_ev_data['edge'] >= min_edge:
                    best_side = 'UNDER'
                    best_odds = prop.under_odds
                    best_ev = under_ev_data
                    best_analysis = under_analysis
                else:
                    continue  # Skip if no good edge
                
                # Determine streak status
                streak_status = self.determine_streak_status(player, prop.prop_type, prop.line)
                
                # Calculate grade
                grade = self.calculate_grade(
                    best_ev['ev'], 
                    best_ev['edge'], 
                    best_analysis['composite_rating'],
                    streak_status
                )
                
                # Build enhanced reasoning
                reasoning_parts = []
                
                if best_analysis['clutch_adjustment'] != 0:
                    clutch_adj = best_analysis['clutch_adjustment']
                    reasoning_parts.append(f"Clutch: {'+' if clutch_adj > 0 else ''}{clutch_adj:.1%}")
                
                if best_analysis['athletic_adjustment'] != 0:
                    athletic_adj = best_analysis['athletic_adjustment']
                    reasoning_parts.append(f"Athletic: {'+' if athletic_adj > 0 else ''}{athletic_adj:.1%}")
                
                if best_analysis['composite_rating'] > 0.7:
                    reasoning_parts.append(f"Elite composite rating ({best_analysis['composite_rating']:.1%})")
                
                reasoning = f"Enhanced analysis: {best_analysis['probability']*100:.1f}% hit rate"
                if reasoning_parts:
                    reasoning += f" • {' • '.join(reasoning_parts)}"
                
                genius_picks.append({
                    'player': player.name,
                    'prop': prop.prop_type.replace('+', ' + ').title(),
                    'line': prop.line,
                    'pick': best_side,
                    'odds': best_odds,
                    'ev': f"+${round(best_ev['ev'], 2)}",
                    'edge': f"+{round(best_ev['edge'] * 100, 1)}%",
                    'kelly_bet': f"${round(best_ev['kelly_fraction'] * 1000, 2)}",
                    'hit_rate': f"{round(best_analysis['probability'] * 100, 1)}%",
                    'streak': streak_status,
                    'confidence_range': f"{round(best_analysis['confidence_interval'][0] * 100, 0)}-{round(best_analysis['confidence_interval'][1] * 100, 0)}%",
                    'grade': grade,
                    'composite_rating': best_analysis['composite_rating'],
                    'reasoning': reasoning,
                    'clutch_adjusted': best_analysis['clutch_adjustment'] != 0,
                    'athletic_adjusted': best_analysis['athletic_adjustment'] != 0
                })
            
            # Sort by EV
            genius_picks.sort(key=lambda x: float(x['ev'].replace("+$", "")), reverse=True)
            
            return {
                'genius_count': len(genius_picks),
                'picks': genius_picks[:15],  # Top 15 picks
                'enhanced_features_used': ['clutch_performance', 'athletic_metrics', 'defensive_impact', 'consistency_scoring'],
                'data_source': 'Reconstructed NBA Analytics'
            }
            
        finally:
            db.close()
    
    def determine_streak_status(self, player: models.Player, prop_type: str, line: float) -> str:
        """Determine streak status based on recent performance."""
        if not player.stats:
            return "neutral"
        
        recent_games = player.stats[:8]  # Last 8 games
        hits = 0
        
        for stat in recent_games:
            if prop_type == 'points':
                value = stat.points or 0
            elif prop_type == 'rebounds':
                value = stat.rebounds or 0
            elif prop_type == 'assists':
                value = stat.assists or 0
            elif prop_type == 'pts+reb+ast':
                value = (stat.points or 0) + (stat.rebounds or 0) + (stat.assists or 0)
            else:
                value = 0
            
            if value > line:
                hits += 1
        
        hit_rate = hits / len(recent_games) if recent_games else 0.5
        
        if hit_rate >= 0.75:  # 6+ out of 8
            return "hot"
        elif hit_rate <= 0.25:  # 2 or fewer out of 8
            return "cold"
        else:
            return "neutral"
    
    def calculate_grade(self, ev: float, edge: float, composite_rating: float, streak: str) -> str:
        """Calculate grade based on multiple factors."""
        # Base grade from EV and edge
        if ev > 8 and edge > 0.12 and composite_rating > 0.8 and streak == "hot":
            return "S"
        elif ev > 5 and edge > 0.08 and composite_rating > 0.7:
            return "A+"
        elif ev > 3 and edge > 0.05 and composite_rating > 0.6:
            return "A"
        elif ev > 2 and edge > 0.03 and composite_rating > 0.5:
            return "B+"
        else:
            return "B"

# Convenience function
def get_enhanced_genius_picks(target_date: date = None, min_edge: float = 0.03) -> Dict:
    """Get enhanced genius picks using reconstructed NBA data."""
    genius_system = EnhancedGeniusPicks()
    return genius_system.get_enhanced_genius_picks(target_date, min_edge)

if __name__ == "__main__":
    # Test the enhanced genius picks system
    print("Testing Enhanced Genius Picks System...")
    
    result = get_enhanced_genius_picks()
    
    print(f"\nFound {result['genius_count']} enhanced genius picks")
    print(f"Features used: {', '.join(result['enhanced_features_used'])}")
    print(f"Data source: {result['data_source']}")
    
    if result['picks']:
        print(f"\nTop pick: {result['picks'][0]['player']} - {result['picks'][0]['pick']} {result['picks'][0]['line']}")
        print(f"EV: {result['picks'][0]['ev']} | Edge: {result['picks'][0]['edge']}%")