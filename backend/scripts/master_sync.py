import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.espn_sync import sync_upcoming_games
from scrapers.nba_official_sync import sync_official_scoreboard
from scrapers.injury_sync import sync_nba_injuries
from scrapers.fanduel_scraper import FanDuelScraper
from scrapers.bettingpros_scraper import BettingProsScraper
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

async def run_sync_once():
    logger.info("=== Starting Sync Cycle ===")
    start_time = datetime.now()
    
    # 1. Sync Games & Player Stats
    logger.info("Step 1: Syncing NBA Game Data & Injuries...")
    try:
        sync_official_scoreboard()
        sync_upcoming_games(3)
        sync_nba_injuries()
        logger.info("NBA Sync Complete.")
    except Exception as e:
        logger.error(f"NBA Sync Failed: {e}")

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

    # 3. Sync Odds & Props from BettingPros
    logger.info("Step 3: Scrapping BettingPros Odds & Props...")
    bp_scraper = BettingProsScraper(headless=True)
    try:
        # Fetch game lines and player props
        await bp_scraper.scrape_nba_data()
        # Fetch pre-analyzed prop data (star ratings, EV, performance)
        await bp_scraper.scrape_prop_analyzer()
        logger.info("BettingPros Scrape Complete.")
    except Exception as e:
        logger.error(f"BettingPros Scrape Failed: {e}")
    finally:
        await bp_scraper.close()

    # 4. Refresh AI Recommendations
    logger.info("Step 4: Refreshing AI Recommendations...")
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
    logger.info(f"=== Sync Cycle Finished (Duration: {duration}) ===")

async def main_loop(interval_minutes: int = 30):
    logger.info(f"Starting Master Sync Loop. Interval: {interval_minutes} minutes.")
    while True:
        try:
            await run_sync_once()
        except Exception as e:
            logger.error(f"Unexpected error in sync loop: {e}")
        
        logger.info(f"Sleeping for {interval_minutes} minutes...")
        await asyncio.sleep(interval_minutes * 60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Karchain Master Sync Service")
    parser.add_argument("--loop", action="store_true", help="Run in a continuous loop")
    parser.add_argument("--interval", type=int, default=30, help="Sync interval in minutes (default: 30)")
    args = parser.parse_args()

    try:
        if args.loop:
            asyncio.run(main_loop(args.interval))
        else:
            asyncio.run(run_sync_once())
    except KeyboardInterrupt:
        logger.info("Sync service stopped by user.")
    except Exception as e:
        logger.error(f"Critical error in master sync service: {e}")
