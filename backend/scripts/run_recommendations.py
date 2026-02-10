import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DATABASE_URL
from app.routers.recommendations import generate_recommendations
from app.dependencies import get_db

def run_recs():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    print("Generating recommendations...")
    recs = generate_recommendations(db=db)
    
    print(f"Generated {len(recs)} recommendations.")
    for rec in recs:
        print(f"[{rec.bet_type}] {rec.recommended_pick} (Conf: {rec.confidence_score:.2f})")
        print(f"  Reason: {rec.reasoning}")

if __name__ == "__main__":
    run_recs()
