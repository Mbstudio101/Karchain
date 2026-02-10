"""
Self-improvement system for tracking prediction outcomes and retraining models.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

from ..models import Recommendation, Game, PredictionOutcome, MLModelMetadata, Player, Team, BettingOdds
from ..analytics.ml_models import NBAXGBoostModel, FeatureEngineer
from ..models_nba_official import NBAOfficialPlayerStats

logger = logging.getLogger(__name__)

class PredictionTracker:
    """Tracks prediction outcomes and provides feedback for model improvement."""
    
    def __init__(self, db: Session):
        self.db = db
        self.feature_engineer = FeatureEngineer(db)
        
    def capture_feature_snapshot(self, game: Game) -> Dict:
        """Capture comprehensive feature snapshot for ML model prediction."""
        try:
            # Get basic rolling stats
            home_stats = self.feature_engineer.get_team_rolling_stats(game.home_team_id, game.game_date)
            away_stats = self.feature_engineer.get_team_rolling_stats(game.away_team_id, game.game_date)
            
            # Get hustle and defense stats (using current season)
            home_hustle = self.feature_engineer.get_team_hustle_defense_stats(game.home_team_id, "2023-24")
            away_hustle = self.feature_engineer.get_team_hustle_defense_stats(game.away_team_id, "2023-24")
            
            # Get betting odds snapshot
            betting_odds = self.db.query(BettingOdds).filter(
                BettingOdds.game_id == game.id
            ).order_by(BettingOdds.timestamp.desc()).first()
            
            snapshot = {
                "game_id": game.id,
                "game_date": game.game_date.isoformat(),
                "home_team": game.home_team.name,
                "away_team": game.away_team.name,
                "home_team_id": game.home_team_id,
                "away_team_id": game.away_team_id,
                
                # Basic stats
                "home_ppg": home_stats.get("ppg", 0),
                "away_ppg": away_stats.get("ppg", 0),
                "home_rpg": home_stats.get("rpg", 0),
                "away_rpg": away_stats.get("rpg", 0),
                "home_apg": home_stats.get("apg", 0),
                "away_apg": away_stats.get("apg", 0),
                
                # Conference matchup
                "is_home_conference_match": 1 if game.home_team.conference == game.away_team.conference else 0,
                
                # Hustle and defense stats (new "hidden" features)
                "home_hustle_score": home_hustle.get("hustle_score", 0),
                "away_hustle_score": away_hustle.get("hustle_score", 0),
                "home_defense_fg_diff": home_hustle.get("team_defense_fg_diff", 0),
                "away_defense_fg_diff": away_hustle.get("team_defense_fg_diff", 0),
                "home_contested_shots": home_hustle.get("team_contested_shots", 0),
                "away_contested_shots": away_hustle.get("team_contested_shots", 0),
                "home_deflections": home_hustle.get("team_deflections", 0),
                "away_deflections": away_hustle.get("team_deflections", 0),
                "home_screen_assists": home_hustle.get("team_screen_assists", 0),
                "away_screen_assists": away_hustle.get("team_screen_assists", 0),
                "home_loose_balls": home_hustle.get("team_loose_balls", 0),
                "away_loose_balls": away_hustle.get("team_loose_balls", 0),
                "home_charges_drawn": home_hustle.get("team_charges_drawn", 0),
                "away_charges_drawn": away_hustle.get("team_charges_drawn", 0),
                
                # Betting context
                "home_moneyline": betting_odds.home_moneyline if betting_odds else None,
                "away_moneyline": betting_odds.away_moneyline if betting_odds else None,
                "spread_points": betting_odds.spread_points if betting_odds else None,
                "home_spread_price": betting_odds.home_spread_price if betting_odds else None,
                "away_spread_price": betting_odds.away_spread_price if betting_odds else None,
                "total_points": betting_odds.total_points if betting_odds else None,
                "over_price": betting_odds.over_price if betting_odds else None,
                "under_price": betting_odds.under_price if betting_odds else None,
                
                # Timestamp
                "snapshot_timestamp": datetime.utcnow().isoformat()
            }
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error capturing feature snapshot: {e}")
            # Return basic snapshot on error
            return {
                "game_id": game.id,
                "game_date": game.game_date.isoformat(),
                "home_team": game.home_team.name,
                "away_team": game.away_team.name,
                "home_team_id": game.home_team_id,
                "away_team_id": game.away_team_id,
                "home_ppg": 0,
                "away_ppg": 0,
                "home_rpg": 0,
                "away_rpg": 0,
                "home_apg": 0,
                "away_apg": 0,
                "is_home_conference_match": 1 if game.home_team.conference == game.away_team.conference else 0,
                "home_hustle_score": 0,
                "away_hustle_score": 0,
                "home_defense_fg_diff": 0,
                "away_defense_fg_diff": 0,
                "home_contested_shots": 0,
                "away_contested_shots": 0,
                "error": str(e),
                "snapshot_timestamp": datetime.utcnow().isoformat()
            }
        
    def record_prediction(self, recommendation: Recommendation, model_used: str = None, 
                         feature_snapshot: Dict = None) -> PredictionOutcome:
        """Record a new prediction for tracking."""
        outcome = PredictionOutcome(
            recommendation_id=recommendation.id,
            game_id=recommendation.game_id,
            predicted_pick=recommendation.recommended_pick,
            predicted_confidence=recommendation.confidence_score,
            bet_type=recommendation.bet_type,
            model_used=model_used or 'heuristic',
            feature_snapshot=json.dumps(feature_snapshot) if feature_snapshot else None,
            actual_result='pending'
        )
        self.db.add(outcome)
        self.db.commit()
        return outcome
    
    def resolve_prediction(self, outcome: PredictionOutcome, game: Game) -> bool:
        """Resolve a prediction based on actual game results."""
        if game.status != 'Final':
            return False
            
        # Determine if prediction was correct
        result = self._evaluate_prediction(outcome, game)
        
        # Calculate profit/loss (assuming $100 bet for simplicity)
        profit_loss = self._calculate_profit_loss(result, outcome.odds_at_bet or -110)
        
        outcome.actual_result = result
        outcome.actual_score_home = game.home_score
        outcome.actual_score_away = game.away_score
        outcome.profit_loss = profit_loss
        outcome.resolved_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def _evaluate_prediction(self, outcome: PredictionOutcome, game: Game) -> str:
        """Evaluate if the prediction was correct."""
        pick = outcome.predicted_pick.lower()
        
        if outcome.bet_type == 'spread':
            return self._evaluate_spread(pick, game)
        elif outcome.bet_type == 'total':
            return self._evaluate_total(pick, game)
        elif outcome.bet_type == 'moneyline':
            return self._evaluate_moneyline(pick, game)
        else:
            return 'pending'  # Props need special handling
    
    def _evaluate_spread(self, pick: str, game: Game) -> str:
        """Evaluate spread bet outcome."""
        # Extract team and spread from pick (e.g., "LAL Lakers -5.5")
        parts = pick.split()
        if len(parts) < 2:
            return 'pending'
            
        try:
            spread = float(parts[-1])
            is_home = game.home_team.name.lower() in pick.lower()
            
            if is_home:
                final_margin = game.home_score - game.away_score
            else:
                final_margin = game.away_score - game.home_score
            
            # For favorite (negative spread), need to win by more than spread
            if spread < 0:
                if final_margin > abs(spread):
                    return 'win'
                elif final_margin == abs(spread):
                    return 'push'
                else:
                    return 'loss'
            # For underdog (positive spread), can lose by less than spread or win outright
            else:
                if final_margin > 0 or abs(final_margin) < spread:
                    return 'win'
                elif final_margin == -spread:
                    return 'push'
                else:
                    return 'loss'
        except (ValueError, IndexError):
            return 'pending'
    
    def _evaluate_total(self, pick: str, game: Game) -> str:
        """Evaluate total bet outcome."""
        total_score = game.home_score + game.away_score
        
        if 'over' in pick.lower():
            # Extract the total line from pick
            import re
            match = re.search(r'(\d+\.?\d*)', pick)
            if match:
                line = float(match.group(1))
                return 'win' if total_score > line else 'loss'
        elif 'under' in pick.lower():
            match = re.search(r'(\d+\.?\d*)', pick)
            if match:
                line = float(match.group(1))
                return 'win' if total_score < line else 'loss'
        
        return 'pending'
    
    def _evaluate_moneyline(self, pick: str, game: Game) -> str:
        """Evaluate moneyline bet outcome."""
        if game.home_score > game.away_score:
            winner = game.home_team.name.lower()
        else:
            winner = game.away_team.name.lower()
            
        if winner in pick.lower():
            return 'win'
        else:
            return 'loss'
    
    def _calculate_profit_loss(self, result: str, odds: int) -> float:
        """Calculate profit/loss for a bet."""
        if result == 'win':
            if odds > 0:
                return (odds / 100) * 100  # Positive odds
            else:
                return (100 / abs(odds)) * 100  # Negative odds
        elif result == 'loss':
            return -100  # Assume $100 bet
        else:
            return 0  # Push
    
    def get_model_performance(self, model_name: str, days_back: int = 30) -> Dict:
        """Get performance metrics for a specific model."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        outcomes = self.db.query(PredictionOutcome).filter(
            PredictionOutcome.model_used == model_name,
            PredictionOutcome.created_at >= cutoff_date,
            PredictionOutcome.actual_result != 'pending'
        ).all()
        
        if not outcomes:
            return {'win_rate': 0, 'total_bets': 0, 'profit': 0, 'roi': 0}
        
        wins = sum(1 for o in outcomes if o.actual_result == 'win')
        losses = sum(1 for o in outcomes if o.actual_result == 'loss')
        pushes = sum(1 for o in outcomes if o.actual_result == 'push')
        
        total_bets = wins + losses + pushes
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        total_profit = sum(o.profit_loss for o in outcomes)
        roi = (total_profit / (total_bets * 100)) * 100 if total_bets > 0 else 0
        
        return {
            'win_rate': win_rate,
            'total_bets': total_bets,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'profit': total_profit,
            'roi': roi
        }
    
    def get_all_models_performance(self, days_back: int = 30) -> Dict[str, Dict]:
        """Get performance for all models."""
        models = ['xgboost', 'pythagorean', 'heuristic']
        return {model: self.get_model_performance(model, days_back) for model in models}
    
    def should_retrain_model(self, model_name: str, threshold_days: int = 7, 
                           performance_threshold: float = 0.45) -> bool:
        """Determine if a model should be retrained based on performance."""
        performance = self.get_model_performance(model_name, days_back=threshold_days)
        
        # Retrain if win rate drops below threshold and we have enough samples
        if performance['total_bets'] >= 20 and performance['win_rate'] < performance_threshold:
            logger.warning(f"Model {model_name} performance dropped: {performance['win_rate']:.1%} win rate")
            return True
            
        return False
    
    def get_xgboost_prediction(self, game: Game) -> Dict:
        """Get XGBoost prediction with enhanced features for a game."""
        try:
            model = NBAXGBoostModel()
            
            # Get the prediction probability
            prediction_prob = model.predict_one(game, self.db)
            
            if prediction_prob is None:
                return {
                    "model": "xgboost",
                    "error": "Model not available or insufficient data",
                    "confidence": 0,
                    "recommended_pick": "pending"
                }
            
            # Convert probability to confidence and pick
            confidence = prediction_prob
            recommended_pick = game.home_team.name if confidence > 0.5 else game.away_team.name
            
            # Capture feature snapshot for this prediction
            feature_snapshot = self.capture_feature_snapshot(game)
            
            return {
                "model": "xgboost",
                "confidence": confidence,
                "recommended_pick": recommended_pick,
                "home_win_probability": prediction_prob,
                "away_win_probability": 1 - prediction_prob,
                "feature_snapshot": feature_snapshot,
                "is_high_confidence": confidence > 0.65 or confidence < 0.35  # High confidence if >65% or <35%
            }
            
        except Exception as e:
            logger.error(f"Error getting XGBoost prediction: {e}")
            return {
                "model": "xgboost",
                "error": str(e),
                "confidence": 0,
                "recommended_pick": "pending"
            }
    
    def resolve_all_pending_predictions(self) -> int:
        """Resolve all pending predictions for games that are now final."""
        pending_outcomes = self.db.query(PredictionOutcome).filter(
            PredictionOutcome.actual_result == 'pending'
        ).join(Game).filter(
            Game.status == 'Final'
        ).all()
        
        resolved_count = 0
        for outcome in pending_outcomes:
            game = self.db.query(Game).filter(Game.id == outcome.game_id).first()
            if game and self.resolve_prediction(outcome, game):
                resolved_count += 1
        
        logger.info(f"Resolved {resolved_count} pending predictions")
        return resolved_count