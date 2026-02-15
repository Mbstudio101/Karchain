import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models
from scrapers.espn_sync import sync_espn_data
from scrapers.bettingpros_scraper import BettingProsScraper
from scrapers.team_stats_sync import sync_all_team_metrics
import asyncio
import threading

logger = logging.getLogger(__name__)

class DataSyncService:
    """
    Service to automatically sync NBA data when the database is empty or outdated.
    """
    
    @staticmethod
    def sync_if_needed(db: Session, force: bool = False) -> bool:
        """
        Sync data if needed. Returns True if sync was performed.
        """
        today = datetime.utcnow().date()
        
        # Check if we have games for today
        today_games = db.query(models.Game).filter(
            models.Game.game_date >= today,
            models.Game.game_date < today + timedelta(days=1)
        ).count()
        
        # Check if we have games for tomorrow (in case games start early)
        tomorrow = today + timedelta(days=1)
        tomorrow_games = db.query(models.Game).filter(
            models.Game.game_date >= tomorrow,
            models.Game.game_date < tomorrow + timedelta(days=1)
        ).count()
        
        total_games = today_games + tomorrow_games
        
        if total_games == 0 or force:
            logger.info(f"Database sync needed. Found {today_games} today games and {tomorrow_games} tomorrow games.")
            return DataSyncService.perform_sync(db)
        else:
            logger.info(f"Database is up to date. Found {total_games} games for today and tomorrow.")
            return False
    
    @staticmethod
    def perform_sync(db: Session) -> bool:
        """
        Perform the actual data sync.
        """
        try:
            logger.info("Starting data sync...")
            
            # 1. Sync ESPN data for today and tomorrow
            today_str = datetime.utcnow().strftime('%Y%m%d')
            tomorrow_str = (datetime.utcnow() + timedelta(days=1)).strftime('%Y%m%d')
            
            logger.info("Syncing ESPN data for today...")
            sync_espn_data(today_str)
            
            logger.info("Syncing ESPN data for tomorrow...")
            sync_espn_data(tomorrow_str)
            
            # 2. Sync team metrics (real NBA data + allowed opponent splits)
            logger.info("Syncing team metrics...")
            sync_all_team_metrics()

            # 3. Sync BettingPros data
            logger.info("Syncing BettingPros data...")
            DataSyncService._run_async_safely(DataSyncService._sync_bettingpros())
            
            logger.info("Data sync completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Data sync failed: {e}")
            return False
    
    @staticmethod
    async def _sync_bettingpros():
        """
        Sync BettingPros data asynchronously.
        """
        scraper = BettingProsScraper()
        await scraper.scrape_nba_data()
        await scraper.scrape_prop_analyzer()

    @staticmethod
    def _run_async_safely(coro):
        """
        Run async work from sync code, even when already inside an event loop.
        """
        try:
            asyncio.get_running_loop()
            has_running_loop = True
        except RuntimeError:
            has_running_loop = False

        if not has_running_loop:
            return asyncio.run(coro)

        err_holder = []

        def _runner():
            try:
                asyncio.run(coro)
            except Exception as exc:
                err_holder.append(exc)

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        t.join()
        if err_holder:
            raise err_holder[0]

# Global instance
data_sync_service = DataSyncService()
