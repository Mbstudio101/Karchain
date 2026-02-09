import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.espn_sync import sync_upcoming_games
from scrapers.fanduel_scraper import FanDuelScraper
from app.routers.recommendations import generate_recommendations
from app.database import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MasterSync")

async def run_sync():
    logger.info("=== Starting Master Sync Cycle ===")
    start_time = datetime.now()
    
    # 1. Sync Games & Player Stats from ESPN
    logger.info("Step 1: Syncing ESPN Game Data & Player Stats...")
    try:
        # Sync today, tomorrow, and next day
        sync_upcoming_games(3)
        logger.info("ESPN Sync Complete.")
    except Exception as e:
        logger.error(f"ESPN Sync Failed: {e}")

    # 2. Sync Odds from FanDuel
    logger.info("Step 2: Scrapping FanDuel Odds...")
    scraper = FanDuelScraper(headless=True)
    try:
        await scraper.start()
        await scraper.scrape_nba_odds()
        logger.info("FanDuel Scrape Complete.")
    except Exception as e:
        logger.error(f"FanDuel Scrape Failed: {e}")
    finally:
        await scraper.close()

    # 3. Refresh AI Recommendations
    logger.info("Step 3: Refreshing AI Recommendations...")
    db = SessionLocal()
    try:
        generate_recommendations(db=db)
        logger.info("AI Analysis Refresh Complete.")
    except Exception as e:
        logger.error(f"AI Refresh Failed: {e}")
    finally:
        db.close()

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"=== Master Sync Cycle Finished (Duration: {duration}) ===")

if __name__ == "__main__":
    try:
        asyncio.run(run_sync())
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user.")
    except Exception as e:
        logger.error(f"Critical error in master sync: {e}")
