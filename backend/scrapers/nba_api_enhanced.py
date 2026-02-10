#!/usr/bin/env python3
"""
Enhanced NBA API Fetcher with improved error handling and retry logic
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedNBAFetcher:
    """Enhanced NBA API fetcher with retry logic and better headers"""
    
    BASE_URL = "https://stats.nba.com/stats"
    
    # Enhanced headers with rotation
    HEADER_ROTATIONS = [
        {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'stats.nba.com',
            'Origin': 'https://www.nba.com',
            'Referer': 'https://www.nba.com/stats',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        },
        {
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Host': 'stats.nba.com',
            'Origin': 'https://www.nba.com',
            'Referer': 'https://www.nba.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        }
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def get_headers(self):
        """Get rotated headers"""
        return self.HEADER_ROTATIONS[self.request_count % len(self.HEADER_ROTATIONS)]
    
    def fetch_with_retry(self, endpoint: str, params: Dict[str, Any], max_retries: int = 3) -> Optional[Dict]:
        """Fetch data with retry logic and exponential backoff"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                # Rotate headers
                headers = self.get_headers()
                
                # Add random delay to avoid rate limiting
                if self.request_count > 0:
                    delay = random.uniform(2, 5) + (attempt * 2)
                    logger.info(f"Waiting {delay:.1f}s before request (attempt {attempt + 1})")
                    time.sleep(delay)
                
                logger.info(f"Fetching {endpoint} (attempt {attempt + 1}/{max_retries})")
                
                # Make request with longer timeout
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=60,  # Increased timeout
                    allow_redirects=True
                )
                
                self.request_count += 1
                
                # Check response status
                if response.status_code == 200:
                    data = response.json()
                    self.success_count += 1
                    
                    if 'resultSets' in data and len(data['resultSets']) > 0:
                        logger.info(f"✅ Successfully fetched {endpoint}")
                        return data
                    else:
                        logger.warning(f"⚠️ No data in {endpoint}")
                        return None
                
                elif response.status_code == 403:
                    logger.warning(f"🚫 403 Forbidden for {endpoint}")
                    self.failure_count += 1
                    continue
                    
                elif response.status_code == 429:
                    logger.warning(f"⏰ Rate limited for {endpoint}")
                    time.sleep(10)  # Longer wait for rate limiting
                    continue
                    
                else:
                    logger.warning(f"❌ Status {response.status_code} for {endpoint}")
                    self.failure_count += 1
                    continue
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Timeout on attempt {attempt + 1} for {endpoint}")
                continue
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"🔌 Connection error on attempt {attempt + 1}: {e}")
                time.sleep(5)
                continue
                
            except Exception as e:
                logger.error(f"💥 Unexpected error on attempt {attempt + 1}: {e}")
                self.failure_count += 1
                continue
        
        logger.error(f"❌ Failed to fetch {endpoint} after {max_retries} attempts")
        return None
    
    def test_single_endpoint(self, endpoint: str, params: Dict[str, Any]) -> bool:
        """Test a single endpoint"""
        logger.info(f"Testing endpoint: {endpoint}")
        result = self.fetch_with_retry(endpoint, params)
        return result is not None
    
    def test_all_endpoints(self):
        """Test all NBA endpoints with different parameter combinations"""
        
        test_configs = [
            {
                "name": "Traditional Player Stats",
                "endpoint": "leaguedashplayerstats",
                "params": {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "MeasureType": "Base"
                }
            },
            {
                "name": "Player Clutch Stats",
                "endpoint": "leaguedashplayerclutch",
                "params": {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "ClutchTime": "Last 5 Minutes",
                    "PointDiff": 5
                }
            },
            {
                "name": "Player Hustle Stats",
                "endpoint": "leaguehustlestatsplayer",
                "params": {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals"
                }
            },
            {
                "name": "Team Traditional Stats",
                "endpoint": "leaguedashteamstats",
                "params": {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "MeasureType": "Base"
                }
            },
            {
                "name": "Team Hustle Stats",
                "endpoint": "leaguehustlestatsteam",
                "params": {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals"
                }
            }
        ]
        
        print("🚀 Enhanced NBA API Endpoint Testing")
        print("=" * 60)
        
        working_endpoints = []
        failed_endpoints = []
        
        for config in test_configs:
            print(f"\n📊 Testing: {config['name']}")
            print(f"🎯 Endpoint: {config['endpoint']}")
            
            success = self.test_single_endpoint(config['endpoint'], config['params'])
            
            if success:
                print("✅ SUCCESS")
                working_endpoints.append(config['endpoint'])
            else:
                print("❌ FAILED")
                failed_endpoints.append(config['endpoint'])
            
            # Longer delay between different endpoints
            time.sleep(random.uniform(3, 7))
        
        print("\n" + "=" * 60)
        print("📈 FINAL SUMMARY")
        print(f"✅ Working endpoints: {len(working_endpoints)}")
        print(f"❌ Failed endpoints: {len(failed_endpoints)}")
        print(f"📊 Success rate: {(len(working_endpoints)/len(test_configs)*100):.1f}%")
        print(f"🎯 Total requests made: {self.request_count}")
        
        return working_endpoints, failed_endpoints
    
    def get_sample_data(self, endpoint: str, params: Dict[str, Any], sample_size: int = 5) -> Optional[Dict]:
        """Get sample data from a working endpoint"""
        data = self.fetch_with_retry(endpoint, params)
        
        if data and 'resultSets' in data and len(data['resultSets']) > 0:
            result_set = data['resultSets'][0]
            
            sample = {
                "endpoint": endpoint,
                "total_rows": len(result_set.get('rowSet', [])),
                "headers": result_set.get('headers', []),
                "sample_data": result_set.get('rowSet', [])[:sample_size] if result_set.get('rowSet') else [],
                "params_used": params
            }
            
            return sample
        
        return None

def main():
    """Main function to test the enhanced NBA fetcher"""
    fetcher = EnhancedNBAFetcher()
    
    print("🚀 Starting Enhanced NBA API Testing...")
    
    # Test all endpoints
    working, failed = fetcher.test_all_endpoints()
    
    # Get sample data from working endpoints
    if working:
        print(f"\n📋 Getting sample data from working endpoints...")
        
        sample_configs = [
            {
                "endpoint": "leaguedashplayerstats",
                "params": {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "MeasureType": "Base"
                }
            }
        ]
        
        for config in sample_configs:
            if config["endpoint"] in working:
                sample = fetcher.get_sample_data(config["endpoint"], config["params"])
                if sample:
                    print(f"\n📊 Sample from {config['endpoint']}:")
                    print(f"Total rows: {sample['total_rows']}")
                    print(f"Headers: {', '.join(sample['headers'][:10])}...")
                    if sample['sample_data']:
                        print(f"First row: {sample['sample_data'][0]}")
    
    print(f"\n🎉 Enhanced testing complete!")
    print(f"Working endpoints: {working}")
    print(f"Failed endpoints: {failed}")

if __name__ == "__main__":
    main()