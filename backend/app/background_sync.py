"""
Background synchronization service for continuous data updates.
This service runs 24/7 to keep NBA games and player props fresh.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import schedule
import time
from threading import Thread, Event
import os
import sys

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from scrapers.espn_sync import sync_espn_data
from scrapers.bettingpros_scraper import BettingProsScraper
from scrapers.stats_scraper import sync_player_stats_from_nba
from scrapers.team_stats_sync import sync_all_team_metrics
from app.websocket_manager import notify_games_updated, notify_players_updated, notify_props_updated
import asyncio
import threading

logger = logging.getLogger(__name__)

class BackgroundSyncService:
    """24/7 background service for automatic data synchronization."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.bettingpros_scraper = BettingProsScraper()
        self.stop_event = Event()
        self.sync_thread: Optional[Thread] = None
        
    def sync_games(self):
        """Sync NBA games from ESPN."""
        try:
            logger.info("Starting automatic game sync...")
            # Sync games for today and next 7 days
            today = datetime.now().strftime("%Y%m%d")
            games_synced = sync_espn_data(today)
            logger.info(f"Successfully synced games for {today}")
            
            # Notify connected clients of games update
            self._notify_update("games", {"synced_date": today, "timestamp": datetime.now().isoformat()})
            
        except Exception as e:
            logger.error(f"Game sync failed: {e}")
    
    def _notify_update(self, data_type: str, data: dict):
        """Send update notification to connected clients."""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if data_type == "games":
                loop.run_until_complete(notify_games_updated(data))
            elif data_type == "players":
                loop.run_until_complete(notify_players_updated(data))
            elif data_type == "player_props":
                loop.run_until_complete(notify_props_updated(data))
            
            loop.close()
            logger.info(f"Notified clients of {data_type} update")
            
        except Exception as e:
            logger.error(f"Failed to notify clients: {e}")
    
    def sync_player_props(self):
        """Sync player props from BettingPros."""
        try:
            logger.info("Starting automatic player props sync...")
            asyncio.run(self.bettingpros_scraper.scrape_nba_data())
            logger.info("Successfully synced player props")
            
            # Notify connected clients of props update
            self._notify_update("player_props", {"timestamp": datetime.now().isoformat()})
            
        except Exception as e:
            logger.error(f"Player props sync failed: {e}")

    def sync_player_stats(self):
        """Sync player historical stats from NBA.com."""
        try:
            logger.info("Starting automatic player stats sync...")
            sync_player_stats_from_nba()
            sync_all_team_metrics()
            logger.info("Successfully synced player stats")
            
            # Notify connected clients of players update
            self._notify_update("players", {"timestamp": datetime.now().isoformat()})
            
        except Exception as e:
            logger.error(f"Player stats sync failed: {e}")
    
    def sync_all_data(self):
        """Run complete data synchronization."""
        logger.info("Starting complete data sync cycle...")
        
        # Sync games first (needed for props linking)
        self.sync_games()
        
        # Wait a bit for games to be processed
        time.sleep(30)
        
        # Sync player stats (historical data)
        self.sync_player_stats()
        
        # Sync player props (future predictions)
        self.sync_player_props()
        
        logger.info("Complete data sync cycle finished")
    
    def run_scheduler(self):
        """Run the scheduling loop in a separate thread."""
        logger.info("Starting background sync scheduler...")
        
        # Schedule sync jobs
        schedule.every(30).minutes.do(self.sync_games)
        schedule.every(30).minutes.do(self.sync_player_props)
        schedule.every(12).hours.do(self.sync_player_stats)
        
        # Keep startup light to avoid blocking API responsiveness.
        logger.info("Running light initial sync...")
        self.sync_games()
        
        # Main scheduling loop
        while not self.stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
        
        logger.info("Background sync scheduler stopped")
    
    def start(self):
        """Start the background sync service."""
        if self.sync_thread and self.sync_thread.is_alive():
            logger.warning("Sync service is already running")
            return
        
        logger.info("Starting background sync service...")
        self.stop_event.clear()
        self.sync_thread = Thread(target=self.run_scheduler, daemon=True)
        self.sync_thread.start()
        logger.info("Background sync service started successfully")
    
    def stop(self):
        """Stop the background sync service."""
        logger.info("Stopping background sync service...")
        self.stop_event.set()
        if self.sync_thread:
            self.sync_thread.join(timeout=10)
        logger.info("Background sync service stopped")
    
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self.sync_thread is not None and self.sync_thread.is_alive()

# Global instance
sync_service = BackgroundSyncService()

def start_background_sync():
    """Start the background sync service."""
    sync_service.start()

def stop_background_sync():
    """Stop the background sync service."""
    sync_service.stop()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('background_sync.log'),
            logging.StreamHandler()
        ]
    )
    
    # Start the service
    start_background_sync()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_background_sync()
        logger.info("Background sync service shutdown complete")
