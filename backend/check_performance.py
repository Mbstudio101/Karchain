from app.analytics.prediction_tracker import PredictionTracker
from app.database import SessionLocal
import sys

# Get DB session
db = SessionLocal()
try:
    tracker = PredictionTracker(db)
    
    # Get performance for all models
    performance = tracker.get_all_models_performance(days_back=30)
    
    print('📊 CURRENT AI PERFORMANCE METRICS (Last 30 Days):')
    print('=' * 60)
    for model, stats in performance.items():
        print(f'🤖 {model.upper()}:')
        print(f'   Win Rate: {stats["win_rate"]:.1%}')
        print(f'   Total Bets: {stats["total_bets"]}')
        if stats["total_bets"] > 0:
            print(f'   Record: {stats["wins"]}-{stats["losses"]}-{stats["pushes"]}')
            print(f'   Profit: ${stats["profit"]:.2f}')
            print(f'   ROI: {stats["roi"]:.2f}%')
        else:
            print('   No bets placed yet')
        print()
finally:
    db.close()

# Also check what predictions we have
print('\n📈 CHECKING PREDICTION DATABASE:')
print('=' * 40)
from app.models import PredictionOutcome
outcomes = db.query(PredictionOutcome).filter(PredictionOutcome.actual_result != 'pending').all()
print(f'Total resolved predictions: {len(outcomes)}')
if outcomes:
    wins = sum(1 for o in outcomes if o.actual_result == 'win')
    print(f'Wins: {wins}')
    print(f'Win rate: {wins/len(outcomes):.1%}')