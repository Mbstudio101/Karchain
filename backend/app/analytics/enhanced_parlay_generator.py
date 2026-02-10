"""
Enhanced AI Parlay Generator with Reconstructed NBA Data Integration
Integrates clutch performance, tracking metrics, and advanced analytics for optimal picks.
"""
import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

from app.database import SessionLocal
from app import models
from datetime import datetime
from typing import List, Tuple, Dict
import random
import numpy as np
from scipy.stats import norm

# Import our reconstructed data integration
try:
    from backend.models.nba_data_integration import NBADataIntegration
except ImportError:
    # Fallback for when running from backend root
    from models.nba_data_integration import NBADataIntegration

class EnhancedParlayGenerator:
    def __init__(self):
        self.nba_integration = NBADataIntegration()
        
    def get_enhanced_player_features(self, player_id: str) -> Dict[str, float]:
        """Get enhanced player features including reconstructed data."""
        # Get all features from NBADataIntegration
        features = self.nba_integration.get_player_prediction_features(player_id)
        
        # Enhanced features already include clutch and tracking data
        enhanced_features = {
            **features,
            'clutch_performance': features.get('clutch_rating', 0.5),
            'clutch_usage': features.get('clutch_pts_per_game', 0.0) / 20.0,  # Normalize to 0-1
            'clutch_efg': features.get('clutch_shooting_efficiency', 0.5),
            'defensive_impact': features.get('defensive_impact', 0.45),
            'speed_score': features.get('speed_factor', 4.0 / 6.0),
            'distance_efficiency': features.get('distance_factor', 2.5 / 5.0),
            'athletic_composite': features.get('athletic_performance', 0.5),
        }
        
        return enhanced_features
    
    def calculate_clutch_adjusted_hit_rate(self, player: models.Player, prop_type: str, line: float, 
                                         game_context: Dict = None) -> float:
        """Calculate hit rate adjusted for clutch performance and game context."""
        if not player.stats:
            return 0.5
        
        # Get enhanced features
        features = self.get_enhanced_player_features(str(player.id))
        
        # Base hit rate calculation
        stats = player.stats[:20]  # Last 20 games for larger sample
        hits = 0
        clutch_hits = 0
        total_clutch_games = 0
        
        for stat in stats:
            # Basic hit calculation
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
                
            # Clutch performance adjustment
            if game_context and game_context.get('is_clutch_time', False):
                clutch_performance = features['clutch_performance']
                clutch_multiplier = 1.0 + (clutch_performance - 0.5) * 0.3
                if value > line * clutch_multiplier:
                    clutch_hits += 1
                total_clutch_games += 1
        
        base_hit_rate = hits / len(stats) if stats else 0.5
        
        # Apply clutch adjustment if relevant
        if total_clutch_games > 0 and game_context and game_context.get('is_clutch_time', False):
            clutch_hit_rate = clutch_hits / total_clutch_games
            # Weight clutch performance more heavily in clutch situations
            adjusted_hit_rate = (base_hit_rate * 0.4) + (clutch_hit_rate * 0.6)
        else:
            adjusted_hit_rate = base_hit_rate
        
        # Apply defensive impact adjustment
        defensive_impact = features['defensive_impact']
        if prop_type in ['points', 'pts+reb+ast']:
            # Better defense = lower hit rate for offensive props
            defensive_adjustment = (0.45 - defensive_impact) * 0.2
            adjusted_hit_rate += defensive_adjustment
        
        # Apply athletic composite adjustment
        athletic_score = features['athletic_composite']
        athletic_adjustment = (athletic_score - 0.5) * 0.15
        adjusted_hit_rate += athletic_adjustment
        
        return max(0.1, min(0.9, adjusted_hit_rate))  # Bound between 10% and 90%
    
    def calculate_enhanced_edge(self, odds: float, probability: float, features: Dict[str, float]) -> float:
        """Calculate edge with enhanced features consideration."""
        # Handle invalid odds
        if odds == 0:
            return 0.0
            
        # Base edge calculation
        if odds > 0:
            decimal_odds = 1 + (odds / 100)
        else:
            decimal_odds = 1 + (100 / abs(odds))
        
        implied_prob = 1 / decimal_odds
        base_edge = probability - implied_prob
        
        # Enhance edge with additional factors
        clutch_factor = features.get('clutch_performance', 0.5)
        athletic_factor = features.get('athletic_composite', 0.5)
        
        # Confidence multiplier based on feature quality
        confidence_multiplier = 1.0
        if clutch_factor > 0.7:
            confidence_multiplier += 0.1
        if athletic_factor > 0.7:
            confidence_multiplier += 0.05
        
        enhanced_edge = base_edge * confidence_multiplier
        
        return enhanced_edge
    
    def get_enhanced_prop_bets(self, db, limit: int = 15) -> List[Dict]:
        """Get player props with enhanced analysis using reconstructed data."""
        enhanced_bets = []
        
        # Get all available props
        props = db.query(models.PlayerProps).all()
        
        for prop in props:
            player = db.query(models.Player).filter(models.Player.id == prop.player_id).first()
            if not player or not player.stats or len(player.stats) < 5:
                continue
            
            # Get enhanced features
            features = self.get_enhanced_player_features(str(player.id))
            
            # Determine game context
            game_context = {}
            if prop.game_id:
                game = db.query(models.Game).filter(models.Game.id == prop.game_id).first()
                if game:
                    # Check if this is a clutch-time game (close score expected)
                    home_features = self.get_enhanced_player_features(str(game.home_team_id))
                    away_features = self.get_enhanced_player_features(str(game.away_team_id))
                    
                    # Simple clutch prediction based on team competitiveness
                    competitiveness = abs(home_features.get('clutch_performance', 0.5) - 
                                        away_features.get('clutch_performance', 0.5))
                    game_context['is_clutch_time'] = competitiveness < 0.2
            
            # Calculate enhanced hit rate
            hit_rate = self.calculate_clutch_adjusted_hit_rate(
                player, prop.prop_type, prop.line, game_context
            )
            
            # Calculate enhanced edges
            over_edge = self.calculate_enhanced_edge(prop.over_odds, hit_rate, features)
            under_edge = self.calculate_enhanced_edge(prop.under_odds, 1 - hit_rate, features)
            
            # Enhanced reasoning with reconstructed data
            reasoning_parts = []
            
            if features['clutch_performance'] > 0.6:
                reasoning_parts.append(f"Strong clutch performer ({features['clutch_performance']:.1%})")
            elif features['clutch_performance'] < 0.4:
                reasoning_parts.append(f"Struggles in clutch ({features['clutch_performance']:.1%})")
                
            if features['athletic_composite'] > 0.7:
                reasoning_parts.append(f"Elite athleticism ({features['athletic_composite']:.1%})")
            
            if features['defensive_impact'] < 0.4:
                reasoning_parts.append("Elite defensive impact")
            
            reasoning = f"{player.name} hits {prop.prop_type} in {hit_rate*100:.0f}% of games"
            if reasoning_parts:
                reasoning += f" • {' • '.join(reasoning_parts)}"
            
            # Add over bet if edge is significant
            if over_edge > 0.04:  # 4%+ edge threshold
                enhanced_bets.append({
                    'type': 'prop',
                    'player': player.name,
                    'prop_type': prop.prop_type,
                    'pick': 'OVER',
                    'line': prop.line,
                    'odds': prop.over_odds,
                    'hit_rate': hit_rate,
                    'edge': over_edge,
                    'features': features,
                    'reasoning': reasoning,
                    'confidence_score': hit_rate + (over_edge * 0.5)  # Combined confidence
                })
            
            # Add under bet if edge is significant
            if under_edge > 0.04:
                enhanced_bets.append({
                    'type': 'prop',
                    'player': player.name,
                    'prop_type': prop.prop_type,
                    'pick': 'UNDER',
                    'line': prop.line,
                    'odds': prop.under_odds,
                    'hit_rate': 1 - hit_rate,
                    'edge': under_edge,
                    'features': features,
                    'reasoning': f"{player.name} stays under {prop.line} {(1-hit_rate)*100:.0f}% of games",
                    'confidence_score': (1 - hit_rate) + (under_edge * 0.5)
                })
        
        # Sort by confidence score and return top bets
        enhanced_bets.sort(key=lambda x: x['confidence_score'], reverse=True)
        return enhanced_bets[:limit]
    
    def get_enhanced_game_bets(self, db, limit: int = 8) -> List[Dict]:
        """Get game bets with enhanced team analysis."""
        enhanced_games = []
        
        # Get recommendations with high confidence
        recommendations = db.query(models.Recommendation).order_by(
            models.Recommendation.confidence_score.desc()
        ).limit(20).all()
        
        for rec in recommendations:
            game = db.query(models.Game).filter(models.Game.id == rec.game_id).first()
            if not game or not game.odds:
                continue
            
            # Get team features
            home_features = self.get_enhanced_player_features(str(game.home_team_id))
            away_features = self.get_enhanced_player_features(str(game.away_team_id))
            
            # Enhanced analysis
            home_clutch = home_features.get('clutch_performance', 0.5)
            away_clutch = away_features.get('clutch_performance', 0.5)
            
            home_athletic = home_features.get('athletic_composite', 0.5)
            away_athletic = away_features.get('athletic_composite', 0.5)
            
            # Calculate clutch advantage
            clutch_advantage = abs(home_clutch - away_clutch)
            athletic_advantage = abs(home_athletic - away_athletic)
            
            latest_odds = game.odds[-1]
            
            if 'spread' in rec.bet_type.lower():
                odds = latest_odds.home_spread_price if rec.recommended_pick == game.home_team.name else latest_odds.away_spread_price
                line = abs(latest_odds.spread_points) if latest_odds.spread_points is not None else 0
            else:
                odds = latest_odds.home_moneyline if rec.recommended_pick == game.home_team.name else latest_odds.away_moneyline
                line = None
            
            if odds is None:
                odds = -110
            
            # Enhanced reasoning
            reasoning_parts = []
            
            if clutch_advantage > 0.3:
                if home_clutch > away_clutch:
                    reasoning_parts.append(f"Home clutch advantage ({home_clutch:.1%} vs {away_clutch:.1%})")
                else:
                    reasoning_parts.append(f"Away clutch advantage ({away_clutch:.1%} vs {home_clutch:.1%})")
            
            if athletic_advantage > 0.3:
                if home_athletic > away_athletic:
                    reasoning_parts.append(f"Home athletic edge ({home_athletic:.1%})")
                else:
                    reasoning_parts.append(f"Away athletic edge ({away_athletic:.1%})")
            
            enhanced_reasoning = rec.reasoning or f"AI pick: {rec.recommended_pick}"
            if reasoning_parts:
                enhanced_reasoning += f" • {' • '.join(reasoning_parts)}"
            
            enhanced_games.append({
                'type': 'game',
                'game': f"{game.away_team.name} @ {game.home_team.name}",
                'bet_type': rec.bet_type,
                'pick': rec.recommended_pick,
                'line': line,
                'odds': odds,
                'confidence': rec.confidence_score,
                'edge': rec.confidence_score - 0.5,
                'reasoning': enhanced_reasoning,
                'home_clutch': home_clutch,
                'away_clutch': away_clutch,
                'home_athletic': home_athletic,
                'away_athletic': away_athletic,
                'clutch_advantage': clutch_advantage,
                'athletic_advantage': athletic_advantage
            })
        
        # Sort by confidence and return top games
        enhanced_games.sort(key=lambda x: x['confidence'], reverse=True)
        return enhanced_games[:limit]
    
    def generate_ai_parlay(self, legs: int = 5, risk_level: str = 'balanced') -> Dict:
        """Generate an AI-optimized parlay using reconstructed data."""
        db = SessionLocal()
        
        try:
            # Get enhanced bets
            prop_bets = self.get_enhanced_prop_bets(db, limit=25)
            game_bets = self.get_enhanced_game_bets(db, limit=15)
            
            # Risk-based allocation strategy
            if risk_level == 'conservative':
                num_props = int(legs * 0.7)  # More props (safer)
                num_games = legs - num_props
                min_edge = 0.06  # Higher edge threshold
            elif risk_level == 'aggressive':
                num_props = int(legs * 0.4)  # More games (higher variance)
                num_games = legs - num_props
                min_edge = 0.03  # Lower edge threshold
            else:  # balanced
                num_props = int(legs * 0.6)
                num_games = legs - num_props
                min_edge = 0.04
            
            selected = []
            
            # Filter by minimum edge
            filtered_props = [bet for bet in prop_bets if bet['edge'] >= min_edge]
            filtered_games = [bet for bet in game_bets if bet['edge'] >= min_edge]
            
            # Add top prop bets
            for bet in filtered_props[:num_props]:
                selected.append(bet)
            
            # Add top game bets
            for bet in filtered_games[:num_games]:
                selected.append(bet)
            
            # Fill remaining slots if needed
            remaining = legs - len(selected)
            all_bets = filtered_props + filtered_games
            for bet in all_bets:
                if bet not in selected and remaining > 0:
                    selected.append(bet)
                    remaining -= 1
            
            # Calculate combined odds and metrics
            combined_decimal = 1.0
            total_edge = 0
            total_confidence = 0
            
            for bet in selected:
                odds = bet['odds']
                if odds > 0:
                    decimal_odds = 1 + (odds / 100)
                else:
                    decimal_odds = 1 + (100 / abs(odds))
                combined_decimal *= decimal_odds
                total_edge += bet['edge']
                total_confidence += bet.get('confidence_score', bet.get('confidence', 0.6))
            
            # Convert to American odds
            if combined_decimal >= 2:
                combined_american = int((combined_decimal - 1) * 100)
            else:
                combined_american = int(-100 / (combined_decimal - 1))
            
            payout = 100 * combined_decimal
            avg_edge = total_edge / len(selected) if selected else 0
            avg_confidence = total_confidence / len(selected) if selected else 0
            
            # Risk assessment
            risk_score = self.calculate_parlay_risk(selected)
            
            print("\n" + "="*70)
            print(f"🎯 AI-ENHANCED MIXED PARLAY ({risk_level.upper()})")
            print("="*70)
            
            for i, bet in enumerate(selected, 1):
                if bet['type'] == 'prop':
                    print(f"\n[Leg {i}] ENHANCED PLAYER PROP")
                    print(f"  {bet['player']} - {bet['prop_type'].upper()} {bet['pick']} {bet['line']}")
                    print(f"  Odds: {bet['odds']:+d} | Hit Rate: {bet['hit_rate']*100:.1f}%")
                    if 'features' in bet:
                        clutch = bet['features'].get('clutch_performance', 0.5)
                        athletic = bet['features'].get('athletic_composite', 0.5)
                        print(f"  Clutch: {clutch:.1%} | Athletic: {athletic:.1%}")
                else:
                    print(f"\n[Leg {i}] ENHANCED GAME BET")
                    print(f"  {bet['game']}")
                    print(f"  {bet['bet_type']}: {bet['pick']}")
                    print(f"  Odds: {bet['odds']:+d}")
                    if 'clutch_advantage' in bet:
                        print(f"  Clutch Adv: {bet['clutch_advantage']:.1%}")
                
                print(f"  Edge: {bet['edge']*100:.1f}%")
            
            print("\n" + "-"*70)
            print(f"Combined Odds: {combined_american:+d}")
            print(f"Potential Payout ($100): ${payout:.2f}")
            print(f"Average Edge: {avg_edge*100:.1f}%")
            print(f"Average Confidence: {avg_confidence*100:.1f}%")
            print(f"Risk Score: {risk_score:.2f}/10")
            print("="*70 + "\n")
            
            return {
                'legs': selected,
                'combined_odds': combined_american,
                'payout': payout,
                'avg_edge': avg_edge,
                'avg_confidence': avg_confidence,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'total_features_used': len(selected) * 5 if selected else 0  # Approximate feature count
            }
            
        finally:
            db.close()
    
    def calculate_parlay_risk(self, bets: List[Dict]) -> float:
        """Calculate risk score for a parlay based on various factors."""
        if not bets:
            return 0.0
        
        risk_factors = []
        
        for bet in bets:
            # Edge-based risk
            edge = bet.get('edge', 0)
            if edge < 0.03:
                risk_factors.append(8.0)
            elif edge < 0.05:
                risk_factors.append(5.0)
            else:
                risk_factors.append(2.0)
            
            # Confidence-based risk
            confidence = bet.get('confidence_score', bet.get('confidence', 0.6))
            if confidence < 0.5:
                risk_factors.append(7.0)
            elif confidence < 0.6:
                risk_factors.append(4.0)
            else:
                risk_factors.append(1.0)
            
            # Prop type risk
            if bet['type'] == 'game':
                risk_factors.append(6.0)  # Games are riskier
            else:
                risk_factors.append(3.0)
        
        # Calculate average risk
        avg_risk = sum(risk_factors) / len(risk_factors)
        
        # Adjust for number of legs (more legs = higher risk)
        leg_penalty = len(bets) * 0.5
        
        final_risk = avg_risk + leg_penalty
        
        return min(10.0, final_risk)  # Cap at 10

# Convenience function for backward compatibility
def generate_enhanced_parlay(legs: int = 5, risk_level: str = 'balanced') -> Dict:
    """Generate an enhanced parlay using reconstructed NBA data."""
    generator = EnhancedParlayGenerator()
    return generator.generate_ai_parlay(legs, risk_level)

if __name__ == "__main__":
    # Test the enhanced generator
    generator = EnhancedParlayGenerator()
    
    print("Testing Enhanced AI Parlay Generator...")
    
    # Generate different risk levels
    for risk in ['conservative', 'balanced', 'aggressive']:
        print(f"\n{'='*50}")
        print(f"GENERATING {risk.upper()} PARLAY")
        print('='*50)
        result = generator.generate_ai_parlay(5, risk)
        print(f"Generated {len(result['legs'])} legs with avg edge: {result['avg_edge']*100:.1f}%")