import asyncio
import logging
from scrapers.fanduel_scraper import FanDuelScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NicheTest")

async def test_niche():
    # Target a specific game known to have deep markets
    url = "https://sportsbook.fanduel.com/basketball/nba/detroit-pistons-@-charlotte-hornets-35025251"
    home_team = "Charlotte Hornets"
    away_team = "Detroit Pistons"
    
    scraper = FanDuelScraper(headless=True)
    try:
        await scraper.start()
        logger.info(f"Targeting game detail: {url}")
        
        # Give it some time to load
        await scraper.page.goto(url, timeout=60000)
        await asyncio.sleep(5)
        await scraper.handle_captcha(scraper.page)
        await scraper.page.screenshot(path="niche_debug.png")
        
        # We call scrape_game_props directly using the scraper's page for better context
        await scraper.scrape_game_props(url, home_team, away_team)
        
        logger.info("Test scrape complete.")
    except Exception as e:
        logger.error(f"Test scrape failed: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_niche())
