#!/usr/bin/env python3
"""
NBA Official API Endpoint Discovery and Data Fetcher

This script maps the hidden NBA API endpoints behind the NBA.com stats pages
and provides functions to fetch comprehensive NBA statistics data.

Based on the NBA links provided and reverse-engineering of NBA.com
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBAOfficialAPI:
    """NBA Official API Client for hidden endpoints"""
    
    BASE_URL = "https://stats.nba.com/stats"
    
    # Headers required to access NBA API
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
    
    # Mapping of NBA.com pages to their corresponding API endpoints
    ENDPOINT_MAPPING = {
        # Player Statistics
        'https://www.nba.com/stats/players/traditional': {
            'endpoint': 'leaguedashplayerstats',
            'measure_type': 'Base',
            'description': 'Traditional Player Stats (Points, Rebounds, Assists, etc.)'
        },
        'https://www.nba.com/stats/players/clutch-traditional': {
            'endpoint': 'leaguedashplayerclutch',
            'measure_type': 'Base',
            'description': 'Clutch Player Stats (Last 5 min, +/- 5 points)'
        },
        'https://www.nba.com/stats/players/shots-general': {
            'endpoint': 'leaguedashplayershotlocations',
            'measure_type': 'Base',
            'description': 'Player Shot Locations and General Shooting Stats'
        },
        'https://www.nba.com/stats/players/defense-dash-overall': {
            'endpoint': 'leaguedashptdefend',
            'measure_type': 'Base',
            'description': 'Player Defense Stats (Defended FG%, etc.)'
        },
        'https://www.nba.com/stats/players/transition': {
            'endpoint': 'leaguedashptstats',
            'measure_type': 'Transition',
            'description': 'Player Transition Stats (Fast break, etc.)'
        },
        'https://www.nba.com/stats/players/catch-shoot': {
            'endpoint': 'leaguedashptstats',
            'measure_type': 'CatchShoot',
            'description': 'Player Catch and Shoot Stats'
        },
        'https://www.nba.com/stats/players/shooting': {
            'endpoint': 'leaguedashplayershotlocations',
            'measure_type': 'Base',
            'description': 'Player Shooting Stats by Distance'
        },
        'https://www.nba.com/stats/players/opponent-shooting': {
            'endpoint': 'leaguedashptdefend',
            'measure_type': 'Base',
            'description': 'Player Opponent Shooting Stats'
        },
        'https://www.nba.com/stats/players/hustle': {
            'endpoint': 'leaguehustlestatsplayer',
            'measure_type': 'Base',
            'description': 'Player Hustle Stats (Loose balls, charges, etc.)'
        },
        'https://www.nba.com/stats/players/box-outs': {
            'endpoint': 'leaguehustlestatsplayer',
            'measure_type': 'Base',
            'description': 'Player Box Out Stats'
        },
        
        # Team Statistics
        'https://www.nba.com/stats/teams/traditional': {
            'endpoint': 'leaguedashteamstats',
            'measure_type': 'Base',
            'description': 'Traditional Team Stats'
        },
        'https://www.nba.com/stats/teams': {
            'endpoint': 'leaguedashteamstats',
            'measure_type': 'Base',
            'description': 'General Team Stats'
        },
        'https://www.nba.com/stats/teams/boxscores': {
            'endpoint': 'leaguegamelog',
            'measure_type': 'Base',
            'description': 'Team Box Scores'
        },
        'https://www.nba.com/stats/teams/box-outs': {
            'endpoint': 'leaguehustlestatsteam',
            'measure_type': 'Base',
            'description': 'Team Box Out Stats'
        },
        'https://www.nba.com/stats/teams/hustle': {
            'endpoint': 'leaguehustlestatsteam',
            'measure_type': 'Base',
            'description': 'Team Hustle Stats'
        },
        'https://www.nba.com/stats/teams/opponent-shooting': {
            'endpoint': 'leaguedashptdefend',
            'measure_type': 'Base',
            'description': 'Team Opponent Shooting Stats'
        },
        'https://www.nba.com/stats/teams/shooting': {
            'endpoint': 'leaguedashplayershotlocations',
            'measure_type': 'Base',
            'description': 'Team Shooting Stats'
        },
        'https://www.nba.com/stats/teams/catch-shoot': {
            'endpoint': 'leaguedashptstats',
            'measure_type': 'CatchShoot',
            'description': 'Team Catch and Shoot Stats'
        },
        'https://www.nba.com/stats/teams/shots-general': {
            'endpoint': 'leaguedashplayershotlocations',
            'measure_type': 'Base',
            'description': 'Team Shot Locations'
        },
        'https://www.nba.com/stats/teams/clutch-traditional': {
            'endpoint': 'leaguedashplayerclutch',
            'measure_type': 'Base',
            'description': 'Team Clutch Stats'
        },
        'https://www.nba.com/stats/teams/defense-dash-overall': {
            'endpoint': 'leaguedashptdefend',
            'measure_type': 'Base',
            'description': 'Team Defense Stats'
        }
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def make_api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make request to NBA API endpoint"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {endpoint}: {e}")
            return None
    
    def get_player_traditional_stats(self, season: str = "2023-24", season_type: str = "Regular Season") -> Optional[pd.DataFrame]:
        """Get traditional player statistics"""
        params = {
            'College': '',
            'Conference': '',
            'Country': '',
            'DateFrom': '',
            'DateTo': '',
            'Division': '',
            'DraftPick': '',
            'DraftYear': '',
            'GameScope': '',
            'GameSegment': '',
            'Height': '',
            'LastNGames': 0,
            'LeagueID': '00',
            'Location': '',
            'MeasureType': 'Base',
            'Month': 0,
            'OpponentTeamID': 0,
            'Outcome': '',
            'PORound': 0,
            'PaceAdjust': 'N',
            'PerMode': 'Totals',
            'Period': 0,
            'PlayerExperience': '',
            'PlayerPosition': '',
            'PlusMinus': 'N',
            'Rank': 'N',
            'Season': season,
            'SeasonSegment': '',
            'SeasonType': season_type,
            'ShotClockRange': '',
            'StarterBench': '',
            'TeamID': 0,
            'TwoWay': 0,
            'VsConference': '',
            'VsDivision': '',
            'Weight': ''
        }
        
        data = self.make_api_request('leaguedashplayerstats', params)
        if data and 'resultSets' in data:
            return pd.DataFrame(data['resultSets'][0]['rowSet'], columns=data['resultSets'][0]['headers'])
        return None
    
    def get_player_clutch_stats(self, season: str = "2023-24", season_type: str = "Regular Season") -> Optional[pd.DataFrame]:
        """Get clutch player statistics (last 5 minutes, +/- 5 points)"""
        params = {
            'College': '',
            'Conference': '',
            'Country': '',
            'DateFrom': '',
            'DateTo': '',
            'Division': '',
            'DraftPick': '',
            'DraftYear': '',
            'GameScope': '',
            'GameSegment': '',
            'Height': '',
            'LastNGames': 0,
            'LeagueID': '00',
            'Location': '',
            'MeasureType': 'Base',
            'Month': 0,
            'OpponentTeamID': 0,
            'Outcome': '',
            'PORound': 0,
            'PerMode': 'Totals',
            'Period': 0,
            'PlayerExperience': '',
            'PlayerPosition': '',
            'PlusMinus': 'N',
            'Rank': 'N',
            'Season': season,
            'SeasonSegment': '',
            'SeasonType': season_type,
            'ShotClockRange': '',
            'StarterBench': '',
            'TeamID': 0,
            'VsConference': '',
            'VsDivision': '',
            'Weight': ''
        }
        
        data = self.make_api_request('leaguedashplayerclutch', params)
        if data and 'resultSets' in data:
            return pd.DataFrame(data['resultSets'][0]['rowSet'], columns=data['resultSets'][0]['headers'])
        return None
    
    def get_player_defense_stats(self, season: str = "2023-24", season_type: str = "Regular Season") -> Optional[pd.DataFrame]:
        """Get player defense statistics"""
        params = {
            'College': '',
            'Conference': '',
            'Country': '',
            'DateFrom': '',
            'DateTo': '',
            'DefenseCategory': 'Overall',
            'Division': '',
            'DraftPick': '',
            'DraftYear': '',
            'GameScope': '',
            'GameSegment': '',
            'Height': '',
            'LastNGames': 0,
            'LeagueID': '00',
            'Location': '',
            'Month': 0,
            'OpponentTeamID': 0,
            'Outcome': '',
            'PORound': 0,
            'PerMode': 'Totals',
            'Period': 0,
            'PlayerExperience': '',
            'PlayerPosition': '',
            'Season': season,
            'SeasonSegment': '',
            'SeasonType': season_type,
            'TeamID': 0,
            'VsConference': '',
            'VsDivision': '',
            'Weight': ''
        }
        
        data = self.make_api_request('leaguedashptdefend', params)
        if data and 'resultSets' in data:
            return pd.DataFrame(data['resultSets'][0]['rowSet'], columns=data['resultSets'][0]['headers'])
        return None
    
    def get_player_hustle_stats(self, season: str = "2023-24", season_type: str = "Regular Season") -> Optional[pd.DataFrame]:
        """Get player hustle statistics"""
        params = {
            'College': '',
            'Conference': '',
            'Country': '',
            'DateFrom': '',
            'DateTo': '',
            'Division': '',
            'DraftPick': '',
            'DraftYear': '',
            'GameScope': '',
            'Height': '',
            'LeagueID': '00',
            'Location': '',
            'Month': 0,
            'OpponentTeamID': 0,
            'Outcome': '',
            'PORound': 0,
            'PerMode': 'Totals',
            'PlayerExperience': '',
            'PlayerPosition': '',
            'Season': season,
            'SeasonSegment': '',
            'SeasonType': season_type,
            'TeamID': 0,
            'VsConference': '',
            'VsDivision': '',
            'Weight': ''
        }
        
        data = self.make_api_request('leaguehustlestatsplayer', params)
        if data and 'resultSets' in data:
            return pd.DataFrame(data['resultSets'][0]['rowSet'], columns=data['resultSets'][0]['headers'])
        return None
    
    def get_team_traditional_stats(self, season: str = "2023-24", season_type: str = "Regular Season") -> Optional[pd.DataFrame]:
        """Get traditional team statistics"""
        params = {
            'Conference': '',
            'DateFrom': '',
            'DateTo': '',
            'Division': '',
            'GameScope': '',
            'GameSegment': '',
            'Height': '',
            'LastNGames': 0,
            'LeagueID': '00',
            'Location': '',
            'MeasureType': 'Base',
            'Month': 0,
            'OpponentTeamID': 0,
            'Outcome': '',
            'PORound': 0,
            'PaceAdjust': 'N',
            'PerMode': 'Totals',
            'Period': 0,
            'PlayerExperience': '',
            'PlayerPosition': '',
            'PlusMinus': 'N',
            'Rank': 'N',
            'Season': season,
            'SeasonSegment': '',
            'SeasonType': season_type,
            'ShotClockRange': '',
            'StarterBench': '',
            'TeamID': 0,
            'TwoWay': 0,
            'VsConference': '',
            'VsDivision': '',
            'Weight': ''
        }
        
        data = self.make_api_request('leaguedashteamstats', params)
        if data and 'resultSets' in data:
            return pd.DataFrame(data['resultSets'][0]['rowSet'], columns=data['resultSets'][0]['headers'])
        return None
    
    def get_all_player_stats(self, season: str = "2023-24", season_type: str = "Regular Season") -> Dict[str, pd.DataFrame]:
        """Get all player statistics in one call"""
        stats = {}
        
        # Traditional stats
        traditional = self.get_player_traditional_stats(season, season_type)
        if traditional is not None:
            stats['traditional'] = traditional
            logger.info(f"Fetched traditional stats for {len(traditional)} players")
        
        # Clutch stats
        clutch = self.get_player_clutch_stats(season, season_type)
        if clutch is not None:
            stats['clutch'] = clutch
            logger.info(f"Fetched clutch stats for {len(clutch)} players")
        
        # Defense stats
        defense = self.get_player_defense_stats(season, season_type)
        if defense is not None:
            stats['defense'] = defense
            logger.info(f"Fetched defense stats for {len(defense)} players")
        
        # Hustle stats
        hustle = self.get_player_hustle_stats(season, season_type)
        if hustle is not None:
            stats['hustle'] = hustle
            logger.info(f"Fetched hustle stats for {len(hustle)} players")
        
        return stats
    
    def get_all_team_stats(self, season: str = "2023-24", season_type: str = "Regular Season") -> Dict[str, pd.DataFrame]:
        """Get all team statistics in one call"""
        stats = {}
        
        # Traditional team stats
        traditional = self.get_team_traditional_stats(season, season_type)
        if traditional is not None:
            stats['traditional'] = traditional
            logger.info(f"Fetched traditional team stats for {len(traditional)} teams")
        
        return stats
    
    def save_stats_to_database(self, stats: Dict[str, pd.DataFrame], season: str, data_type: str = "player"):
        """Save fetched stats to database (placeholder for your DB integration)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for stat_type, df in stats.items():
            if df is not None and not df.empty:
                filename = f"nba_{data_type}_{stat_type}_{season}_{timestamp}.csv"
                df.to_csv(f"/tmp/{filename}", index=False)
                logger.info(f"Saved {stat_type} {data_type} stats to {filename}")
                
                # Here you would integrate with your database
                # For now, we'll just log the action
                logger.info(f"Would save {len(df)} rows of {stat_type} {data_type} data to database")
    
    def discover_endpoints(self):
        """Discover and test all available NBA API endpoints"""
        logger.info("Discovering NBA API endpoints...")
        
        test_endpoints = [
            'leaguedashplayerstats',
            'leaguedashplayerclutch', 
            'leaguedashptdefend',
            'leaguehustlestatsplayer',
            'leaguedashteamstats',
            'leaguehustlestatsteam'
        ]
        
        working_endpoints = []
        
        for endpoint in test_endpoints:
            try:
                response = self.make_api_request(endpoint, {'Season': '2023-24', 'LeagueID': '00'})
                if response and 'resultSets' in response:
                    working_endpoints.append(endpoint)
                    logger.info(f"✅ {endpoint} - Working")
                else:
                    logger.warning(f"❌ {endpoint} - No data returned")
            except Exception as e:
                logger.error(f"❌ {endpoint} - Error: {e}")
            
            time.sleep(1)  # Rate limiting
        
        logger.info(f"Found {len(working_endpoints)} working endpoints")
        return working_endpoints

