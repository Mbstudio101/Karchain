"""
Self-improvement analytics endpoints for tracking AI performance and triggering improvements.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..dependencies import get_db
from ..analytics.prediction_tracker import PredictionTracker
from ..analytics.self_improvement import SelfImprovementEngine
from ..analytics.background_tasks import run_self_improvement_analysis, retrain_model_task
from .. import models

router = APIRouter(
    prefix="/self-improvement",
    tags=["self-improvement"]
)

@router.get("/performance")
def get_model_performance(model_name: Optional[str] = None, days_back: int = 30, db: Session = Depends(get_db)):
    """Get performance metrics for AI models."""
    tracker = PredictionTracker(db)
    
    if model_name:
        return tracker.get_model_performance(model_name, days_back)
    else:
        return tracker.get_all_models_performance(days_back)

@router.post("/run-analysis")
def run_self_improvement_analysis_endpoint(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger daily self-improvement analysis in background."""
    background_tasks.add_task(run_self_improvement_analysis)
    return {"message": "Self-improvement analysis started in background"}

@router.post("/retrain-model/{model_name}")
def retrain_model_endpoint(model_name: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger model retraining in background."""
    background_tasks.add_task(retrain_model_task, model_name)
    return {"message": f"Model retraining started for {model_name}"}

@router.get("/recommendations")
def get_improvement_recommendations(db: Session = Depends(get_db)):
    """Get current improvement recommendations."""
    engine = SelfImprovementEngine(db)
    return engine.get_improvement_recommendations()

@router.get("/genius-picks")
def get_genius_picks(days_back: int = 30, min_confidence: float = 0.8, db: Session = Depends(get_db)):
    """Get Genius Picks that hit their targets."""
    tracker = PredictionTracker(db)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Get winning predictions with high confidence
    from sqlalchemy import and_
    genius_picks = db.query(models.PredictionOutcome).join(models.Recommendation).filter(
        and_(
            models.PredictionOutcome.created_at >= cutoff_date,
            models.PredictionOutcome.actual_result == 'win',
            models.Recommendation.confidence_score >= min_confidence
        )
    ).order_by(models.Recommendation.confidence_score.desc()).all()
    
    return {
        "count": len(genius_picks),
        "picks": [
            {
                "id": pick.id,
                "game_id": pick.game_id,
                "predicted_pick": pick.predicted_pick,
                "confidence": pick.predicted_confidence,
                "model_used": pick.model_used,
                "created_at": pick.created_at,
                "resolved_at": pick.resolved_at
            }
            for pick in genius_picks
        ]
    }

@router.get("/ai-parlays")
def get_ai_parlays(days_back: int = 30, min_confidence: float = 0.7, db: Session = Depends(get_db)):
    """Get AI Parlays that hit their targets."""
    # This would need a ParlayOutcome table - for now return empty
    return {
        "count": 0,
        "parlays": [],
        "message": "Parlay tracking coming soon"
    }

@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive dashboard stats for the AI system."""
    tracker = PredictionTracker(db)
    engine = SelfImprovementEngine(db)
    
    # Get performance data
    performance_30d = tracker.get_all_models_performance(days_back=30)
    performance_7d = tracker.get_all_models_performance(days_back=7)
    
    # Get recent genius picks
    genius_picks = db.query(models.PredictionOutcome).join(models.Recommendation).filter(
        models.PredictionOutcome.created_at >= datetime.utcnow() - timedelta(days=30),
        models.PredictionOutcome.actual_result == 'win',
        models.Recommendation.confidence_score >= 0.8
    ).count()
    
    # Get improvement recommendations
    recommendations = engine.get_improvement_recommendations()
    
    return {
        "performance": {
            "30_days": performance_30d,
            "7_days": performance_7d
        },
        "genius_picks": {
            "last_30_days": genius_picks,
            "hit_rate": genius_picks / max(1, db.query(models.PredictionOutcome).filter(
                models.PredictionOutcome.created_at >= datetime.utcnow() - timedelta(days=30),
                models.PredictionOutcome.actual_result.in_(['win', 'loss'])
            ).count())
        },
        "improvement_recommendations": recommendations,
        "last_analysis": datetime.utcnow()
    }