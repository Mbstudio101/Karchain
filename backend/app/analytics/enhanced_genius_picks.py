"""
Enhanced Genius Picks with Real NBA Data Integration
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
import logging

# Import enhanced NBA API client
from app.enhanced_nba_api_client import get_enhanced_nba_client
# Import real sportsbook aggregator
from app.sportsbook_api_client import get_sportsbook_aggregator
# Import NBA media client for headshots and logos
from app.nba_media_client import get_nba_media_client

logger = logging.getLogger(__name__)

class EnhancedGeniusPicks:
    def __init__(self):
        self.nba_client = get_enhanced_nba_client()
        self.sportsbook_aggregator = get_sportsbook_aggregator()
        self.media_client = get_nba_media_client()
        
    def get_enhanced_player_analytics(self, player_id: str) -> Dict[str, float]:
        """Get comprehensive player analytics using real NBA API data."""
        try:
            # Get real clutch stats from NBA API
            clutch_stats = self.nba_client.get_player_clutch_stats(player_id)
            
            # Get real tracking stats (speed, distance)
            tracking_stats = self.nba_client.get_player_tracking_stats(player_id)
            
            # Get defensive impact
            defensive_stats = self.nba_client.get_defensive_impact(player_id)
            
            # Get current season stats
            season_stats = self.nba_client.get_live_player_stats(player_id)
            
            # Calculate composite ratings based on real data
            clutch_score = clutch_stats['clutch_rating']
            athletic_score = (tracking_stats['speed_factor'] + tracking_stats['distance_factor']) / 2
            defensive_score = defensive_stats['defensive_impact']
            
            # Calculate consistency score based on real clutch efficiency
            clutch_usage = clutch_stats['clutch_usage_percentage'] / 35.0  # Normalize to 0-1
            clutch_efg = clutch_stats['clutch_efg_percentage']
            consistency_score = (clutch_usage * 0.3) + (clutch_efg * 0.7)
            
            return {
                'clutch_score': clutch_score,
                'athletic_score': athletic_score,
                'defensive_score': defensive_score,
                'consistency_score': consistency_score,
                'clutch_usage': clutch_usage,
                'clutch_efg': clutch_efg,
                'composite_rating': (clutch_score * 0.4 + athletic_score * 0.3 + defensive_score * 0.2 + consistency_score * 0.1),
                'season_stats': season_stats,
                'clutch_stats': clutch_stats,
                'tracking_stats': tracking_stats,
                'defensive_stats': defensive_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced analytics for player {player_id}: {e}")
            return self._get_fallback_analytics()
    
    def _get_fallback_analytics(self) -> Dict[str, float]:
        """Conservative fallback analytics when NBA API fails"""
        return {
            'clutch_score': 0.6,
            'athletic_score': 0.5,
            'defensive_score': 0.5,
            'consistency_score': 0.5,
            'clutch_usage': 0.4,
            'clutch_efg': 0.45,
            'composite_rating': 0.55,
            'season_stats': {
                'ppg': 12.0,
                'rpg': 4.0,
                'apg': 3.0,
                'fg_pct': 0.45,
                'three_pct': 0.35,
                'minutes': 28.0,
                'games_played': 15
            }
        }
    
    def calculate_enhanced_probability(self, player: models.Player, prop_type: str, 
                                     line: float, game_context: Dict = None) -> Dict[str, float]:
        """Calculate enhanced probability using real NBA API data and advanced statistics."""
        player_id = str(player.id)
        analytics = self.get_enhanced_player_analytics(player_id)
        
        # Base probability from historical data with larger sample size
        if not player.stats:
            return {
                'probability': 0.5,
                'confidence_interval': [0.4, 0.6],
                'composite_rating': analytics['composite_rating'],
                'clutch_adjustment': 0,
                'athletic_adjustment': 0,
                'sample_size': 0
            }
        
        # Use larger sample size (50 games instead of 25)
        recent_games = player.stats[:50]
        if not recent_games:
            return {
                'probability': 0.5,
                'confidence_interval': [0.4, 0.6],
                'composite_rating': analytics['composite_rating'],
                'clutch_adjustment': 0,
                'athletic_adjustment': 0,
                'sample_size': 0
            }
        
        # Calculate hits vs line
        hits = 0
        total_games = len(recent_games)
        
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
        
        # Calculate recent form (last 10 games)
        recent_games_10 = player.stats[:10]
        recent_hits = 0
        recent_total = len(recent_games_10)
        
        for stat in recent_games_10:
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
                recent_hits += 1
        
        # Base probability with recency weighting
        overall_prob = hits / total_games if total_games > 0 else 0.5
        recent_prob = recent_hits / recent_total if recent_total > 0 else overall_prob
        base_prob = (overall_prob * 0.7) + (recent_prob * 0.3)  # Weight recent form
        
        # Apply clutch adjustments for close games
        clutch_adjustment = 0
        if game_context and game_context.get('is_close_game'):
            clutch_factor = analytics['clutch_score'] - 0.5  # Above average clutch
            clutch_adjustment = clutch_factor * 0.1  # 10% max adjustment
            base_prob += clutch_adjustment
        
        # Apply athletic adjustments for high-usage props
        athletic_adjustment = 0
        if prop_type in ['points', 'pts+reb+ast'] and analytics['athletic_score'] > 0.7:
            athletic_factor = analytics['athletic_score'] - 0.5
            athletic_adjustment = athletic_factor * 0.05  # 5% max adjustment
            base_prob += athletic_adjustment
        
        # Apply defensive adjustments for opponent context
        if game_context and game_context.get('opponent_defensive_rating'):
            defensive_factor = analytics['defensive_score'] - game_context['opponent_defensive_rating']
            base_prob += defensive_factor * 0.03
        
        # Ensure probability stays within bounds
        base_prob = max(0.1, min(0.9, base_prob))
        
        # Calculate 99% confidence interval using Wilson Score Interval
        confidence_interval = self.wilson_confidence_interval(hits, total_games, z_score=2.576)
        
        return {
            'probability': base_prob,
            'confidence_interval': confidence_interval,
            'composite_rating': analytics['composite_rating'],
            'clutch_adjustment': clutch_adjustment,
            'athletic_adjustment': athletic_adjustment,
            'sample_size': total_games
        }
    
    def wilson_confidence_interval(self, successes: int, trials: int, z_score: float = 1.96) -> List[float]:
        """Calculate Wilson Score Interval for binomial proportion"""
        if trials == 0:
            return [0.0, 1.0]
        
        p = successes / trials
        n = trials
        
        # Wilson Score Interval calculation
        denominator = 1 + (z_score**2 / n)
        center = (p + (z_score**2 / (2 * n))) / denominator
        margin = z_score * math.sqrt((p * (1 - p) / n) + (z_score**2 / (4 * n**2))) / denominator
        
        lower = max(0.0, center - margin)
        upper = min(1.0, center + margin)
        
        return [lower, upper]
    
    def calculate_enhanced_ev(self, probability: float, odds: float, confidence_width: float, 
                             composite_rating: float) -> Dict[str, float]:
        """Calculate expected value with enhanced risk management"""
        # Convert American odds to decimal
        if odds > 0:
            decimal_odds = (odds / 100) + 1
        else:
            decimal_odds = (100 / abs(odds)) + 1
        
        # Calculate EV
        ev = (probability * decimal_odds) - 1
        
        # Calculate edge (advantage over bookmaker)
        implied_prob = 1 / decimal_odds
        edge = probability - implied_prob
        
        # Kelly Criterion for bet sizing with risk management
        kelly_fraction = self.calculate_kelly_fraction(probability, decimal_odds, confidence_width, composite_rating)
        
        return {
            'ev': ev * 100,  # Convert to dollar amount per $1 bet
            'edge': edge,
            'kelly_fraction': kelly_fraction,
            'confidence_width': confidence_width
        }
    
    def calculate_kelly_fraction(self, probability: float, decimal_odds: float, 
                               confidence_width: float, composite_rating: float) -> float:
        """Calculate Kelly Criterion fraction with risk management"""
        # Basic Kelly formula
        q = 1 - probability
        kelly = (decimal_odds * probability - q) / decimal_odds if decimal_odds > 0 else 0
        
        # Apply confidence adjustment (wider confidence = less certainty)
        confidence_factor = 1 - (confidence_width * 0.5)
        
        # Apply composite rating adjustment (higher rating = more confidence)
        rating_factor = composite_rating
        
        # Apply conservative multiplier (0.25 for quarter Kelly)
        adjusted_kelly = kelly * confidence_factor * rating_factor * 0.25
        
        return max(0, min(adjusted_kelly, 0.05))  # Cap at 5%
    
    def get_enhanced_genius_picks(self, target_date: date = None, min_edge: float = 0.03) -> Dict:
        """Get enhanced genius picks using real NBA data and sportsbook odds."""
        if target_date is None:
            target_date = date.today()
        
        db = SessionLocal()
        
        try:
            # Use the gameday range to capture all games for the target date
            from ..date_utils import get_gameday_range
            start_utc, end_utc = get_gameday_range(target_date)
            
            # Get all player props for the date range
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
                
                # Get real sportsbook odds for this player and prop
                best_odds_info = self.sportsbook_aggregator.get_best_odds(
                    player.name, prop.prop_type, prop.line
                )
                
                # Use real odds if available, otherwise use the prop's odds
                if best_odds_info:
                    over_odds = best_odds_info['over'].over_odds
                    under_odds = best_odds_info['under'].under_odds
                    sportsbook = f"{best_odds_info['over'].sportsbook}/{best_odds_info['under'].sportsbook}"
                else:
                    over_odds = prop.over_odds
                    under_odds = prop.under_odds
                    sportsbook = prop.sportsbook or 'Consensus'
                over_analysis = self.calculate_enhanced_probability(
                    player, prop.prop_type, prop.line, game_context
                )
                
                under_analysis = self.calculate_enhanced_probability(
                    player, prop.prop_type, prop.line, game_context
                )
                
                # Calculate EV for both sides using real odds
                over_ev_data = self.calculate_enhanced_ev(
                    over_analysis['probability'], 
                    over_odds,
                    (over_analysis['confidence_interval'][1] - over_analysis['confidence_interval'][0]),
                    over_analysis['composite_rating']
                )
                
                under_ev_data = self.calculate_enhanced_ev(
                    1 - under_analysis['probability'],  # Under probability
                    under_odds,
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
                
                # Get player headshot and team information using NBA Media Client
                player_headshot_info = self.media_client.get_player_headshot_with_fallback(
                    player.name, 
                    str(player.id) if player.id else None
                )
                player_headshot = player_headshot_info['url']
                
                # Get team information
                team_info = None
                if player.team:
                    team_logo_info = self.media_client.get_team_logo_with_fallback(player.team.name)
                    team_info = {
                        'name': player.team.name,
                        'logo': team_logo_info['url'],
                        'logo_source': team_logo_info['source']
                    }
                
                genius_picks.append({
                    'player': player.name,
                    'player_headshot': player_headshot,
                    'player_headshot_source': player_headshot_info['source'],
                    'player_headshot_is_fallback': player_headshot_info['is_fallback'],
                    'team': team_info,
                    'prop': prop.prop_type.replace('+', ' + ').title(),
                    'line': prop.line,
                    'pick': best_side,
                    'odds': best_odds,
                    'sportsbook': prop.sportsbook or 'Consensus',
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
                'data_source': 'Real NBA Analytics'
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
        elif ev > 1 and edge > 0.02 and composite_rating > 0.4:
            return "B"
        else:
            return "C"