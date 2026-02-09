"""
Karchain Brain - Automated Scheduler
Runs background jobs for scraping, analysis, and recommendations.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# --- Job Functions ---

def scrape_odds_job():
    """Scrape latest odds from FanDuel."""
    logger.info("🧠 BRAIN: Starting odds scrape job...")
    try:
        # Import here to avoid circular imports
        import subprocess
        result = subprocess.run(
            ["python3", "scrapers/fanduel_scraper.py"],
            cwd="/Users/marvens/Desktop/Karchain/backend",
            capture_output=True,
            text=True,
            timeout=300
        )
        logger.info(f"Odds scrape completed. Output: {result.stdout[:200] if result.stdout else 'No output'}")
    except Exception as e:
        logger.error(f"Odds scrape failed: {e}")

def generate_recommendations_job():
    """Trigger recommendation generation after scraping."""
    logger.info("🧠 BRAIN: Running recommendation engine...")
    try:
        import requests
        response = requests.post("http://localhost:8000/recommendations/generate", timeout=60)
        logger.info(f"Recommendations generated: {len(response.json())} new picks")
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")

def scrape_player_stats_job():
    """Daily refresh of player stats."""
    logger.info("🧠 BRAIN: Running daily player stats scrape...")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "scrapers/nba_player_stats_scraper.py"],
            cwd="/Users/marvens/Desktop/Karchain/backend",
            capture_output=True,
            text=True,
            timeout=600
        )
        logger.info(f"Player stats scrape completed. Output: {result.stdout[:200] if result.stdout else 'No output'}")
    except Exception as e:
        logger.error(f"Player stats scrape failed: {e}")

# --- Scheduler Setup ---

def start_scheduler():
    """Initialize and start the scheduler with all jobs."""
    # Odds scraping every 15 minutes
    scheduler.add_job(
        scrape_odds_job,
        IntervalTrigger(minutes=15),
        id="scrape_odds",
        name="Scrape Odds Every 15 Min",
        replace_existing=True
    )
    
    # Generate recommendations after odds (offset by 2 mins)
    scheduler.add_job(
        generate_recommendations_job,
        IntervalTrigger(minutes=15, start_date="2026-01-01 00:02:00"),
        id="generate_recommendations",
        name="Generate Recommendations",
        replace_existing=True
    )
    
    # Daily player stats at 6 AM
    scheduler.add_job(
        scrape_player_stats_job,
        CronTrigger(hour=6, minute=0),
        id="scrape_player_stats",
        name="Daily Player Stats Scrape",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🧠 BRAIN: Scheduler started with 3 jobs")
    
    # List all jobs
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}: Next run at {job.next_run_time}")

def shutdown_scheduler():
    """Gracefully shutdown the scheduler."""
    scheduler.shutdown()
    logger.info("🧠 BRAIN: Scheduler shutdown complete")

if __name__ == "__main__":
    # For testing
    start_scheduler()
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        shutdown_scheduler()
