from app.database import SessionLocal
from app.routers.games import read_games
from datetime import date

db = SessionLocal()
try:
    print("Calling read_games...")
    games = read_games(db=db)
    print(f"Success! Found {len(games)} games.")
except Exception as e:
    import traceback
    print(f"Error caught: {e}")
    traceback.print_exc()
finally:
    db.close()
