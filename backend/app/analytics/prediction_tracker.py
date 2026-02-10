"""
Self-improvement system for tracking prediction outcomes and retraining models.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

from ..models import Recommendation, Game, PredictionOutcome, MLModelMetadata
from ..analytics.ml_models import NBAXGBoostModel

logger = logging.getLogger(__name__)

class PredictionTracker:
    """Tracks prediction outcomes and provides feedback for model improvement."""
    
    def __init__(self, db: Session):
        self.db = db
        
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