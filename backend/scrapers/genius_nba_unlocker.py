#!/usr/bin/env python3
"""
🧠 GENIUS NBA ENDPOINT UNLOCKER - PHASE 4
The ultimate weapon to crack the remaining NBA endpoints using parameter magic,
browser evolution, and alternative URL strategies.
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

class GeniusNBAEndpointUnlocker:
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats"
        self.alternative_urls = [
            "https://cdn.nba.com/static/json",
            "https://data.nba.net/10s/prod/v1",
            "https://stats.nba.com/js/data",
            "https://ak-static.cms.nba.com/wp-content/uploads"
        ]
        
        # Advanced browser configurations
        self.browser_configs = [
            {
                "name": "Chrome 120 Windows (Latest)",
                "impersonate": "chrome120",
                "headers": {
                    'Host': 'stats.nba.com',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Origin': 'https://www.nba.com',
                    'Referer': 'https://www.nba.com/',
                    'x-nba-stats-origin': 'stats',
                    'x-nba-stats-token': 'true',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                    'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-CH-UA-Mobile': '?0',
                    'Sec-CH-UA-Platform': '"Windows"',
                }
            },
            {
                "name": "Safari 17 Mac (Mobile)",
                "impersonate": "safari17_0",
                "headers": {
                    'Host': 'stats.nba.com',
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Origin': 'https://www.nba.com',
                    'Referer': 'https://www.nba.com/',
                    'x-nba-stats-origin': 'stats',
                    'x-nba-stats-token': 'true',
                }
            }
        ]
        
        # Parameter variations for genius unlocking
        self.parameter_combinations = [
            # Season variations
            {"Season": "2023-24", "SeasonType": "Regular Season"},
            {"Season": "2023-24", "SeasonType": "Playoffs"},
            {"Season": "2023-24", "SeasonType": "Pre Season"},
            {"Season": "2022-23", "SeasonType": "Regular Season"},
            
            # Per mode variations
            {"PerMode": "PerGame", "MeasureType": "Base"},
            {"PerMode": "Per36", "MeasureType": "Base"},
            {"PerMode": "Per100Possessions", "MeasureType": "Base"},
            {"PerMode": "PerGame", "MeasureType": "Advanced"},
            {"PerMode": "PerGame", "MeasureType": "Misc"},
            {"PerMode": "PerGame", "MeasureType": "Scoring"},
            {"PerMode": "PerGame", "MeasureType": "Usage"},
            
            # Advanced parameter combinations
            {"PerMode": "PerGame", "MeasureType": "Base", "PlusMinus": "Y"},
            {"PerMode": "PerGame", "MeasureType": "Base", "PaceAdjust": "Y"},
            {"PerMode": "PerGame", "MeasureType": "Base", "Rank": "Y"},
            {"PerMode": "PerGame", "MeasureType": "Base", "Outcome": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "Location": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "Month": "0"},
            {"PerMode": "PerGame", "MeasureType": "Base", "SeasonSegment": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "DateFrom": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "DateTo": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "OpponentTeamID": "0"},
            {"PerMode": "PerGame", "MeasureType": "Base", "VsConference": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "VsDivision": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "GameSegment": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "Period": "0"},
            {"PerMode": "PerGame", "MeasureType": "Base", "ShotClockRange": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "LastNGames": "0"},
            {"PerMode": "PerGame", "MeasureType": "Base", "GameScope": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "PlayerExperience": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "PlayerPosition": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "StarterBench": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "TeamID": "0"},
            {"PerMode": "PerGame", "MeasureType": "Base", "GameID": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "PointDiff": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "RangeType": "0"},
            {"PerMode": "PerGame", "MeasureType": "Base", "StartPeriod": "1"},
            {"PerMode": "PerGame", "MeasureType": "Base", "EndPeriod": "10"},
            {"PerMode": "PerGame", "MeasureType": "Base", "StartRange": "0"},
            {"PerMode": "PerGame", "MeasureType": "Base", "EndRange": "55800"},
            {"PerMode": "PerGame", "MeasureType": "Base", "ContextFilter": ""},
            {"PerMode": "PerGame", "MeasureType": "Base", "ContextMeasure": "FG_PCT"},
        ]
        
        # Target endpoints that need unlocking
        self.target_endpoints = [
            {
                "name": "Clutch Stats",
                "endpoint": "leaguedashplayerclutch",
                "url": f"{self.base_url}/leaguedashplayerclutch",
                "priority": "CRITICAL",
                "description": "Player performance in clutch situations (last 5 min, +/- 5 points)"
            },
            {
                "name": "Shot Locations",
                "endpoint": "leaguedashplayershotlocations",
                "url": f"{self.base_url}/leaguedashplayershotlocations",
                "priority": "CRITICAL",
                "description": "Player shooting by location (Restricted, Paint, Mid-range, 3PT)"
            },
            {
                "name": "Player Tracking Stats",
                "endpoint": "leaguedashptstats",
                "url": f"{self.base_url}/leaguedashptstats",
                "priority": "HIGH",
                "description": "Advanced player tracking data (speed, distance, touches)"
            },
            {
                "name": "Team Stats",
                "endpoint": "leaguedashteamstats",
                "url": f"{self.base_url}/leaguedashteamstats",
                "priority": "HIGH",
                "description": "Team-level traditional and advanced statistics"
            }
        ]
        
        self.results = {}

    async def test_endpoint_with_browser(self, endpoint: Dict, browser_config: Dict, params: Dict) -> Dict:
        """Test endpoint with specific browser configuration and parameters"""
        try:
            logger.info(f"🧪 Testing {endpoint['name']} with {browser_config['name']} and params: {params}")
            
            session = requests.AsyncSession()
            
            # Merge base headers with browser-specific headers
            headers = browser_config['headers'].copy()
            
            # Add timestamp to prevent caching
            params_with_timestamp = params.copy()
            params_with_timestamp['_'] = str(int(time.time() * 1000))
            
            response = await session.get(
                endpoint['url'],
                headers=headers,
                params=params_with_timestamp,
                impersonate=browser_config['impersonate'],
                timeout=30
            )
            
            await session.close()
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "status": "SUCCESS",
                    "status_code": 200,
                    "record_count": len(data.get('resultSets', [{}])[0].get('rowSet', [])),
                    "headers": len(data.get('resultSets', [{}])[0].get('headers', [])),
                    "browser": browser_config['name'],
                    "params": params,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"✅ SUCCESS: {endpoint['name']} unlocked with {browser_config['name']}!")
                return result
            else:
                logger.warning(f"❌ Status {response.status_code}: {endpoint['name']} with {browser_config['name']}")
                return {
                    "status": f"FAILED_{response.status_code}",
                    "status_code": response.status_code,
                    "browser": browser_config['name'],
                    "params": params,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"💥 Exception testing {endpoint['name']}: {str(e)}")
            return {
                "status": "EXCEPTION",
                "error": str(e),
                "browser": browser_config['name'],
                "params": params,
                "timestamp": datetime.now().isoformat()
            }

    async def test_endpoint_with_alternative_url(self, endpoint: Dict, base_url: str, params: Dict) -> Dict:
        """Test endpoint with alternative base URL"""
        try:
            alternative_url = f"{base_url}/{endpoint['endpoint']}"
            logger.info(f"🌐 Testing alternative URL: {alternative_url}")
            
            session = requests.AsyncSession()
            
            response = await session.get(
                alternative_url,
                headers=self.browser_configs[0]['headers'],
                params=params,
                impersonate=self.browser_configs[0]['impersonate'],
                timeout=30
            )
            
            await session.close()
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "status": "SUCCESS_ALTERNATIVE",
                    "status_code": 200,
                    "record_count": len(data.get('resultSets', [{}])[0].get('rowSet', [])),
                    "headers": len(data.get('resultSets', [{}])[0].get('headers', [])),
                    "alternative_url": alternative_url,
                    "params": params,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"🎯 ALTERNATIVE SUCCESS: {endpoint['name']} unlocked via {alternative_url}!")
                return result
            else:
                return {
                    "status": f"ALT_FAILED_{response.status_code}",
                    "status_code": response.status_code,
                    "alternative_url": alternative_url,
                    "params": params,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"💥 Alternative URL exception: {str(e)}")
            return {
                "status": "ALT_EXCEPTION",
                "error": str(e),
                "alternative_url": alternative_url,
                "params": params,
                "timestamp": datetime.now().isoformat()
            }

    async def unlock_endpoint(self, endpoint: Dict) -> Dict:
        """Comprehensive unlock attempt for a single endpoint"""
        logger.info(f"\n🔓 ATTEMPTING TO UNLOCK: {endpoint['name']} ({endpoint['endpoint']})")
        logger.info(f"📝 Description: {endpoint['description']}")
        logger.info(f"🎯 Priority: {endpoint['priority']}")
        
        all_results = []
        
        # Phase 1: Test with different browser configurations and parameter combinations
        logger.info(f"\n🧪 PHASE 1: Browser + Parameter Matrix Testing")
        for browser_config in self.browser_configs:
            for params in self.parameter_combinations[:10]:  # Test first 10 parameter combinations
                result = await self.test_endpoint_with_browser(endpoint, browser_config, params)
                all_results.append(result)
                
                # If we found a working combination, test more variations
                if result['status'] == 'SUCCESS':
                    logger.info(f"🎉 FOUND WORKING COMBO! Testing more variations...")
                    for additional_params in self.parameter_combinations[10:20]:
                        additional_result = await self.test_endpoint_with_browser(endpoint, browser_config, additional_params)
                        all_results.append(additional_result)
                    break
            
            # Check if we already found a working combination
            if any(r['status'] == 'SUCCESS' for r in all_results):
                break
        
        # Phase 2: Test alternative URLs if standard approach failed
        if not any(r['status'] == 'SUCCESS' for r in all_results):
            logger.info(f"\n🌐 PHASE 2: Alternative URL Testing")
            for alternative_base in self.alternative_urls:
                for params in self.parameter_combinations[:5]:
                    alt_result = await self.test_endpoint_with_alternative_url(endpoint, alternative_base, params)
                    all_results.append(alt_result)
                    
                    if alt_result['status'] == 'SUCCESS_ALTERNATIVE':
                        logger.info(f"🚀 ALTERNATIVE URL SUCCESS!")
                        break
                
                if any(r['status'] == 'SUCCESS_ALTERNATIVE' for r in all_results):
                    break
        
        # Analyze results
        success_results = [r for r in all_results if 'SUCCESS' in r['status']]
        
        summary = {
            "endpoint": endpoint['name'],
            "endpoint_url": endpoint['endpoint'],
            "total_attempts": len(all_results),
            "successful_attempts": len(success_results),
            "success_rate": len(success_results) / len(all_results) * 100 if all_results else 0,
            "best_result": success_results[0] if success_results else None,
            "all_results": all_results,
            "timestamp": datetime.now().isoformat()
        }
        
        if success_results:
            logger.info(f"🎉 UNLOCK SUCCESSFUL for {endpoint['name']}!")
            logger.info(f"📊 Success Rate: {summary['success_rate']:.1f}% ({len(success_results)}/{len(all_results)})")
            if summary['best_result']:
                logger.info(f"🏆 Best Result: {summary['best_result']['status']} - {summary['best_result'].get('record_count', 0)} records")
        else:
            logger.warning(f"❌ UNLOCK FAILED for {endpoint['name']} after {len(all_results)} attempts")
        
        return summary

    async def run_genius_unlock_campaign(self) -> Dict:
        """Run the complete genius unlock campaign"""
        logger.info("🚀 LAUNCHING GENIUS NBA ENDPOINT UNLOCK CAMPAIGN")
        logger.info("=" * 60)
        logger.info("🧠 Using advanced parameter magic, browser evolution,")
        logger.info("   and alternative URL strategies to crack NBA endpoints!")
        logger.info("=" * 60)
        
        campaign_results = {}
        
        for endpoint in self.target_endpoints:
            result = await self.unlock_endpoint(endpoint)
            campaign_results[endpoint['endpoint']] = result
            
            # Save intermediate results
            self.save_results(campaign_results, f"genius_unlock_intermediate_{endpoint['endpoint']}")
            
            # Small delay between endpoints to avoid rate limiting
            await asyncio.sleep(2)
        
        # Final summary
        total_endpoints = len(campaign_results)
        successful_unlocks = len([r for r in campaign_results.values() if r['successful_attempts'] > 0])
        
        final_summary = {
            "campaign_summary": {
                "total_endpoints_tested": total_endpoints,
                "successful_unlocks": successful_unlocks,
                "overall_success_rate": successful_unlocks / total_endpoints * 100,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": campaign_results
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("🏆 GENIUS UNLOCK CAMPAIGN COMPLETE!")
        logger.info(f"📊 Results: {successful_unlocks}/{total_endpoints} endpoints unlocked")
        logger.info(f"🎯 Success Rate: {successful_unlocks/total_endpoints*100:.1f}%")
        logger.info("=" * 60)
        
        return final_summary

    def save_results(self, results: Dict, filename_prefix: str):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"💾 Results saved to {filename}")

async def main():
    """Main execution function"""
    unlocker = GeniusNBAEndpointUnlocker()
    
    try:
        results = await unlocker.run_genius_unlock_campaign()
        unlocker.save_results(results, "genius_nba_unlock_final")
        
        # Print summary for easy viewing
        print("\n" + "="*80)
        print("🎯 GENIUS NBA ENDPOINT UNLOCK SUMMARY")
        print("="*80)
        
        for endpoint, result in results['detailed_results'].items():
            status = "✅ UNLOCKED" if result['successful_attempts'] > 0 else "❌ FAILED"
            print(f"{status} {endpoint}: {result['successful_attempts']}/{result['total_attempts']} successful")
            if result['best_result']:
                print(f"   🏆 Best: {result['best_result']['status']} - {result['best_result'].get('record_count', 0)} records")
        
        print(f"\n📊 Overall Success Rate: {results['campaign_summary']['overall_success_rate']:.1f}%")
        print("="*80)
        
    except Exception as e:
        logger.error(f"💥 Campaign failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())