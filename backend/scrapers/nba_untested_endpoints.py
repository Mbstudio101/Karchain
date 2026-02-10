#!/usr/bin/env python3
"""
🎯 NBA UNTESTED ENDPOINTS - FINAL ASSAULT
Testing all the UNTESTED endpoints from NBA LINKS that we haven't tried yet.
This could be where the real treasure is hiding!
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict
from curl_cffi import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAUntestedEndpoints:
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats"
        
        # Browser configuration
        self.browser_config = {
            "name": "Chrome 120 Windows",
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
        }
        
        # UNTESTED ENDPOINTS - THE FINAL FRONTIER
        self.untested_endpoints = [
            # PLAYER ADVANCED STATS (UNTESTED)
            {
                "name": "Player Transition Tracking",
                "endpoint": "leaguedashplayerptshot",
                "url": f"{self.base_url}/leaguedashplayerptshot",
                "priority": "HIGH",
                "description": "Player transition and shot tracking data",
                "category": "Player Advanced"
            },
            {
                "name": "Player Catch & Shoot",
                "endpoint": "leaguedashplayercatchshoot",
                "url": f"{self.base_url}/leaguedashplayercatchshoot",
                "priority": "HIGH",
                "description": "Player catch and shoot statistics",
                "category": "Player Advanced"
            },
            {
                "name": "Player Shot Chart",
                "endpoint": "leaguedashplayershotchart",
                "url": f"{self.base_url}/leaguedashplayershotchart",
                "priority": "HIGH",
                "description": "Player shot chart data with locations",
                "category": "Player Advanced"
            },
            {
                "name": "Player Opponent Shooting",
                "endpoint": "leaguedashplayeropponent",
                "url": f"{self.base_url}/leaguedashplayeropponent",
                "priority": "HIGH",
                "description": "Player impact on opponent shooting",
                "category": "Player Advanced"
            },
            {
                "name": "Player Rebounding Analytics",
                "endpoint": "leaguedashplayerrebounds",
                "url": f"{self.base_url}/leaguedashplayerrebounds",
                "priority": "HIGH",
                "description": "Player rebounding analytics and box-outs",
                "category": "Player Advanced"
            },
            
            # TEAM ADVANCED STATS (UNTESTED)
            {
                "name": "Team Box Scores",
                "endpoint": "leaguedashteamboxscores",
                "url": f"{self.base_url}/leaguedashteamboxscores",
                "priority": "MEDIUM",
                "description": "Team box score data game-by-game",
                "category": "Team Advanced"
            },
            {
                "name": "Team Rebounding Analytics",
                "endpoint": "leaguedashteamrebounds",
                "url": f"{self.base_url}/leaguedashteamrebounds",
                "priority": "MEDIUM",
                "description": "Team rebounding analytics",
                "category": "Team Advanced"
            },
            {
                "name": "Team Opponent Shooting",
                "endpoint": "leaguedashteamopponent",
                "url": f"{self.base_url}/leaguedashteamopponent",
                "priority": "MEDIUM",
                "description": "Team impact on opponent shooting",
                "category": "Team Advanced"
            },
            {
                "name": "Team Shot Chart",
                "endpoint": "leaguedashteamshotchart",
                "url": f"{self.base_url}/leaguedashteamshotchart",
                "priority": "MEDIUM",
                "description": "Team shot chart data",
                "category": "Team Advanced"
            },
            {
                "name": "Team Catch & Shoot",
                "endpoint": "leaguedashteamcatchshoot",
                "url": f"{self.base_url}/leaguedashteamcatchshoot",
                "priority": "MEDIUM",
                "description": "Team catch and shoot statistics",
                "category": "Team Advanced"
            },
            {
                "name": "Team Shot Locations",
                "endpoint": "leaguedashteamshotlocations",
                "url": f"{self.base_url}/leaguedashteamshotlocations",
                "priority": "MEDIUM",
                "description": "Team shooting by location",
                "category": "Team Advanced"
            },
            {
                "name": "Team Clutch Stats",
                "endpoint": "leaguedashteamclutch",
                "url": f"{self.base_url}/leaguedashteamclutch",
                "priority": "MEDIUM",
                "description": "Team clutch performance statistics",
                "category": "Team Advanced"
            }
        ]
        
        # Standard parameters for testing
        self.test_params = {
            'Season': '2023-24',
            'SeasonType': 'Regular Season',
            'PerMode': 'PerGame',
            'MeasureType': 'Base'
        }
        
        self.results = {}

    async def test_endpoint(self, endpoint_info: Dict) -> Dict:
        """Test a single untested endpoint"""
        logger.info(f"\n🎯 TESTING: {endpoint_info['name']}")
        logger.info(f"📍 Endpoint: {endpoint_info['endpoint']}")
        logger.info(f"📝 Description: {endpoint_info['description']}")
        logger.info(f"⚡ Priority: {endpoint_info['priority']}")
        logger.info(f"📊 Category: {endpoint_info['category']}")
        
        try:
            session = requests.AsyncSession()
            
            # Test the endpoint
            response = await session.get(
                endpoint_info['url'],
                headers=self.browser_config['headers'],
                params=self.test_params,
                impersonate=self.browser_config['impersonate'],
                timeout=30
            )
            
            await session.close()
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Extract data from resultSets
                    result_sets = data.get('resultSets', [])
                    if result_sets:
                        first_result = result_sets[0]
                        row_set = first_result.get('rowSet', [])
                        headers = first_result.get('headers', [])
                        
                        result = {
                            "status": "SUCCESS",
                            "status_code": 200,
                            "record_count": len(row_set),
                            "header_count": len(headers),
                            "headers": headers[:10] if len(headers) > 10 else headers,  # First 10 headers
                            "sample_data": row_set[:3] if len(row_set) > 3 else row_set,  # First 3 records
                            "endpoint": endpoint_info['endpoint'],
                            "name": endpoint_info['name'],
                            "category": endpoint_info['category'],
                            "description": endpoint_info['description'],
                            "priority": endpoint_info['priority'],
                            "test_timestamp": datetime.now().isoformat()
                        }
                        
                        logger.info(f"✅ SUCCESS: {len(row_set)} records found!")
                        logger.info(f"📊 Headers: {len(headers)} fields")
                        if headers:
                            logger.info(f"📝 Sample headers: {', '.join(headers[:5])}")
                        
                        return result
                        
                    else:
                        logger.warning(f"⚠️ No resultSets found in response")
                        return {
                            "status": "NO_DATA",
                            "status_code": 200,
                            "endpoint": endpoint_info['endpoint'],
                            "name": endpoint_info['name'],
                            "test_timestamp": datetime.now().isoformat()
                        }
                        
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Response is not valid JSON")
                    return {
                        "status": "INVALID_JSON",
                        "status_code": 200,
                        "content_length": len(response.text),
                        "endpoint": endpoint_info['endpoint'],
                        "name": endpoint_info['name'],
                        "test_timestamp": datetime.now().isoformat()
                    }
                    
            else:
                logger.warning(f"❌ Status {response.status_code}: {endpoint_info['name']}")
                return {
                    "status": f"HTTP_{response.status_code}",
                    "status_code": response.status_code,
                    "endpoint": endpoint_info['endpoint'],
                    "name": endpoint_info['name'],
                    "test_timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"💥 Exception testing {endpoint_info['name']}: {str(e)}")
            return {
                "status": "EXCEPTION",
                "error": str(e),
                "endpoint": endpoint_info['endpoint'],
                "name": endpoint_info['name'],
                "test_timestamp": datetime.now().isoformat()
            }

    async def test_all_untested_endpoints(self) -> Dict:
        """Test all untested endpoints"""
        logger.info("🚀 NBA UNTESTED ENDPOINTS - FINAL ASSAULT")
        logger.info("=" * 60)
        logger.info("🎯 Testing all the UNTESTED endpoints from NBA LINKS")
        logger.info("   These could be the GOLDMINE we've been missing!")
        logger.info("=" * 60)
        
        all_results = []
        working_endpoints = []
        
        # Test each untested endpoint
        for endpoint_info in self.untested_endpoints:
            result = await self.test_endpoint(endpoint_info)
            all_results.append(result)
            
            # Track working endpoints
            if result['status'] == 'SUCCESS':
                working_endpoints.append(result)
                logger.info(f"🎉 WORKING ENDPOINT DISCOVERED: {endpoint_info['name']}")
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        # Summary statistics
        total_tested = len(all_results)
        successful_tests = len(working_endpoints)
        success_rate = (successful_tests / total_tested * 100) if total_tested > 0 else 0
        
        # Category breakdown
        player_advanced_working = len([r for r in working_endpoints if r['category'] == 'Player Advanced'])
        team_advanced_working = len([r for r in working_endpoints if r['category'] == 'Team Advanced'])
        
        summary = {
            "final_assault_summary": {
                "total_endpoints_tested": total_tested,
                "successful_unlocks": successful_tests,
                "failed_tests": total_tested - successful_tests,
                "overall_success_rate": success_rate,
                "player_advanced_working": player_advanced_working,
                "team_advanced_working": team_advanced_working,
                "timestamp": datetime.now().isoformat()
            },
            "working_endpoints": working_endpoints,
            "all_results": all_results
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("🏆 FINAL ASSAULT COMPLETE!")
        logger.info(f"📊 Results: {successful_tests}/{total_tested} endpoints unlocked")
        logger.info(f"🎯 Success Rate: {success_rate:.1f}%")
        logger.info(f"🏀 Player Advanced: {player_advanced_working} working")
        logger.info(f"🏆 Team Advanced: {team_advanced_working} working")
        logger.info("=" * 60)
        
        return summary

    def save_results(self, results: Dict, filename_prefix: str):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"💾 Results saved to {filename}")

async def main():
    """Main execution function"""
    tester = NBAUntestedEndpoints()
    
    try:
        results = await tester.test_all_untested_endpoints()
        tester.save_results(results, "nba_untested_endpoints_final")
        
        # Print summary for easy viewing
        print("\n" + "="*80)
        print("🎯 NBA UNTESTED ENDPOINTS - FINAL RESULTS")
        print("="*80)
        
        if results['working_endpoints']:
            print("🚀 NEW WORKING ENDPOINTS DISCOVERED:")
            print()
            for endpoint in results['working_endpoints']:
                print(f"✅ {endpoint['name']}")
                print(f"   📍 {endpoint['endpoint']}")
                print(f"   📊 {endpoint['record_count']} records, {endpoint['header_count']} fields")
                print(f"   📝 {', '.join(endpoint['headers'][:3])}...")
                print()
        else:
            print("❌ No new working endpoints discovered")
        
        print(f"📊 Summary: {results['final_assault_summary']['successful_unlocks']}/{results['final_assault_summary']['total_endpoints_tested']} endpoints working")
        print(f"🎯 Success Rate: {results['final_assault_summary']['overall_success_rate']:.1f}%")
        print("="*80)
        
    except Exception as e:
        logger.error(f"💥 Final assault failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())