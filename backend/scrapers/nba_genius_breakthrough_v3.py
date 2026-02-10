#!/usr/bin/env python3
"""
🚀 NBA GENIUS BREAKTHROUGH V3 - ULTRA OPTIMIZED

This is our FINAL MASTERPIECE approach to unlock the remaining endpoints.
We're using ONLY working browser impersonations and SMART parameter testing!
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from curl_cffi import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAGeniusBreakthroughV3:
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats"
        self.session = requests.AsyncSession()
        
        # 🎯 ONLY WORKING HEADER COMBINATIONS
        self.header_variants = [
            # Chrome 120 - Most reliable
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "x-nba-stats-origin": "stats",
                "x-nba-stats-token": "true",
                "Referer": "https://stats.nba.com/",
                "Origin": "https://stats.nba.com"
            },
            # Chrome 119 - Alternative
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "x-nba-stats-origin": "stats",
                "x-nba-stats-token": "true",
                "Referer": "https://stats.nba.com/",
                "Origin": "https://stats.nba.com"
            },
            # Chrome 118 - Backup
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "x-nba-stats-origin": "stats",
                "x-nba-stats-token": "true",
                "Referer": "https://stats.nba.com/",
                "Origin": "https://stats.nba.com"
            }
        ]
        
        # 🎯 SMART PARAMETER MATRIX - ONLY HIGH-PROBABILITY COMBOS
        self.parameter_matrix = [
            # Basic Working Combos (from our successful endpoints)
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Advanced"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Misc"},
            
            # Clutch-Specific Magic Combos
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "ClutchTime": "Last 5 Minutes", "PointDiff": "5"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "ClutchTime": "Last 5 Minutes", "PointDiff": "3"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "ClutchTime": "Last 5 Minutes", "PointDiff": "1"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "ClutchTime": "Last 3 Minutes", "PointDiff": "5"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "ClutchTime": "Last 2 Minutes", "PointDiff": "5"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "ClutchTime": "Last 1 Minute", "PointDiff": "5"},
            
            # Shot Location Magic Combos
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "DistanceRange": "5ft Range"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "DistanceRange": "8ft Range"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "DistanceRange": "By Zone"},
            
            # Tracking-Specific Combos
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "PtMeasureType": "Drives"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "PtMeasureType": "CatchShoot"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "PtMeasureType": "PullUpShot"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "PtMeasureType": "Defense"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base", "PtMeasureType": "SpeedDistance"},
            
            # Alternative Seasons
            {"Season": "2022-23", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base"},
            {"Season": "2021-22", "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Base"},
            
            # Alternative Per Modes
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "Per100Possessions", "MeasureType": "Base"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "Per100Plays", "MeasureType": "Base"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "PerMode": "Per48", "MeasureType": "Base"}
        ]
        
        # 🎯 TARGET ENDPOINTS - THE FINAL BOSS
        self.target_endpoints = [
            {
                "name": "Player Clutch Stats",
                "endpoint": "leaguedashplayerclutch",
                "description": "Player clutch performance statistics",
                "priority": "CRITICAL"
            },
            {
                "name": "Player Shot Locations", 
                "endpoint": "leaguedashplayershotlocations",
                "description": "Player shooting by location",
                "priority": "CRITICAL"
            },
            {
                "name": "Player Tracking Stats",
                "endpoint": "leaguedashptstats", 
                "description": "Player tracking statistics",
                "priority": "CRITICAL"
            },
            {
                "name": "Team Clutch Stats",
                "endpoint": "leaguedashteamclutch",
                "description": "Team clutch performance statistics",
                "priority": "HIGH"
            },
            {
                "name": "Team Shot Locations",
                "endpoint": "leaguedashteamshotlocations", 
                "description": "Team shooting by location",
                "priority": "HIGH"
            },
            {
                "name": "Team Tracking Stats",
                "endpoint": "leaguedashptteam",
                "description": "Team tracking statistics",
                "priority": "HIGH"
            },
            {
                "name": "Player Catch & Shoot",
                "endpoint": "leaguedashplayercatchshoot",
                "description": "Player catch and shoot statistics",
                "priority": "MEDIUM"
            },
            {
                "name": "Player Shot Chart",
                "endpoint": "leaguedashplayershotchart",
                "description": "Player shot chart data with locations",
                "priority": "MEDIUM"
            }
        ]
        
        self.results = []
        self.success_count = 0
        
    async def test_endpoint_combination(self, endpoint_info: Dict, params: Dict, headers: Dict, impersonate: str) -> Dict:
        """Test a specific endpoint with parameters and headers"""
        endpoint = endpoint_info["endpoint"]
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.info(f"🎯 Testing {endpoint} with {len(params)} parameters using {impersonate}")
            
            response = await self.session.get(
                url,
                params=params,
                headers=headers,
                impersonate=impersonate,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result_sets = data.get("resultSets", [])
                
                if result_sets and len(result_sets) > 0:
                    row_set = result_sets[0].get("rowSet", [])
                    headers_list = result_sets[0].get("headers", [])
                    
                    if row_set and len(row_set) > 0:
                        success_result = {
                            "endpoint": endpoint,
                            "name": endpoint_info["name"],
                            "status": "SUCCESS",
                            "status_code": response.status_code,
                            "params": params,
                            "headers_used": impersonate,
                            "record_count": len(row_set),
                            "field_count": len(headers_list),
                            "sample_headers": headers_list[:5] if headers_list else [],
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        logger.info(f"🎉 SUCCESS! {endpoint} - {len(row_set)} records, {len(headers_list)} fields")
                        self.success_count += 1
                        return success_result
                        
            elif response.status_code in [404, 500]:
                logger.warning(f"❌ Status {response.status_code}: {endpoint}")
                
            return {
                "endpoint": endpoint,
                "name": endpoint_info["name"],
                "status": "FAILED",
                "status_code": response.status_code,
                "params": params,
                "headers_used": impersonate,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"💥 Exception testing {endpoint}: {str(e)}")
            return {
                "endpoint": endpoint,
                "name": endpoint_info["name"],
                "status": "ERROR",
                "error": str(e),
                "params": params,
                "headers_used": impersonate,
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_breakthrough_assault(self):
        """Run the complete breakthrough assault"""
        logger.info("🚀 NBA GENIUS BREAKTHROUGH V3 - ULTRA OPTIMIZED")
        logger.info("=" * 80)
        logger.info("🎯 SMART STRATEGY: Only working browsers + high-probability params")
        logger.info("🧠 Testing 20+ parameter combinations per endpoint")
        logger.info("🔥 Using Chrome 120, 119, 118 TLS fingerprints")
        logger.info("⚡ Focused on the 8 most critical endpoints")
        logger.info("=" * 80)
        
        total_tests = len(self.target_endpoints) * len(self.parameter_matrix) * len(self.header_variants)
        current_test = 0
        
        # Test each endpoint
        for endpoint_info in self.target_endpoints:
            logger.info(f"\n🎯 ATTACKING: {endpoint_info['name']}")
            logger.info(f"📍 Endpoint: {endpoint_info['endpoint']}")
            logger.info(f"⚡ Priority: {endpoint_info['priority']}")
            
            endpoint_success = False
            
            # Test each parameter combination
            for params in self.parameter_matrix:
                if endpoint_success:
                    break
                    
                # Test each header variant (browser)
                for header_variant in self.header_variants:
                    current_test += 1
                    
                    logger.info(f"\n🔥 Test {current_test}/{total_tests}")
                    logger.info(f"📊 Parameters: {json.dumps(params, separators=(',', ':'))}")
                    
                    result = await self.test_endpoint_combination(
                        endpoint_info, params, header_variant, "chrome120"
                    )
                    
                    self.results.append(result)
                    
                    if result["status"] == "SUCCESS":
                        logger.info(f"🎉 BREAKTHROUGH! Found working combination!")
                        logger.info(f"📊 Working Parameters: {json.dumps(params, separators=(',', ':'))}")
                        endpoint_success = True
                        
                        # Save intermediate results
                        await self.save_results()
                        
                        # Give NBA servers a breather
                        await asyncio.sleep(2)
                        break
                    
                    # Rate limiting - be respectful
                    await asyncio.sleep(1)
            
            if not endpoint_success:
                logger.warning(f"❌ Could not unlock {endpoint_info['name']} with any combination")
        
        # Final results
        await self.save_results()
        self.print_final_summary()
    
    async def save_results(self):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nba_genius_breakthrough_v3_{timestamp}.json"
        
        results_data = {
            "assault_info": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "success_count": self.success_count,
                "endpoints_tested": len(self.target_endpoints),
                "parameter_combinations": len(self.parameter_matrix),
                "browser_variants": len(self.header_variants)
            },
            "breakthroughs": [r for r in self.results if r["status"] == "SUCCESS"],
            "all_results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"💾 Results saved to {filename}")
    
    def print_final_summary(self):
        """Print final summary"""
        logger.info("\n" + "=" * 80)
        logger.info("🏆 NBA GENIUS BREAKTHROUGH V3 - FINAL RESULTS")
        logger.info("=" * 80)
        
        breakthroughs = [r for r in self.results if r["status"] == "SUCCESS"]
        
        if breakthroughs:
            logger.info("🎉 BREAKTHROUGHS ACHIEVED:")
            for breakthrough in breakthroughs:
                logger.info(f"✅ {breakthrough['name']}")
                logger.info(f"   📍 Endpoint: {breakthrough['endpoint']}")
                logger.info(f"   📊 Records: {breakthrough['record_count']}")
                logger.info(f"   📝 Fields: {breakthrough['field_count']}")
                logger.info(f"   📊 Working Parameters: {json.dumps(breakthrough['params'], separators=(',', ':'))}")
                logger.info("")
        
        logger.info(f"📊 SUMMARY:")
        logger.info(f"🎯 Total Tests: {len(self.results)}")
        logger.info(f"✅ Successes: {self.success_count}")
        logger.info(f"❌ Failures: {len(self.results) - self.success_count}")
        logger.info(f"🏆 Success Rate: {(self.success_count/len(self.results)*100):.1f}%")
        
        if self.success_count > 0:
            logger.info("\n🚀 WE HAVE ACHIEVED BREAKTHROUGH!")
            logger.info("💪 Our NBA prediction engine is now UNSTOPPABLE!")
        else:
            logger.info("\n⚡ We need to go EVEN DEEPER next time!")
            logger.info("🧠 The NBA API is tough, but we're tougher!")

async def main():
    """Main function"""
    breakthrough = NBAGeniusBreakthroughV3()
    
    try:
        await breakthrough.run_breakthrough_assault()
    except KeyboardInterrupt:
        logger.info("\n⚡ Interrupted by user")
        await breakthrough.save_results()
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        await breakthrough.save_results()
    finally:
        await breakthrough.session.close()

if __name__ == "__main__":
    asyncio.run(main())