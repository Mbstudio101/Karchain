from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Game, Team
from datetime import datetime, timedelta, date
import os
from dotenv import load_dotenv
from app.database import SessionLocal

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine) # This line is removed as SessionLocal is now imported
session = SessionLocal()

print("Checking games...")
now = datetime.utcnow()
live_games = session.query(Game).filter(Game.status == "Live").all()
print(f"Found {len(live_games)} Live games.")

for g in live_games:
    print(f"ID: {g.id} | Date: {g.game_date} | Teams: {g.home_team_id} vs {g.away_team_id}")
    if g.game_date < now - timedelta(hours=6):
        print("  -> Game is OLD and should be Final.")

# Show today's games
today = date(2026, 2, 8) # Fixed for this specific gameday in the prompt
today_games = session.query(Game).filter(
    Game.game_date >= datetime.combine(today, datetime.min.time()),
    Game.game_date <= datetime.combine(today, datetime.max.time())
).all()

print(f"\nGames for {today}:")
for g in today_games:
    home_name = g.home_team.name if g.home_team else "Unknown"
    away_name = g.away_team.name if g.away_team else "Unknown"
    print(f"ID: {g.id} | {away_name} @ {home_name} | Status: {g.status} | Score: {g.away_score}-{g.home_score}")

all_games = session.query(Game).order_by(Game.game_date.desc()).limit(10).all()
print("\nRecent 10 games in DB:")
for g in all_games:
    print(f"ID: {g.id} | Date: {g.game_date} | Status: {g.status} | Score: {g.away_score}-{g.home_score}")

session.close()