def main():
    """Main function to test the NBA API client"""
    nba_api = NBAOfficialAPI()
    
    logger.info("Starting NBA API endpoint discovery...")
    
    # Discover working endpoints
    working_endpoints = nba_api.discover_endpoints()
    
    # Fetch player stats
    logger.info("Fetching player statistics...")
    player_stats = nba_api.get_all_player_stats(season="2023-24")
    
    # Fetch team stats
    logger.info("Fetching team statistics...")
    team_stats = nba_api.get_all_team_stats(season="2023-24")
    
    # Save to database/files
    nba_api.save_stats_to_database(player_stats, "2023-24", "player")
    nba_api.save_stats_to_database(team_stats, "2023-24", "team")
    
    # Print summary
    logger.info("\n=== NBA API Data Summary ===")
    logger.info(f"Working endpoints: {len(working_endpoints)}")
    logger.info(f"Player stat categories: {len(player_stats)}")
    logger.info(f"Team stat categories: {len(team_stats)}")
    
    for stat_type, df in player_stats.items():
        if df is not None:
            logger.info(f"  - {stat_type}: {len(df)} players, {len(df.columns)} stats")
    
    for stat_type, df in team_stats.items():
        if df is not None:
            logger.info(f"  - {stat_type}: {len(df)} teams, {len(df.columns)} stats")

if __name__ == "__main__":
    main()