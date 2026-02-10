import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models

db = SessionLocal()
try:
    game = db.query(models.Game).filter(models.Game.id == 14).first()
    if game:
        print(f"Game: {game.home_team.name} vs {game.away_team.name}")
        print(f"Date: {game.game_date}")
        print(f"Status: {game.status}")
        print(f"Scores: {game.home_score} - {game.away_score}")
    else:
        print("Game 14 not found")
finally:
    db.close()