from app.database import SessionLocal
from app.models import PlayerProps
from sqlalchemy import func

def check_props():
    db = SessionLocal()
    try:
        count = db.query(PlayerProps).count()
        print(f"Total Player Props: {count}")
        
        # Breakdown by type
        stats = db.query(PlayerProps.prop_type, func.count(PlayerProps.id)).group_by(PlayerProps.prop_type).all()
        print("\nBreakdown by type:")
        for pt, c in stats:
            print(f"- {pt}: {c}")
            
        # Sample recent
        recent = db.query(PlayerProps).order_by(PlayerProps.timestamp.desc()).limit(10).all()
        print("\nRecent 10 props:")
        for p in recent:
            print(f"- Player ID: {p.player_id}, Type: {p.prop_type}, Line: {p.line}, Over: {p.over_odds}, Under: {p.under_odds}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_props()
