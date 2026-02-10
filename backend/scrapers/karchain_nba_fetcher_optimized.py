#!/usr/bin/env python3
"""
Karchain NBA Fetcher v3.0 - Ultimate Bypass Edition

Optimized version using only supported browser impersonations (Chrome 120, Safari 17)
with enhanced header variations and parameter tuning for maximum success rate.
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

class OptimizedKarchainNBAFetcher:
    """
    Optimized NBA data fetcher using only supported browser impersonations
    """
    
    BASE_URL = "https://stats.nba.com/stats"
    
    # Only use supported impersonations
    BROWSER_CONFIGS = [
        {
            "name": "Chrome 120 Windows",
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
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'x-nba-stats-origin': 'stats',
                'x-nba-stats-token': 'true'
            }
        },
        {
            "name": "Chrome 120 Mac",
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
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'x-nba-stats-origin': 'stats',
                'x-nba-stats-token': 'true'
            }
        },
        {
            "name": "Safari 17 Mac",
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
    
    # Enhanced endpoint configurations with specific parameter variations
    ENDPOINT_CONFIGS = {
        # Player Statistics
        "leaguedashplayerstats": {
            "description": "Traditional Player Statistics",
            "category": "player_traditional",
            "param_variations": [
                {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "MeasureType": "Base",
                    "LastNGames": 0,
                    "Month": 0,
                    "OpponentTeamID": 0,
                    "PORound": 0,
                    "Period": 0,
                    "PlayerExperience": "",
                    "PlayerPosition": "",
                    "StarterBench": "",
                    "TeamID": 0,
                    "VsConference": "",
                    "VsDivision": ""
                }
            ],
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT"]
        },
        "leaguedashplayerclutch": {
            "description": "Player Clutch Statistics",
            "category": "player_clutch",
            "param_variations": [
                {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "ClutchTime": "Last 5 Minutes",
                    "PointDiff": 5,
                    "AheadBehind": "Ahead or Behind",
                    "LastNGames": 0,
                    "Month": 0,
                    "OpponentTeamID": 0,
                    "PORound": 0,
                    "Period": 0,
                    "PlayerExperience": "",
                    "PlayerPosition": "",
                    "StarterBench": "",
                    "TeamID": 0,
                    "VsConference": "",
                    "VsDivision": ""
                }
            ],
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST", "PLUS_MINUS", "FG_PCT", "FG3_PCT"]
        },
        "leaguedashplayershotlocations": {
            "description": "Player Shot Locations",
            "category": "player_shooting",
            "param_variations": [
                {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "DistanceRange": "5ft Range",
                    "LastNGames": 0,
                    "Month": 0,
                    "OpponentTeamID": 0,
                    "PORound": 0,
                    "Period": 0,
                    "PlayerExperience": "",
                    "PlayerPosition": "",
                    "StarterBench": "",
                    "TeamID": 0,
                    "VsConference": "",
                    "VsDivision": ""
                }
            ],
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "EFG_PCT", "SHOT_DISTANCE"]
        },
        "leaguedashptdefend": {
            "description": "Player Defense Statistics",
            "category": "player_defense",
            "param_variations": [
                {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "DefenseCategory": "Overall",
                    "LastNGames": 0,
                    "Month": 0,
                    "OpponentTeamID": 0,
                    "PORound": 0,
                    "Period": 0,
                    "PlayerExperience": "",
                    "PlayerPosition": "",
                    "StarterBench": "",
                    "TeamID": 0,
                    "VsConference": "",
                    "VsDivision": ""
                }
            ],
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "DEF_RIM_FGM", "DEF_RIM_FGA", "DEF_RIM_FG_PCT", "DREB", "STL", "BLK"]
        },
        "leaguedashptstats": {
            "description": "Player Tracking Statistics",
            "category": "player_tracking",
            "param_variations": [
                {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "PerGame",
                    "PtMeasureType": "Transition",
                    "LastNGames": 0,
                    "Month": 0,
                    "OpponentTeamID": 0,
                    "PORound": 0,
                    "Period": 0,
                    "PlayerExperience": "",
                    "PlayerPosition": "",
                    "StarterBench": "",
                    "TeamID": 0,
                    "VsConference": "",
                    "VsDivision": ""
                }
            ],
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "TRANSITION_FGM", "TRANSITION_FGA", "TRANSITION_FG_PCT", "TRANSITION_PTS", "TRANSITION_POSS"]
        },
        "leaguehustlestatsplayer": {
            "description": "Player Hustle Statistics",
            "category": "player_hustle",
            "param_variations": [
                {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "LastNGames": 0,
                    "Month": 0,
                    "OpponentTeamID": 0,
                    "PORound": 0,
                    "Period": 0,
                    "PlayerExperience": "",
                    "PlayerPosition": "",
                    "StarterBench": "",
                    "TeamID": 0,
                    "VsConference": "",
                    "VsDivision": ""
                }
            ],
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "SCREEN_ASSISTS", "SCREEN_AST_PTS", "LOOSE_BALLS_RECOVERED", "CHARGES_DRAWN", "DEFLECTIONS"]
        },
        # Team Statistics
        "leaguedashteamstats": {
            "description": "Traditional Team Statistics",
            "category": "team_traditional",
            "param_variations": [
                {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "MeasureType": "Base",
                    "LastNGames": 0,
                    "Month": 0,
                    "OpponentTeamID": 0,
                    "PORound": 0,
                    "Period": 0,
                    "VsConference": "",
                    "VsDivision": ""
                }
            ],
            "key_stats": ["TEAM_NAME", "GP", "W", "L", "W_PCT", "MIN", "PTS", "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT"]
        },
        "leaguehustlestatsteam": {
            "description": "Team Hustle Statistics",
            "category": "team_hustle",
            "param_variations": [
                {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "LastNGames": 0,
                    "Month": 0,
                    "OpponentTeamID": 0,
                    "PORound": 0,
                    "Period": 0,
                    "VsConference": "",
                    "VsDivision": ""
                }
            ],
            "key_stats": ["TEAM_NAME", "SCREEN_ASSISTS", "SCREEN_AST_PTS", "LOOSE_BALLS_RECOVERED", "CHARGES_DRAWN", "DEFLECTIONS", "CONTESTED_SHOTS_2PT", "CONTESTED_SHOTS_3PT"]
        }
    }
    
    def __init__(self, db_session=None):
        self.db = db_session or next(get_db())
        self.session = requests.Session()
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def get_browser_config(self, index: int = 0) -> Dict[str, Any]:
        """Get browser configuration by index"""
        return self.BROWSER_CONFIGS[index % len(self.BROWSER_CONFIGS)]
    
    def add_header_variations(self, config: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """Add realistic header variations for specific endpoints"""
        # Randomize some headers slightly
        if 'User-Agent' in config['headers']:
            # Add slight variations to accept-language
            langs = ['en-US,en;q=0.9', 'en-US,en;q=0.8', 'en-US,en;q=0.95', 'en-US,en;q=0.85']
            config['headers']['Accept-Language'] = random.choice(langs)
        
        # Add realistic timing headers
        config['headers']['DNT'] = '1'
        config['headers']['Upgrade-Insecure-Requests'] = '1'
        
        # Add specific headers for problematic endpoints
        if endpoint in ["leaguedashplayerstats", "leaguedashplayerclutch"]:
            config['headers']['Priority'] = 'u=1, i'
            config['headers']['sec-fetch-user'] = '?1'
        
        return config
    
    def fetch_endpoint(self, endpoint: str, params: Dict[str, Any], max_retries: int = 7) -> Optional[Dict]:
        """
        Optimized endpoint fetcher with advanced techniques
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(max_retries):
            # Rotate through different browser configs
            config_index = (self.request_count + attempt) % len(self.BROWSER_CONFIGS)
            config = self.get_browser_config(config_index)
            config = self.add_header_variations(config, endpoint)
            
            try:
                # Progressive delay strategy
                if self.request_count > 0:
                    base_delay = random.uniform(2, 4)
                    attempt_delay = attempt * 1.5
                    endpoint_delay = random.uniform(1, 3) if endpoint in ["leaguedashplayerstats", "leaguedashplayerclutch"] else 0
                    total_delay = base_delay + attempt_delay + endpoint_delay
                    
                    logger.info(f"⏱️  Waiting {total_delay:.1f}s... (attempt {attempt+1})")
                    time.sleep(total_delay)
                
                logger.info(f"🎯 Fetching {endpoint} (Attempt {attempt+1}/{max_retries}) with {config['name']}")
                
                # Make the request with enhanced settings
                response = self.session.get(
                    url,
                    params=params,
                    headers=config['headers'],
                    impersonate=config['impersonate'],
                    timeout=60,  # Increased timeout for complex endpoints
                    allow_redirects=True,
                    verify=True
                )
                
                self.request_count += 1
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'resultSets' in data and len(data['resultSets']) > 0:
                            if data['resultSets'][0].get('rowSet'):
                                self.success_count += 1
                                logger.info(f"✅ Successfully fetched {endpoint} - {len(data['resultSets'][0]['rowSet'])} records")
                                return data
                            else:
                                logger.warning(f"⚠️ Empty result set for {endpoint}")
                        else:
                            logger.warning(f"⚠️ No resultSets found for {endpoint}")
                    except json.JSONDecodeError:
                        logger.error(f"❌ Invalid JSON response for {endpoint}")
                
                elif response.status_code == 403:
                    logger.warning(f"🚫 403 Forbidden for {endpoint}. Switching browsers...")
                    # Wait longer before retry with different browser
                    time.sleep(random.uniform(5, 10))
                
                elif response.status_code == 500:
                    logger.warning(f"🔧 Server error 500 for {endpoint}. Trying different parameters...")
                    # Try different parameter variations for 500 errors
                    if attempt < len(self.ENDPOINT_CONFIGS.get(endpoint, {}).get("param_variations", [])):
                        params = self.ENDPOINT_CONFIGS[endpoint]["param_variations"][attempt]
                        logger.info(f"🔄 Trying alternative parameters for {endpoint}")
                        continue
                    time.sleep(random.uniform(4, 8))
                
                elif response.status_code == 429:
                    logger.warning(f"⏰ Rate limited on {endpoint}. Waiting 25s...")
                    time.sleep(25)
                
                elif response.status_code == 503:
                    logger.warning(f"🔧 Service unavailable for {endpoint}. Waiting 15s...")
                    time.sleep(15)
                
                else:
                    logger.warning(f"❌ Status {response.status_code} for {endpoint}")
                    
            except Exception as e:
                logger.error(f"💥 Error fetching {endpoint}: {e}")
                # Exponential backoff on errors
                time.sleep(random.uniform(3, 6) * (attempt + 1))
        
        self.failure_count += 1
        logger.error(f"❌ Failed to fetch {endpoint} after {max_retries} attempts")
        return None

    def fetch_all_endpoints(self, season: str = "2023-24") -> Dict[str, Any]:
        """
        Fetch all 8 endpoints with comprehensive tracking and parameter variations
        """
        logger.info(f"🚀 Starting optimized NBA endpoint fetch for {season}...")
        
        results = {}
        total_start_time = time.time()
        
        for endpoint, endpoint_config in self.ENDPOINT_CONFIGS.items():
            start_time = time.time()
            
            # Try different parameter variations for problematic endpoints
            success = False
            for param_variation in endpoint_config["param_variations"]:
                # Update season in params
                params = param_variation.copy()
                params["Season"] = season
                
                logger.info(f"\n📊 Testing {endpoint} - {endpoint_config['description']}")
                logger.info(f"🧪 Using parameter variation: {param_variation}")
                
                # Fetch the endpoint
                data = self.fetch_endpoint(endpoint, params)
                
                if data:
                    success = True
                    break
                else:
                    logger.warning(f"⚠️ Parameter variation failed, trying next...")
                    time.sleep(random.uniform(3, 6))
            
            response_time = time.time() - start_time
            
            if success and data:
                try:
                    result_set = data['resultSets'][0]
                    record_count = len(result_set.get('rowSet', []))
                    
                    # Check for key stats
                    expected_stats = endpoint_config.get("key_stats", [])
                    headers = result_set.get('headers', [])
                    found_stats = [stat for stat in expected_stats if stat in headers]
                    
                    results[endpoint] = {
                        "status": "success",
                        "description": endpoint_config["description"],
                        "category": endpoint_config["category"],
                        "record_count": record_count,
                        "response_time": response_time,
                        "key_stats_found": found_stats,
                        "key_stats_expected": expected_stats,
                        "data_quality": "high" if len(found_stats) == len(expected_stats) else "medium" if found_stats else "low"
                    }
                    
                    logger.info(f"✅ {endpoint}: SUCCESS - {record_count} records, {len(found_stats)}/{len(expected_stats)} key stats")
                    
                except Exception as e:
                    results[endpoint] = {
                        "status": "error",
                        "description": endpoint_config["description"],
                        "category": endpoint_config["category"],
                        "error": str(e),
                        "response_time": response_time
                    }
                    logger.error(f"❌ {endpoint}: Error processing data - {e}")
            else:
                results[endpoint] = {
                    "status": "failed",
                    "description": endpoint_config["description"],
                    "category": endpoint_config["category"],
                    "response_time": response_time
                }
                logger.error(f"❌ {endpoint}: FAILED to fetch")
            
            # Add delay between different endpoints to avoid overwhelming
            if endpoint != list(self.ENDPOINT_CONFIGS.keys())[-1]:
                delay = random.uniform(4, 8)
                logger.info(f"⏱️  Waiting {delay:.1f}s before next endpoint...")
                time.sleep(delay)
        
        total_time = time.time() - total_start_time
        
        # Generate summary
        summary = {
            "total_endpoints": len(self.ENDPOINT_CONFIGS),
            "successful_endpoints": sum(1 for r in results.values() if r["status"] == "success"),
            "failed_endpoints": sum(1 for r in results.values() if r["status"] in ["failed", "error"]),
            "high_quality_endpoints": sum(1 for r in results.values() if r.get("data_quality") == "high"),
            "medium_quality_endpoints": sum(1 for r in results.values() if r.get("data_quality") == "medium"),
            "low_quality_endpoints": sum(1 for r in results.values() if r.get("data_quality") == "low"),
            "total_request_count": self.request_count,
            "total_time": total_time,
            "most_reliable_endpoints": []
        }
        
        # Find most reliable endpoints
        successful_endpoints = [
            {"endpoint": ep, "info": info} 
            for ep, info in results.items() 
            if info["status"] == "success"
        ]
        
        summary["most_reliable_endpoints"] = sorted(
            successful_endpoints,
            key=lambda x: (x["info"]["record_count"], len(x["info"]["key_stats_found"])),
            reverse=True
        )[:5]
        
        # Print summary
        logger.info(f"\n🎆 GENIUS SUMMARY")
        logger.info(f"📊 Total requests: {self.request_count}")
        logger.info(f"✅ Successful: {summary['successful_endpoints']}")
        logger.info(f"❌ Failed: {summary['failed_endpoints']}")
        logger.info(f"📈 Success rate: {(summary['successful_endpoints']/summary['total_endpoints']*100):.1f}%")
        logger.info(f"\n🎉 SUCCESS! Found {summary['successful_endpoints']} working endpoints:")
        
        for ep in summary["most_reliable_endpoints"]:
            logger.info(f"  ✅ {ep['endpoint']} - {ep['info']['record_count']} records")
        
        return {
            "results": results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }

    def save_results(self, results: Dict[str, Any], filename: str = "nba_endpoint_optimized_results.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Results saved to {filename}")

def main():
    # Create database tables first
    create_tables()
    
    fetcher = OptimizedKarchainNBAFetcher()
    
    # Test all endpoints
    results = fetcher.fetch_all_endpoints()
    
    # Save results
    fetcher.save_results(results, "nba_endpoint_optimized_results.json")
    
    return results

if __name__ == "__main__":
    main()