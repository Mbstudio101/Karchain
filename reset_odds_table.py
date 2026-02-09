from app.database import engine, Base
from app.models import BettingOdds
from sqlalchemy import text

def reset_odds_table():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS betting_odds CASCADE"))
        conn.commit()
    
    Base.metadata.create_all(bind=engine)
    print("BettingOdds table reset.")

if __name__ == "__main__":
    reset_odds_table()
