#!/usr/bin/env python3
"""
Genius NBA API Fetcher using curl_cffi

This script uses curl_cffi to mimic real browser TLS/JA3 fingerprints,
allowing it to bypass sophisticated bot detection on NBA.com.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from curl_cffi import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeniusNBAFetcher:
    """
    Advanced NBA API fetcher using curl_cffi to bypass bot detection.
    Mimics real browser TLS/JA3 fingerprints.
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
    
    def __init__(self):
        self.session = requests.Session()
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def get_browser_config(self, index: int = 0) -> Dict[str, Any]:
        """Get browser configuration by index"""
        return self.BROWSER_CONFIGS[index % len(self.BROWSER_CONFIGS)]
    
    def fetch_endpoint(self, endpoint: str, params: Dict[str, Any], browser_index: int = 0) -> Optional[Dict]:
        """
        Fetch NBA API endpoint using curl_cffi with browser impersonation
        """
        url = f"{self.BASE_URL}/{endpoint}"
        config = self.get_browser_config(browser_index)
        
        try:
            logger.info(f"🎯 Fetching {endpoint} with {config['name']} impersonation")
            
            # Add random delay to avoid patterns
            if self.request_count > 0:
                delay = 1.5 + (self.request_count * 0.5) + (time.time() % 1)
                logger.info(f"⏱️  Waiting {delay:.1f}s before request")
                time.sleep(delay)
            
            # Make request with browser impersonation
            response = self.session.get(
                url,
                params=params,
                headers=config['headers'],
                impersonate=config['impersonate'],
                timeout=30,
                allow_redirects=True
            )
            
            self.request_count += 1
            
            # Handle response
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'resultSets' in data and len(data['resultSets']) > 0:
                        self.success_count += 1
                        logger.info(f"✅ Successfully fetched {endpoint}")
                        return data
                    else:
                        logger.warning(f"⚠️ No resultSets in {endpoint}")
                        return None
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error for {endpoint}: {e}")
                    self.failure_count += 1
                    return None
                    
            elif response.status_code == 403:
                logger.warning(f"🚫 403 Forbidden for {endpoint}")
                self.failure_count += 1
                return None
                
            elif response.status_code == 429:
                logger.warning(f"⏰ Rate limited for {endpoint}")
                self.failure_count += 1
                time.sleep(10)
                return None
                
            else:
                logger.warning(f"❌ Status {response.status_code} for {endpoint}")
                self.failure_count += 1
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"💥 Request error for {endpoint}: {e}")
            self.failure_count += 1
            return None
        except Exception as e:
            logger.error(f"💥 Unexpected error for {endpoint}: {e}")
            self.failure_count += 1
            return None
    
    def test_all_endpoints(self) -> Dict[str, bool]:
        """Test all NBA endpoints with different browser configurations"""
        
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
                "name": "Team Defense Stats",
                "endpoint": "leaguedashptdefend",
                "params": {
                    "Season": "2023-24",
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "DefenseCategory": "Overall"
                }
            }
        ]
        
        print("🧠 Genius NBA API Testing with curl_cffi")
        print("=" * 60)
        
        results = {}
        
        for i, config in enumerate(test_configs):
            print(f"\n📊 Testing: {config['name']}")
            print(f"🎯 Endpoint: {config['endpoint']}")
            
            # Try with different browser configurations
            success = False
            for browser_idx in range(len(self.BROWSER_CONFIGS)):
                result = self.fetch_endpoint(config['endpoint'], config['params'], browser_idx)
                if result:
                    success = True
                    break
                else:
                    logger.info(f"🔄 Retrying with different browser config...")
                    time.sleep(3)  # Longer delay between browser switches
            
            results[config['endpoint']] = success
            
            if success:
                print("✅ SUCCESS")
                # Save sample data
                self.save_sample_data(config['endpoint'], result)
            else:
                print("❌ FAILED")
            
            # Delay between different endpoints
            if i < len(test_configs) - 1:
                time.sleep(5)
        
        return results
    
    def save_sample_data(self, endpoint: str, data: Dict):
        """Save sample data from successful fetches"""
        if 'resultSets' in data and len(data['resultSets']) > 0:
            result_set = data['resultSets'][0]
            
            sample = {
                "endpoint": endpoint,
                "timestamp": time.time(),
                "total_rows": len(result_set.get('rowSet', [])),
                "headers": result_set.get('headers', []),
                "sample_data": result_set.get('rowSet', [])[:3] if result_set.get('rowSet') else []
            }
            
            filename = f"nba_sample_{endpoint}.json"
            with open(filename, 'w') as f:
                json.dump(sample, f, indent=2)
            
            logger.info(f"💾 Saved sample data to {filename}")
            logger.info(f"📊 {endpoint}: {sample['total_rows']} rows, {len(sample['headers'])} columns")
    
    def get_working_endpoints(self) -> List[str]:
        """Get list of working endpoints"""
        results = self.test_all_endpoints()
        working = [ep for ep, success in results.items() if success]
        return working
    
    def print_summary(self):
        """Print final summary"""
        print("\n" + "=" * 60)
        print("🎆 GENIUS SUMMARY")
        print(f"📊 Total requests: {self.request_count}")
        print(f"✅ Successful: {self.success_count}")
        print(f"❌ Failed: {self.failure_count}")
        print(f"📈 Success rate: {(self.success_count/max(1, self.request_count)*100):.1f}%")

def main():
    """Main function to run the genius NBA fetcher"""
    print("🚀 Starting Genius NBA API Fetcher with curl_cffi...")
    print("This approach mimics real browser TLS/JA3 fingerprints to bypass detection.")
    
    fetcher = GeniusNBAFetcher()
    
    try:
        # Test all endpoints
        results = fetcher.test_all_endpoints()
        
        # Print summary
        fetcher.print_summary()
        
        # Get working endpoints
        working = [ep for ep, success in results.items() if success]
        
        if working:
            print(f"\n🎉 SUCCESS! Found {len(working)} working endpoints:")
            for ep in working:
                print(f"  ✅ {ep}")
        else:
            print("\n❌ No working endpoints found. NBA.com might be blocking all requests.")
        
        return working
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    working_endpoints = main()