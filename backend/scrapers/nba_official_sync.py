#!/usr/bin/env python3
"""
NBA Official Data Fetcher for Karchain Backend

This script fetches comprehensive NBA statistics from the official NBA API
and integrates with your existing database and analytics system.

Endpoints discovered from your NBA links:
- Player traditional, clutch, defense, hustle stats
- Team traditional, defense, hustle stats
- Advanced shooting and transition statistics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app import models, schemas
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBAOfficialDataFetcher:
    """Fetches NBA data from official API and integrates with Karchain backend"""
    
    BASE_URL = "https://stats.nba.com/stats"
    
    # Headers required for NBA API access
    HEADERS = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'stats.nba.com',
        'Origin': 'https://www.nba.com',
        'Referer': 'https://www.nba.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-nba-stats-origin': 'stats',
        'x-nba-stats-token': 'true'
    }
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def fetch_endpoint(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Fetch data from NBA API endpoint"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            logger.info(f"Fetching {endpoint} with params: {params}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'resultSets' in data and len(data['resultSets']) > 0:
                return data
            else:
                logger.warning(f"No data returned for {endpoint}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {endpoint}: {e}")
            return None
    
    def fetch_player_traditional_stats(self, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Fetch traditional player statistics"""
        params = {
            'Season': season,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'Totals',
            'MeasureType': 'Base',
            'LastNGames': 0,
            'Month': 0,
            'OpponentTeamID': 0,
            'PaceAdjust': 'N',
            'Period': 0,
            'PlusMinus': 'N',
            'Rank': 'N',
            'TeamID': 0
        }
        
        data = self.fetch_endpoint('leaguedashplayerstats', params)
        if data:
            result_set = data['resultSets'][0]
            df = pd.DataFrame(result_set['rowSet'], columns=result_set['headers'])
            
            # Add metadata
            df['season'] = season
            df['stat_type'] = 'traditional'
            df['fetched_at'] = datetime.now()
            
            logger.info(f"Fetched traditional stats for {len(df)} players")
            return df
        return None
    
    def fetch_player_advanced_stats(self, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Fetch advanced player statistics"""
        params = {
            'Season': season,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'Totals',
            'MeasureType': 'Advanced',
            'LastNGames': 0,
            'Month': 0,
            'OpponentTeamID': 0,
            'PaceAdjust': 'N',
            'Period': 0,
            'PlusMinus': 'N',
            'Rank': 'N',
            'TeamID': 0
        }
        
        data = self.fetch_endpoint('leaguedashplayerstats', params)
        if data:
            result_set = data['resultSets'][0]
            df = pd.DataFrame(result_set['rowSet'], columns=result_set['headers'])
            
            # Add metadata
            df['season'] = season
            df['stat_type'] = 'advanced'
            df['fetched_at'] = datetime.now()
            
            logger.info(f"Fetched advanced stats for {len(df)} players")
            return df
        return None
    
    def fetch_player_clutch_stats(self, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Fetch clutch player statistics"""
        params = {
            'Season': season,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'Totals',
            'MeasureType': 'Base',
            'ClutchTime': 'Last 5 Minutes',
            'PointDiff': 5,
            'LastNGames': 0,
            'Month': 0,
            'OpponentTeamID': 0,
            'Period': 0,
            'Rank': 'N',
            'TeamID': 0
        }
        
        data = self.fetch_endpoint('leaguedashplayerclutch', params)
        if data:
            result_set = data['resultSets'][0]
            df = pd.DataFrame(result_set['rowSet'], columns=result_set['headers'])
            
            # Add metadata
            df['season'] = season
            df['stat_type'] = 'clutch'
            df['fetched_at'] = datetime.now()
            
            logger.info(f"Fetched clutch stats for {len(df)} players")
            return df
        return None
    
    def fetch_player_defense_stats(self, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Fetch player defense statistics"""
        params = {
            'Season': season,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'Totals',
            'DefenseCategory': 'Overall',
            'LastNGames': 0,
            'Month': 0,
            'OpponentTeamID': 0,
            'Period': 0,
            'TeamID': 0
        }
        
        data = self.fetch_endpoint('leaguedashptdefend', params)
        if data:
            result_set = data['resultSets'][0]
            df = pd.DataFrame(result_set['rowSet'], columns=result_set['headers'])
            
            # Add metadata
            df['season'] = season
            df['stat_type'] = 'defense'
            df['fetched_at'] = datetime.now()
            
            logger.info(f"Fetched defense stats for {len(df)} players")
            return df
        return None
    
    def fetch_player_hustle_stats(self, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Fetch player hustle statistics"""
        params = {
            'Season': season,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'Totals',
            'LastNGames': 0,
            'Month': 0,
            'OpponentTeamID': 0,
            'Period': 0,
            'TeamID': 0
        }
        
        data = self.fetch_endpoint('leaguehustlestatsplayer', params)
        if data:
            result_set = data['resultSets'][0]
            df = pd.DataFrame(result_set['rowSet'], columns=result_set['headers'])
            
            # Add metadata
            df['season'] = season
            df['stat_type'] = 'hustle'
            df['fetched_at'] = datetime.now()
            
            logger.info(f"Fetched hustle stats for {len(df)} players")
            return df
        return None
    
    def fetch_team_stats(self, season: str = "2023-24") -> Optional[pd.DataFrame]:
        """Fetch team statistics"""
        params = {
            'Season': season,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'Totals',
            'MeasureType': 'Base',
            'LastNGames': 0,
            'Month': 0,
            'OpponentTeamID': 0,
            'PaceAdjust': 'N',
            'Period': 0,
            'PlusMinus': 'N',
            'Rank': 'N',
            'TeamID': 0
        }
        
        data = self.fetch_endpoint('leaguedashteamstats', params)
        if data:
            result_set = data['resultSets'][0]
            df = pd.DataFrame(result_set['rowSet'], columns=result_set['headers'])
            
            # Add metadata
            df['season'] = season
            df['stat_type'] = 'team_traditional'
            df['fetched_at'] = datetime.now()
            
            logger.info(f"Fetched team stats for {len(df)} teams")
            return df
        return None
    
    def save_player_stats_to_db(self, df: pd.DataFrame, stat_type: str):
        """Save player statistics to database"""
        if df is None or df.empty:
            logger.warning(f"No data to save for {stat_type}")
            return
        
        try:
            # Convert DataFrame to database models
            for _, row in df.iterrows():
                # Create or update player stats record
                player_stats = models.PlayerStats(
                    player_id=row.get('PLAYER_ID'),
                    player_name=row.get('PLAYER_NAME'),
                    team_id=row.get('TEAM_ID'),
                    team_abbreviation=row.get('TEAM_ABBREVIATION'),
                    season=row.get('season'),
                    stat_type=stat_type,
                    games_played=row.get('GP', 0),
                    minutes_played=row.get('MIN', 0),
                    points=row.get('PTS', 0),
                    rebounds=row.get('REB', 0),
                    assists=row.get('AST', 0),
                    steals=row.get('STL', 0),
                    blocks=row.get('BLK', 0),
                    turnovers=row.get('TOV', 0),
                    field_goals_made=row.get('FGM', 0),
                    field_goals_attempted=row.get('FGA', 0),
                    field_goal_percentage=row.get('FG_PCT', 0),
                    three_points_made=row.get('FG3M', 0),
                    three_points_attempted=row.get('FG3A', 0),
                    three_point_percentage=row.get('FG3_PCT', 0),
                    free_throws_made=row.get('FTM', 0),
                    free_throws_attempted=row.get('FTA', 0),
                    free_throw_percentage=row.get('FT_PCT', 0),
                    plus_minus=row.get('PLUS_MINUS', 0),
                    # Store raw data as JSON
                    raw_data=row.to_dict(),
                    fetched_at=row.get('fetched_at', datetime.now())
                )
                
                self.db.merge(player_stats)
            
            self.db.commit()
            logger.info(f"Saved {len(df)} {stat_type} player stats to database")
            
        except Exception as e:
            logger.error(f"Error saving {stat_type} stats to database: {e}")
            self.db.rollback()
    
    def save_team_stats_to_db(self, df: pd.DataFrame):
        """Save team statistics to database"""
        if df is None or df.empty:
            logger.warning("No team data to save")
            return
        
        try:
            # Convert DataFrame to database models
            for _, row in df.iterrows():
                team_stats = models.TeamStats(
                    team_id=row.get('TEAM_ID'),
                    team_name=row.get('TEAM_NAME'),
                    season=row.get('season'),
                    games_played=row.get('GP', 0),
                    wins=row.get('W', 0),
                    losses=row.get('L', 0),
                    win_percentage=row.get('W_PCT', 0),
                    points_per_game=row.get('PTS', 0),
                    rebounds_per_game=row.get('REB', 0),
                    assists_per_game=row.get('AST', 0),
                    steals_per_game=row.get('STL', 0),
                    blocks_per_game=row.get('BLK', 0),
                    turnovers_per_game=row.get('TOV', 0),
                    field_goal_percentage=row.get('FG_PCT', 0),
                    three_point_percentage=row.get('FG3_PCT', 0),
                    free_throw_percentage=row.get('FT_PCT', 0),
                    # Store raw data as JSON
                    raw_data=row.to_dict(),
                    fetched_at=row.get('fetched_at', datetime.now())
                )
                
                self.db.merge(team_stats)
            
            self.db.commit()
            logger.info(f"Saved {len(df)} team stats to database")
            
        except Exception as e:
            logger.error(f"Error saving team stats to database: {e}")
            self.db.rollback()
    
    def fetch_all_stats(self, season: str = "2023-24") -> Dict[str, pd.DataFrame]:
        """Fetch all NBA statistics for the season"""
        all_stats = {}
        
        logger.info(f"Fetching all NBA stats for {season} season...")
        
        # Player stats
        all_stats['player_traditional'] = self.fetch_player_traditional_stats(season)
        all_stats['player_advanced'] = self.fetch_player_advanced_stats(season)
        all_stats['player_clutch'] = self.fetch_player_clutch_stats(season)
        all_stats['player_defense'] = self.fetch_player_defense_stats(season)
        all_stats['player_hustle'] = self.fetch_player_hustle_stats(season)
        
        # Team stats
        all_stats['team_traditional'] = self.fetch_team_stats(season)
        
        # Save all to database
        for stat_type, df in all_stats.items():
            if df is not None and not df.empty:
                if 'player' in stat_type:
                    self.save_player_stats_to_db(df, stat_type.replace('player_', ''))
                else:
                    self.save_team_stats_to_db(df)
        
        return all_stats
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

def main():
    """Main function to run the NBA data fetcher"""
    fetcher = NBAOfficialDataFetcher()
    
    try:
        logger.info("Starting NBA Official Data Fetcher...")
        
        # Fetch all stats for current season
        season = "2023-24"
        all_stats = fetcher.fetch_all_stats(season)
        
        # Print summary
        logger.info("\n=== NBA Data Fetch Summary ===")
        for stat_type, df in all_stats.items():
            if df is not None and not df.empty:
                logger.info(f"✅ {stat_type}: {len(df)} records")
            else:
                logger.warning(f"❌ {stat_type}: No data fetched")
        
        logger.info("NBA data fetching completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    finally:
        fetcher.close()

if __name__ == "__main__":
    main()