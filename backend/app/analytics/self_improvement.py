"""
Self-improvement system that monitors prediction performance and triggers model updates.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import json

from .prediction_tracker import PredictionTracker
from .ml_models import NBAXGBoostModel
from ..models import PredictionOutcome, MLModelMetadata

logger = logging.getLogger(__name__)

class SelfImprovementEngine:
    """Monitors prediction performance and triggers model improvements."""
    
    def __init__(self, db: Session):
        self.db = db
        self.tracker = PredictionTracker(db)
        
    def run_daily_analysis(self) -> Dict:
        """Run daily analysis of prediction performance."""
        logger.info("Running daily self-improvement analysis")
        
        # Resolve any pending predictions
        resolved_count = self.tracker.resolve_all_pending_predictions()
        
        # Analyze model performance
        performance_data = self.tracker.get_all_models_performance(days_back=30)
        
        # Check if any models need retraining
        retrain_recommendations = []
        for model_name, performance in performance_data.items():
            if self.tracker.should_retrain_model(model_name):
                retrain_recommendations.append({
                    'model': model_name,
                    'win_rate': performance['win_rate'],
                    'total_bets': performance['total_bets'],
                    'reason': 'Performance below threshold'
                })
        
        # Generate improvement insights
        insights = self._generate_improvement_insights(performance_data)
        
        result = {
            'timestamp': datetime.utcnow(),
            'resolved_predictions': resolved_count,
            'model_performance': performance_data,
            'retrain_recommendations': retrain_recommendations,
            'insights': insights
        }
        
        logger.info(f"Daily analysis complete: {len(retrain_recommendations)} models need retraining")
        return result
    
    def _generate_improvement_insights(self, performance_data: Dict) -> Dict:
        """Generate actionable insights from performance data."""
        insights = {}
        
        # Compare model performance
        if 'xgboost' in performance_data and 'heuristic' in performance_data:
            ml_performance = performance_data['xgboost']
            heuristic_performance = performance_data['heuristic']
            
            if ml_performance['total_bets'] >= 20 and heuristic_performance['total_bets'] >= 20:
                ml_better = ml_performance['win_rate'] > heuristic_performance['win_rate']
                win_rate_diff = abs(ml_performance['win_rate'] - heuristic_performance['win_rate'])
                
                if win_rate_diff > 0.05:  # 5% difference
                    insights['model_comparison'] = {
                        'ml_superior': ml_better,
                        'win_rate_difference': win_rate_diff,
                        'recommendation': 'Increase ML model weight' if ml_better else 'Review ML feature engineering'
                    }
        
        # Identify declining performance trends
        for model_name, performance in performance_data.items():
            if performance['total_bets'] >= 20:
                recent_performance = self.tracker.get_model_performance(model_name, days_back=7)
                older_performance = self.tracker.get_model_performance(model_name, days_back=30)
                
                if recent_performance['win_rate'] < older_performance['win_rate'] - 0.1:  # 10% drop
                    insights[f'{model_name}_decline'] = {
                        'recent_win_rate': recent_performance['win_rate'],
                        'older_win_rate': older_performance['win_rate'],
                        'recommendation': 'Investigate recent performance decline'
                    }
        
        # Feature importance analysis (if we have enough data)
        xgboost_insights = self._analyze_xgboost_features()
        if xgboost_insights:
            insights['xgboost_features'] = xgboost_insights
        
        return insights
    
    def _analyze_xgboost_features(self) -> Optional[Dict]:
        """Analyze XGBoost feature importance and suggest improvements."""
        try:
            # Get recent XGBoost predictions
            recent_predictions = self.db.query(PredictionOutcome).filter(
                PredictionOutcome.model_used == 'xgboost',
                PredictionOutcome.created_at >= datetime.utcnow() - timedelta(days=30),
                PredictionOutcome.actual_result != 'pending'
            ).all()
            
            if len(recent_predictions) < 50:  # Need sufficient data
                return None
            
            # Analyze feature snapshots to identify patterns
            correct_features = []
            incorrect_features = []
            
            for pred in recent_predictions:
                if pred.feature_snapshot:
                    try:
                        features = json.loads(pred.feature_snapshot)
                        if pred.actual_result == 'win':
                            correct_features.append(features)
                        elif pred.actual_result == 'loss':
                            incorrect_features.append(features)
                    except json.JSONDecodeError:
                        continue
            
            if not correct_features or not incorrect_features:
                return None
            
            # Simple feature analysis (could be expanded)
            insights = {
                'total_predictions': len(recent_predictions),
                'correct_predictions': len(correct_features),
                'incorrect_predictions': len(incorrect_features),
                'accuracy': len(correct_features) / len(recent_predictions),
                'recommendation': 'Consider feature engineering review' if len(correct_features) / len(recent_predictions) < 0.5 else 'Model performing well'
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing XGBoost features: {e}")
            return None
    
    def retrain_model(self, model_name: str, days_back: int = 90) -> bool:
        """Retrain a specific model with recent data."""
        logger.info(f"Retraining model: {model_name}")

        try:
            if model_name == 'xgboost':
                from .ml_models import FeatureEngineer

                # Build the DataFrame that train() expects
                engineer = FeatureEngineer(self.db)
                df = engineer.prepare_training_data()

                if df.empty:
                    logger.error("No training data available for retraining")
                    return False

                model = NBAXGBoostModel()
                success = model.train(df)

                if success:
                    # Update model metadata
                    self._update_model_metadata(model_name, model)
                    logger.info(f"Successfully retrained {model_name}")
                    return True
                else:
                    logger.error(f"Failed to retrain {model_name}")
                    return False
                    
            else:
                logger.warning(f"Retraining not implemented for model: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error retraining model {model_name}: {e}")
            return False
    
    def _update_model_metadata(self, model_name: str, model: NBAXGBoostModel) -> None:
        """Update model metadata after retraining."""
        try:
            # Deactivate old model
            old_models = self.db.query(MLModelMetadata).filter(
                MLModelMetadata.model_name == model_name,
                MLModelMetadata.is_active == True
            ).all()
            
            for old_model in old_models:
                old_model.is_active = False
            
            # Create new metadata entry
            new_metadata = MLModelMetadata(
                model_name=model_name,
                model_type='classifier',
                version=f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                filepath=model.model_path,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_metadata)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating model metadata: {e}")
            self.db.rollback()
    
    def get_improvement_recommendations(self) -> Dict:
        """Get current improvement recommendations."""
        daily_results = self.run_daily_analysis()
        
        recommendations = {
            'immediate_actions': [],
            'medium_term': [],
            'long_term': []
        }
        
        # Immediate actions
        for retrain_rec in daily_results['retrain_recommendations']:
            recommendations['immediate_actions'].append({
                'action': f"Retrain {retrain_rec['model']} model",
                'reason': retrain_rec['reason'],
                'priority': 'high'
            })
        
        # Medium term improvements
        if 'model_comparison' in daily_results['insights']:
            comparison = daily_results['insights']['model_comparison']
            if comparison['win_rate_difference'] > 0.1:
                recommendations['medium_term'].append({
                    'action': 'Adjust model weighting in recommendation engine',
                    'reason': f"Significant performance difference: {comparison['win_rate_difference']:.1%}",
                    'priority': 'medium'
                })
        
        # Long term improvements
        for insight_key, insight_data in daily_results['insights'].items():
            if 'decline' in insight_key:
                recommendations['long_term'].append({
                    'action': f"Investigate {insight_key.replace('_decline', '')} model degradation",
                    'reason': insight_data['recommendation'],
                    'priority': 'low'
                })
        
        return recommendations