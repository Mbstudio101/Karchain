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

def sync_master_job():
    """Run the complete master sync cycle."""
    logger.info("🧠 BRAIN: Starting Master Sync Cycle...")
    try:
        import subprocess
        # Run master_sync.py as a separate process to avoid any event loop conflicts with APScheduler
        result = subprocess.run(
            ["python3", "scripts/master_sync.py"],
            cwd="/Users/marvens/Desktop/Karchain/backend",
            capture_output=True,
            text=True,
            timeout=1200 # 20 minutes max
        )
        logger.info(f"Master sync completed. Output length: {len(result.stdout) if result.stdout else 0}")
    except Exception as e:
        logger.error(f"Master sync job failed: {e}")

def scrape_player_stats_job():
    """Daily refresh of player stats."""
    logger.info("🧠 BRAIN: Running daily player stats scrape...")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "scrapers.nba_scraper"],
            cwd="/Users/marvens/Desktop/Karchain/backend",
            capture_output=True,
            text=True,
            timeout=1200
        )
        logger.info(f"Player stats scrape completed. Output: {result.stdout[:200] if result.stdout else 'No output'}")
    except Exception as e:
        logger.error(f"Player stats scrape failed: {e}")

# --- Scheduler Setup ---

def start_scheduler():
    """Initialize and start the scheduler with the master sync job."""
    
    # 1. Run the full master sync every 30 minutes
    # This covers Games, Injuries, Odds, and AI Recommendations
    scheduler.add_job(
        sync_master_job,
        IntervalTrigger(minutes=30),
        id="master_sync",
        name="Master Sync Cycle",
        replace_existing=True
    )
    
    # 2. Daily player stats at 6 AM
    scheduler.add_job(
        scrape_player_stats_job,
        CronTrigger(hour=6, minute=0),
        id="scrape_player_stats",
        name="Daily Player Stats Scrape",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🧠 BRAIN: Scheduler started with Master Sync cycle")
    
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
