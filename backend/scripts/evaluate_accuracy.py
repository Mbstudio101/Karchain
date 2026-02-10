import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Game, Recommendation, BettingOdds, Team
from app.database import DATABASE_URL

def evaluate_accuracy():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    print("=== AI Accuracy Evaluation ===")
    
    # Fetch all recommendations for games that are Final
    recs = db.query(Recommendation).join(Game).filter(
        Game.status == "Final"
    ).all()
    
    if not recs:
        print("No recommendations found for completed games.")
        return

    total = 0
    correct = 0
    
    by_type = {}
    by_confidence = {"High (70%+)": [0,0], "Medium (55-70%)": [0,0], "Low (<55%)": [0,0]}
    
    print(f"Analyzing {len(recs)} recommendations...")
    
    for rec in recs:
        game = rec.game
        won = False
        
        # Determine if recommendation won
        if rec.bet_type == "Moneyline":
            winner = game.home_team.name if game.home_score > game.away_score else game.away_team.name
            won = (rec.recommended_pick == winner)
            
        elif rec.bet_type == "Spread":
            # We need the spread line used at time of recommendation.
            # Currently Recommendation doesn't store the specific line, which is a flaw.
            # We'll use the closing line from odds as a proxy, or parse from reasoning string if possible.
            # Reasoning: "Simulated Spread: -5.5 vs Vegas: -2.0..."
            
            # For now, let's look at the latest odds associated with the game
            if not game.odds:
                continue
            odds = game.odds[-1]
            spread = odds.spread_points # e.g. -5.5 (Home favored by 5.5)
            
            if spread is None:
                continue
                
            # If pick is Home Team
            if rec.recommended_pick == game.home_team.name:
                # Home Score + Spread > Away Score?
                # e.g. Home 100, Away 90. Spread -5.5. 100 + (-5.5) = 94.5 > 90. Win.
                # e.g. Home 100, Away 98. Spread -5.5. 94.5 < 98. Loss.
                margin = game.home_score - game.away_score
                won = (margin + spread > 0)
            else:
                # Away Team
                # Usually spread is inverted for away? 
                # DB stores 'spread_points' usually for Home team perspective in this app (based on brain.py reading)
                # Let's assume spread_points is Home Spread.
                # So Away Spread is -1 * spread_points.
                margin = game.away_score - game.home_score
                won = (margin + (-1 * spread) > 0)

        elif rec.bet_type == "Total":
            if not game.odds: continue
            odds = game.odds[-1]
            total_line = odds.total_points
            
            if total_line is None: continue
            
            actual_total = game.home_score + game.away_score
            if rec.recommended_pick == "Over":
                won = actual_total > total_line
            else:
                won = actual_total < total_line

        # Update Stats
        total += 1
        if won: correct += 1
        
        # Type Stats
        if rec.bet_type not in by_type: by_type[rec.bet_type] = [0, 0]
        by_type[rec.bet_type][1] += 1
        if won: by_type[rec.bet_type][0] += 1
        
        # Confidence Stats
        conf = rec.confidence_score
        if conf >= 0.7:
            key = "High (70%+)"
        elif conf >= 0.55:
            key = "Medium (55-70%)"
        else:
            key = "Low (<55%)"
        
        by_confidence[key][1] += 1
        if won: by_confidence[key][0] += 1

    print("\n=== Results ===")
    if total == 0:
        print("No valid recommendations evaluated (missing odds/lines).")
        return

    print(f"Overall Accuracy: {correct}/{total} ({correct/total:.1%})")
    
    print("\nBy Bet Type:")
    for btype, (c, t) in by_type.items():
        if t > 0:
            print(f"  {btype}: {c}/{t} ({c/t:.1%})")
            
    print("\nBy Confidence:")
    for conf, (c, t) in by_confidence.items():
        if t > 0:
            print(f"  {conf}: {c}/{t} ({c/t:.1%})")

if __name__ == "__main__":
    evaluate_accuracy()
