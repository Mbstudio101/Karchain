import asyncio
from backend.scrapers.nba_scraper import NBAScraper
from app.database import SessionLocal, engine, Base
from app.models import Player, Team

async def main():
    Base.metadata.create_all(bind=engine)
    scraper = NBAScraper(headless=True)
    await scraper.start()
    try:
        await scraper.scrape_players()
        await scraper.scrape_team_stats()
        await scraper.scrape_player_stats()
    finally:
        await scraper.close()

    # Verify DB
    db = SessionLocal()
    player_count = db.query(Player).count()
    team_count = db.query(Team).count()
    print(f"Total Players in DB: {player_count}")
    print(f"Total Teams in DB: {team_count}")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
