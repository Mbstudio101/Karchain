"""
Background tasks for self-improvement system.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy.orm import Session
from ..database import SessionLocal
from .self_improvement import SelfImprovementEngine

logger = logging.getLogger(__name__)

class SelfImprovementWorker:
    """Background worker for self-improvement tasks."""
    
    def __init__(self):
        self.running = False
        
    async def start(self):
        """Start the self-improvement worker."""
        self.running = True
        logger.info("Starting self-improvement worker")
        
        while self.running:
            try:
                await self._run_daily_tasks()
                
                # Wait 24 hours before next run
                await asyncio.sleep(24 * 3600)
                
            except Exception as e:
                logger.error(f"Error in self-improvement worker: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _run_daily_tasks(self):
        """Run daily self-improvement tasks."""
        db = SessionLocal()
        try:
            engine = SelfImprovementEngine(db)
            
            # Run daily analysis
            logger.info("Running daily self-improvement analysis")
            results = engine.run_daily_analysis()
            
            # Auto-retrain models that need it
            for retrain_rec in results['retrain_recommendations']:
                logger.info(f"Auto-retraining model: {retrain_rec['model']}")
                success = engine.retrain_model(retrain_rec['model'])
                if success:
                    logger.info(f"Successfully retrained {retrain_rec['model']}")
                else:
                    logger.error(f"Failed to retrain {retrain_rec['model']}")
            
            # Log summary
            logger.info(f"Daily self-improvement complete. Resolved {results['resolved_predictions']} predictions.")
            
        except Exception as e:
            logger.error(f"Error in daily tasks: {e}")
            raise
        finally:
            db.close()
    
    def stop(self):
        """Stop the self-improvement worker."""
        self.running = False
        logger.info("Stopping self-improvement worker")

# FastAPI background task functions
def run_self_improvement_analysis():
    """Background task to run self-improvement analysis."""
    db = SessionLocal()
    try:
        engine = SelfImprovementEngine(db)
        results = engine.run_daily_analysis()
        logger.info(f"Self-improvement analysis complete: {results}")
        return results
    except Exception as e:
        logger.error(f"Error in self-improvement analysis: {e}")
        raise
    finally:
        db.close()

def retrain_model_task(model_name: str):
    """Background task to retrain a specific model."""
    db = SessionLocal()
    try:
        engine = SelfImprovementEngine(db)
        success = engine.retrain_model(model_name)
        logger.info(f"Model retraining {'successful' if success else 'failed'} for {model_name}")
        return success
    except Exception as e:
        logger.error(f"Error retraining model {model_name}: {e}")
        raise
    finally:
        db.close()