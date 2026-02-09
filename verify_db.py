from app.database import SessionLocal
from app.models import BettingOdds, Game, Team
from sqlalchemy.orm import joinedload

session = SessionLocal()
odds = session.query(BettingOdds).options(joinedload(BettingOdds.game)).all()

print(f"Found {len(odds)} odds entries.")
for odd in odds:
    game = odd.game
    home = session.query(Team).get(game.home_team_id)
    away = session.query(Team).get(game.away_team_id)
    print(f"Game: {away.name} @ {home.name} | Spread: {odd.home_spread_price}/{odd.away_spread_price} | Money: {odd.home_moneyline}/{odd.away_moneyline} | Total: {odd.total_points}")

session.close()
