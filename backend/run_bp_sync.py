
import asyncio
import logging
from scrapers.bettingpros_scraper import BettingProsScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_bettingpros_sync():
    logger.info("Starting BettingPros Sync...")
    scraper = BettingProsScraper(headless=True)
    try:
        # Fetch game lines and player props
        await scraper.scrape_nba_data()
        # Fetch pre-analyzed prop data (star ratings, EV, performance)
        await scraper.scrape_prop_analyzer()
        logger.info("BettingPros Scrape Complete.")
    except Exception as e:
        logger.error(f"BettingPros Scrape Failed: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(run_bettingpros_sync())
