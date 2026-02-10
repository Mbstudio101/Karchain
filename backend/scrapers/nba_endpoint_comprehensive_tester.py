#!/usr/bin/env python3
"""
NBA API Endpoint Comprehensive Tester

This script systematically tests all NBA API endpoints to determine which ones
are accessible and what data quality they provide. Uses the genius curl_cffi
approach to bypass bot detection.
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAEndpointTester:
    """
    Comprehensive tester for NBA API endpoints using advanced browser impersonation
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
        },
        {
            "name": "Firefox 121",
            "impersonate": "firefox121",
            "headers": {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Host': 'stats.nba.com',
                'Origin': 'https://www.nba.com',
                'Referer': 'https://www.nba.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'x-nba-stats-origin': 'stats',
                'x-nba-stats-token': 'true'
            }
        }
    ]
    
    # Comprehensive endpoint mapping
    ENDPOINT_MAPPING = {
        # Player Statistics
        "leaguedashplayerstats": {
            "description": "Traditional Player Statistics",
            "url_path": "/players/traditional",
            "category": "player_traditional",
            "params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "MeasureType": "Base"
            },
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT"]
        },
        "leaguedashplayerclutch": {
            "description": "Player Clutch Statistics",
            "url_path": "/players/clutch-traditional",
            "category": "player_clutch",
            "params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "ClutchTime": "Last 5 Minutes",
                "PointDiff": 5
            },
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST", "PLUS_MINUS", "FG_PCT", "FG3_PCT"]
        },
        "leaguedashplayershotlocations": {
            "description": "Player Shot Locations",
            "url_path": "/players/shots-general",
            "category": "player_shooting",
            "params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "DistanceRange": "5ft Range"
            },
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "EFG_PCT", "SHOT_DISTANCE"]
        },
        "leaguedashptdefend": {
            "description": "Player Defense Statistics",
            "url_path": "/players/defense-dash-overall",
            "category": "player_defense",
            "params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "DefenseCategory": "Overall"
            },
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "DEF_RIM_FGM", "DEF_RIM_FGA", "DEF_RIM_FG_PCT", "DREB", "STL", "BLK"]
        },
        "leaguedashptstats": {
            "description": "Player Tracking Statistics",
            "url_path": "/players/transition",
            "category": "player_tracking",
            "params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "PerGame",
                "PtMeasureType": "Transition"
            },
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "TRANSITION_FGM", "TRANSITION_FGA", "TRANSITION_FG_PCT", "TRANSITION_PTS", "TRANSITION_POSS"]
        },
        "leaguehustlestatsplayer": {
            "description": "Player Hustle Statistics",
            "url_path": "/players/hustle",
            "category": "player_hustle",
            "params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals"
            },
            "key_stats": ["PLAYER_NAME", "TEAM_ABBREVIATION", "SCREEN_ASSISTS", "SCREEN_AST_PTS", "LOOSE_BALLS_RECOVERED", "CHARGES_DRAWN", "DEFLECTIONS"]
        },
        # Team Statistics
        "leaguedashteamstats": {
            "description": "Traditional Team Statistics",
            "url_path": "/teams/traditional",
            "category": "team_traditional",
            "params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "MeasureType": "Base"
            },
            "key_stats": ["TEAM_NAME", "GP", "W", "L", "W_PCT", "MIN", "PTS", "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT"]
        },
        "leaguehustlestatsteam": {
            "description": "Team Hustle Statistics",
            "url_path": "/teams/hustle",
            "category": "team_hustle",
            "params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals"
            },
            "key_stats": ["TEAM_NAME", "SCREEN_ASSISTS", "SCREEN_AST_PTS", "LOOSE_BALLS_RECOVERED", "CHARGES_DRAWN", "DEFLECTIONS", "CONTESTED_SHOTS_2PT", "CONTESTED_SHOTS_3PT"]
        }
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.request_count = 0
        self.results = {}
        
    def get_browser_config(self, index: int = 0) -> Dict[str, Any]:
        """Get browser configuration by index"""
        return self.BROWSER_CONFIGS[index % len(self.BROWSER_CONFIGS)]
    
    def test_endpoint(self, endpoint: str, endpoint_info: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        Test a single NBA API endpoint
        """
        url = f"{self.BASE_URL}/{endpoint}"
        result = {
            "endpoint": endpoint,
            "description": endpoint_info["description"],
            "url_path": endpoint_info["url_path"],
            "category": endpoint_info["category"],
            "status": "unknown",
            "status_code": None,
            "data_quality": None,
            "record_count": 0,
            "sample_data": None,
            "error": None,
            "response_time": 0,
            "key_stats_found": []
        }
        
        for attempt in range(max_retries):
            config = self.get_browser_config(self.request_count + attempt)
            
            try:
                # Add random delay to avoid detection
                if self.request_count > 0:
                    delay = random.uniform(2, 5) + (attempt * 2)
                    logger.info(f"⏱️  Waiting {delay:.1f}s...")
                    time.sleep(delay)
                
                start_time = time.time()
                logger.info(f"🎯 Testing {endpoint} (Attempt {attempt+1}/{max_retries})")
                
                response = self.session.get(
                    url,
                    params=endpoint_info["params"],
                    headers=config['headers'],
                    impersonate=config['impersonate'],
                    timeout=30
                )
                
                result["response_time"] = time.time() - start_time
                result["status_code"] = response.status_code
                self.request_count += 1
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Check if we have valid result sets
                        if 'resultSets' in data and len(data['resultSets']) > 0:
                            result_set = data['resultSets'][0]
                            result["record_count"] = len(result_set.get('rowSet', []))
                            result["status"] = "success"
                            
                            # Check data quality
                            if result["record_count"] > 0:
                                result["data_quality"] = "high" if result["record_count"] > 100 else "medium"
                                
                                # Get sample data
                                headers = result_set.get('headers', [])
                                if len(result_set['rowSet']) > 0:
                                    sample_row = result_set['rowSet'][0]
                                    result["sample_data"] = dict(zip(headers, sample_row))
                                
                                # Check for key stats
                                available_headers = set(headers)
                                expected_stats = endpoint_info.get("key_stats", [])
                                result["key_stats_found"] = [stat for stat in expected_stats if stat in available_headers]
                                
                                logger.info(f"✅ {endpoint} - SUCCESS: {result['record_count']} records, {len(result['key_stats_found'])}/{len(expected_stats)} key stats found")
                            else:
                                result["data_quality"] = "low"
                                logger.warning(f"⚠️ {endpoint} - Empty result set")
                        else:
                            result["data_quality"] = "none"
                            logger.warning(f"⚠️ {endpoint} - No result sets found")
                        
                        return result
                        
                    except json.JSONDecodeError:
                        result["error"] = "Invalid JSON response"
                        logger.error(f"❌ {endpoint} - Invalid JSON response")
                        
                elif response.status_code == 403:
                    result["error"] = "403 Forbidden"
                    logger.warning(f"🚫 {endpoint} - 403 Forbidden. Retrying with different browser...")
                    
                elif response.status_code == 429:
                    result["error"] = "429 Rate Limited"
                    logger.warning(f"⏰ {endpoint} - Rate limited. Waiting 15s...")
                    time.sleep(15)
                    
                else:
                    result["error"] = f"HTTP {response.status_code}"
                    logger.warning(f"❌ {endpoint} - Status {response.status_code}")
                    
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"💥 {endpoint} - Error: {e}")
                
        # If we get here, all attempts failed
        result["status"] = "failed"
        logger.error(f"❌ {endpoint} - Failed after {max_retries} attempts")
        return result
    
    def run_comprehensive_test(self, output_file: str = "nba_endpoint_test_results.json"):
        """
        Run comprehensive test of all endpoints
        """
        logger.info("🚀 Starting comprehensive NBA endpoint testing...")
        
        all_results = []
        
        for endpoint, endpoint_info in self.ENDPOINT_MAPPING.items():
            try:
                result = self.test_endpoint(endpoint, endpoint_info)
                all_results.append(result)
                
                # Add longer delay between different endpoints
                if self.request_count % 3 == 0:
                    delay = random.uniform(5, 10)
                    logger.info(f"⏱️  Taking longer break: {delay:.1f}s...")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"💥 Critical error testing {endpoint}: {e}")
                all_results.append({
                    "endpoint": endpoint,
                    "description": endpoint_info["description"],
                    "status": "critical_error",
                    "error": str(e)
                })
        
        # Generate summary report
        summary = self.generate_summary(all_results)
        
        # Save results
        final_output = {
            "test_timestamp": datetime.now().isoformat(),
            "total_endpoints_tested": len(all_results),
            "summary": summary,
            "detailed_results": all_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(final_output, f, indent=2, default=str)
        
        logger.info(f"🎉 Testing complete! Results saved to {output_file}")
        self.print_summary(summary)
        
        return final_output
    
    def generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            "total_endpoints": len(results),
            "successful_endpoints": 0,
            "failed_endpoints": 0,
            "high_quality_endpoints": 0,
            "medium_quality_endpoints": 0,
            "low_quality_endpoints": 0,
            "by_category": {},
            "response_times": [],
            "most_reliable_endpoints": [],
            "highest_data_quality": []
        }
        
        for result in results:
            category = result.get("category", "unknown")
            if category not in summary["by_category"]:
                summary["by_category"][category] = {"total": 0, "successful": 0, "failed": 0}
            
            summary["by_category"][category]["total"] += 1
            
            if result["status"] == "success":
                summary["successful_endpoints"] += 1
                summary["by_category"][category]["successful"] += 1
                
                if result["data_quality"] == "high":
                    summary["high_quality_endpoints"] += 1
                elif result["data_quality"] == "medium":
                    summary["medium_quality_endpoints"] += 1
                else:
                    summary["low_quality_endpoints"] += 1
                
                summary["response_times"].append(result["response_time"])
                
            else:
                summary["failed_endpoints"] += 1
                summary["by_category"][category]["failed"] += 1
        
        # Find most reliable endpoints (high success rate + good data)
        successful_results = [r for r in results if r["status"] == "success" and r["data_quality"] in ["high", "medium"]]
        if successful_results:
            summary["most_reliable_endpoints"] = sorted(
                successful_results, 
                key=lambda x: (x["record_count"], len(x.get("key_stats_found", []))), 
                reverse=True
            )[:5]
        
        # Calculate average response time
        if summary["response_times"]:
            summary["avg_response_time"] = sum(summary["response_times"]) / len(summary["response_times"])
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print summary to console"""
        print("\n" + "="*60)
        print("🏀 NBA API ENDPOINT TESTING SUMMARY")
        print("="*60)
        print(f"📊 Total Endpoints Tested: {summary['total_endpoints']}")
        print(f"✅ Successful: {summary['successful_endpoints']}")
        print(f"❌ Failed: {summary['failed_endpoints']}")
        print(f"⭐ High Quality: {summary['high_quality_endpoints']}")
        print(f"📈 Medium Quality: {summary['medium_quality_endpoints']}")
        print(f"📉 Low Quality: {summary['low_quality_endpoints']}")
        
        if hasattr(summary, 'avg_response_time'):
            print(f"⏱️  Avg Response Time: {summary['avg_response_time']:.2f}s")
        
        print("\n📋 Results by Category:")
        for category, stats in summary["by_category"].items():
            success_rate = (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {category}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)")
        
        print("\n🎯 Most Reliable Endpoints:")
        for endpoint in summary.get("most_reliable_endpoints", [])[:3]:
            print(f"   • {endpoint['endpoint']} - {endpoint['record_count']} records, {len(endpoint.get('key_stats_found', []))} key stats")
        
        print("="*60)

def main():
    tester = NBAEndpointTester()
    results = tester.run_comprehensive_test()
    
    # Also save a CSV summary for easy analysis
    csv_data = []
    for result in results["detailed_results"]:
        csv_data.append({
            "endpoint": result["endpoint"],
            "description": result["description"],
            "category": result["category"],
            "status": result["status"],
            "status_code": result["status_code"],
            "data_quality": result["data_quality"],
            "record_count": result["record_count"],
            "response_time": result["response_time"],
            "key_stats_found": len(result.get("key_stats_found", [])),
            "error": result["error"]
        })
    
    df = pd.DataFrame(csv_data)
    df.to_csv("nba_endpoint_test_summary.csv", index=False)
    print("📄 CSV summary saved to nba_endpoint_test_summary.csv")

if __name__ == "__main__":
    main()