#!/usr/bin/env python3
"""
Karchain NBA Fetcher - The Ultimate Data Ingestion Engine

Combines database integration with advanced bot-detection bypassing techniques
to reliably fetch high-fidelity NBA statistics.
"""

import sys
import os
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from curl_cffi import requests

# Add parent directory to path for database imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, create_tables
from app import models
from app.models_nba_official import NBAOfficialPlayerStats, NBAOfficialTeamStats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KarchainNBAFetcher:
    """
    Production-ready NBA data fetcher that uses advanced browser impersonation
    to bypass bot detection and save data directly to the Karchain database.
    """
    
    BASE_URL = "https://stats.nba.com/stats"
    
    # Browser impersonation configurations
    BROWSER_CONFIGS = [
        {
            "name": "Chrome 120",
            "impersonate": "chrome120",
            "headers": {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Host': 'stats.nba.com',
                'Origin': 'https://www.nba.com',
                'Referer': 'https://www.nba.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'x-nba-stats-origin': 'stats',
                'x-nba-stats-token': 'true'
            }
        },
        {
            "name": "Safari 17",
            "impersonate": "safari17_0",
            "headers": {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Host': 'stats.nba.com',
                'Origin': 'https://www.nba.com',
                'Referer': 'https://www.nba.com/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'x-nba-stats-origin': 'stats',
                'x-nba-stats-token': 'true'
            }
        }
    ]
    
    def __init__(self, db_session=None):
        self.db = db_session or next(get_db())
        self.session = requests.Session()
        self.request_count = 0
    
    def get_browser_config(self, index: int = 0) -> Dict[str, Any]:
        """Get browser configuration by index"""
        return self.BROWSER_CONFIGS[index % len(self.BROWSER_CONFIGS)]
    
    def fetch_endpoint(self, endpoint: str, params: Dict[str, Any], max_retries: int = 3) -> Optional[Dict]:
        """
        Fetch NBA API endpoint with retry logic and browser rotation
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(max_retries):
            # Rotate browser config for each attempt
            config = self.get_browser_config(self.request_count + attempt)
            
            try:
                # Add random delay to avoid detection
                if self.request_count > 0:
                    delay = random.uniform(2, 5) + (attempt * 2)
                    logger.info(f"⏱️  Waiting {delay:.1f}s...")
                    time.sleep(delay)
                
                logger.info(f"🎯 Fetching {endpoint} (Attempt {attempt+1}/{max_retries})")
                
                response = self.session.get(
                    url,
                    params=params,
                    headers=config['headers'],
                    impersonate=config['impersonate'],
                    timeout=30
                )
                
                self.request_count += 1
                
                if response.status_code == 200:
                    data = response.json()
                    if 'resultSets' in data and len(data['resultSets']) > 0:
                        logger.info(f"✅ Successfully fetched {endpoint}")
                        return data
                    else:
                        logger.warning(f"⚠️ Empty result set for {endpoint}")
                
                elif response.status_code == 403:
                    logger.warning(f"🚫 403 Forbidden. Retrying with different browser...")
                
                elif response.status_code == 429:
                    logger.warning(f"⏰ Rate limited. Waiting 15s...")
                    time.sleep(15)
                
                else:
                    logger.warning(f"❌ Status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"💥 Error: {e}")
                
        logger.error(f"❌ Failed to fetch {endpoint} after {max_retries} attempts")
        return None

    def fetch_hustle_stats(self, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Fetch player hustle statistics"""
        params = {
            'Season': season,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'Totals'
        }
        
        data = self.fetch_endpoint('leaguehustlestatsplayer', params)
        if data:
            result_set = data['resultSets'][0]
            df = pd.DataFrame(result_set['rowSet'], columns=result_set['headers'])
            df['season'] = season
            df['stat_type'] = 'hustle'
            df['fetched_at'] = datetime.now()
            return df
        return None

    def fetch_defense_stats(self, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Fetch player defense statistics"""
        params = {
            'Season': season,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'Totals',
            'DefenseCategory': 'Overall'
        }
        
        data = self.fetch_endpoint('leaguedashptdefend', params)
        if data:
            result_set = data['resultSets'][0]
            df = pd.DataFrame(result_set['rowSet'], columns=result_set['headers'])
            df['season'] = season
            df['stat_type'] = 'defense'
            df['fetched_at'] = datetime.now()
            return df
        return None

    def save_to_db(self, df: pd.DataFrame, stat_type: str):
        """Save statistics to database"""
        if df is None or df.empty:
            logger.warning(f"No data to save for {stat_type}")
            return
            
        try:
            logger.info(f"💾 Saving {len(df)} {stat_type} records to database...")
            
            for _, row in df.iterrows():
                # Create NBA official stats record with all the valuable data
                nba_stats = NBAOfficialPlayerStats(
                    player_id=row.get('PLAYER_ID') or row.get('CLOSE_DEF_PERSON_ID'),
                    player_name=row.get('PLAYER_NAME'),
                    team_id=row.get('TEAM_ID') or row.get('PLAYER_LAST_TEAM_ID'),
                    team_abbreviation=row.get('TEAM_ABBREVIATION') or row.get('PLAYER_LAST_TEAM_ABBREVIATION'),
                    season=row.get('season'),
                    season_type='Regular Season',
                    
                    # Basic stats
                    games_played=row.get('G') or row.get('GP'),
                    minutes_played=row.get('MIN', 0),
                    age=row.get('AGE'),
                    position=row.get('PLAYER_POSITION'),
                    
                    # Hustle stats (if available)
                    contested_shots=row.get('CONTESTED_SHOTS', 0),
                    contested_shots_2pt=row.get('CONTESTED_SHOTS_2PT', 0),
                    contested_shots_3pt=row.get('CONTESTED_SHOTS_3PT', 0),
                    deflections=row.get('DEFLECTIONS', 0),
                    charges_drawn=row.get('CHARGES_DRAWN', 0),
                    screen_assists=row.get('SCREEN_ASSISTS', 0),
                    screen_assist_points=row.get('SCREEN_AST_PTS', 0),
                    loose_balls_recovered=row.get('LOOSE_BALLS_RECOVERED', 0),
                    off_loose_balls_recovered=row.get('OFF_LOOSE_BALLS_RECOVERED', 0),
                    def_loose_balls_recovered=row.get('DEF_LOOSE_BALLS_RECOVERED', 0),
                    box_outs=row.get('BOX_OUTS', 0),
                    off_box_outs=row.get('OFF_BOXOUTS', 0),
                    def_box_outs=row.get('DEF_BOXOUTS', 0),
                    box_out_team_rebounds=row.get('BOX_OUT_PLAYER_TEAM_REBS', 0),
                    box_out_player_rebounds=row.get('BOX_OUT_PLAYER_REBS', 0),
                    
                    # Defense stats (if available)
                    defense_frequency=row.get('FREQ', 0),
                    defense_fgm=row.get('D_FGM', 0),
                    defense_fga=row.get('D_FGA', 0),
                    defense_fg_percentage=row.get('D_FG_PCT', 0),
                    defense_fg_percentage_diff=row.get('PCT_PLUSMINUS', 0),
                    
                    # Store raw data for future analysis
                    raw_data=None,  # Optimization: Don't store full raw dict to save space
                    stat_type=stat_type
                )
                
                self.db.merge(nba_stats)
            
            self.db.commit()
            logger.info(f"✅ Successfully saved {stat_type} stats!")
            
            # Verify the data was saved
            verification_count = self.db.query(NBAOfficialPlayerStats).filter(NBAOfficialPlayerStats.stat_type == stat_type).count()
            logger.info(f"📊 Verification: Found {verification_count} {stat_type} records in database")
            
        except Exception as e:
            logger.error(f"💥 Database error: {e}")
            self.db.rollback()
            # Don't raise, just log error so other stats can still be processed
            pass

    def run_sync(self, season: str = "2023-24"):
        """Run full synchronization of all hidden stats"""
        logger.info(f"🚀 Starting Karchain NBA Sync for {season}...")
        
        # 1. Fetch Hustle Stats
        hustle_df = self.fetch_hustle_stats(season)
        self.save_to_db(hustle_df, 'hustle')
        
        # 2. Fetch Defense Stats
        defense_df = self.fetch_defense_stats(season)
        self.save_to_db(defense_df, 'defense')
        
        logger.info("🎉 Sync complete! Database updated with hidden stats.")

def main():
    # Create database tables first
    create_tables()
    
    fetcher = KarchainNBAFetcher()
    fetcher.run_sync()

if __name__ == "__main__":
    main()
