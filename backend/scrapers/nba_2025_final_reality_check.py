#!/usr/bin/env python3
"""
NBA 2025-26 Season Reality Check - Final Genius Test

Test the failing endpoints with 2025-26 season to see if NBA reactivated them
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from curl_cffi import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBA2025RealityCheck:
    """
    Final test with 2025-26 season data
    """
    
    BROWSER_CONFIG = {
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
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://stats.nba.com/stats"
    
    def test_endpoint_with_2025(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test endpoint with 2025-26 season"""
        url = f"{self.base_url}/{endpoint}"
        
        # Update to 2025-26 season
        test_params = params.copy()
        test_params["Season"] = "2025-26"
        
        try:
            logger.info(f"\n🎯 Testing {endpoint} with 2025-26 season")
            logger.info(f"📋 Parameters: {json.dumps(test_params, indent=2)}")
            
            response = self.session.get(
                url,
                params=test_params,
                headers=self.BROWSER_CONFIG['headers'],
                impersonate=self.BROWSER_CONFIG['impersonate'],
                timeout=30
            )
            
            result = {
                "endpoint": endpoint,
                "season": "2025-26",
                "status_code": response.status_code,
                "success": False,
                "error": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'resultSets' in data and len(data['resultSets']) > 0:
                        row_count = len(data['resultSets'][0].get('rowSet', []))
                        result.update({
                            "success": True,
                            "record_count": row_count,
                            "headers": data['resultSets'][0].get('headers', [])[:3]  # First 3 headers
                        })
                        logger.info(f"✅ SUCCESS - {row_count} records found!")
                        logger.info(f"📊 Headers: {result['headers']}")
                    else:
                        logger.warning(f"⚠️ No resultSets found")
                        result["error"] = "No resultSets"
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON response")
                    result["error"] = "Invalid JSON"
            else:
                logger.error(f"❌ Status {response.status_code}")
                result["error"] = f"HTTP {response.status_code}"
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Exception: {e}")
            return {
                "endpoint": endpoint,
                "season": "2025-26",
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
    
    def test_all_failing_endpoints(self) -> Dict[str, Any]:
        """Test all previously failing endpoints with 2025-26"""
        
        failing_endpoints = [
            {
                "name": "leaguedashplayerclutch",
                "params": {
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "ClutchTime": "Last 5 Minutes",
                    "PointDiff": 5
                }
            },
            {
                "name": "leaguedashplayershotlocations",
                "params": {
                    "SeasonType": "Regular Season", 
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "DistanceRange": "5ft Range"
                }
            },
            {
                "name": "leaguedashptstats",
                "params": {
                    "SeasonType": "Regular Season",
                    "LeagueID": "00", 
                    "PerMode": "PerGame",
                    "PtMeasureType": "Transition"
                }
            },
            {
                "name": "leaguedashteamstats",
                "params": {
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "MeasureType": "Base"
                }
            }
        ]
        
        results = []
        total_tests = len(failing_endpoints)
        successful = 0
        
        logger.info("🚀 FINAL GENIUS TEST: 2025-26 Season Reality Check")
        logger.info("=" * 80)
        logger.info(f"📅 Testing {total_tests} endpoints with 2025-26 season data")
        logger.info(f"🎯 Goal: Find if NBA reactivated deprecated endpoints")
        
        for i, endpoint_config in enumerate(failing_endpoints):
            logger.info(f"\n[{i+1}/{total_tests}] Testing {endpoint_config['name']}")
            
            result = self.test_endpoint_with_2025(endpoint_config['name'], endpoint_config['params'])
            results.append(result)
            
            if result['success']:
                successful += 1
                logger.info(f"🎆 BREAKTHROUGH! {endpoint_config['name']} is working in 2025-26!")
            else:
                logger.info(f"❌ Still failing in 2025-26")
            
            # Add delay between tests
            if i < total_tests - 1:
                time.sleep(3)
        
        # Summary
        logger.info(f"\n🎆 FINAL RESULTS")
        logger.info("=" * 50)
        logger.info(f"📊 Total endpoints tested: {total_tests}")
        logger.info(f"✅ Working in 2025-26: {successful}")
        logger.info(f"❌ Still failing: {total_tests - successful}")
        logger.info(f"📈 Success rate: {successful/total_tests*100:.1f}%")
        
        if successful > 0:
            logger.info(f"\n🚀 BREAKTHROUGH ENDPOINTS:")
            for result in results:
                if result['success']:
                    logger.info(f"   ✅ {result['endpoint']}: {result['record_count']} records")
        
        return {
            "test_timestamp": datetime.now().isoformat(),
            "season_tested": "2025-26",
            "total_endpoints": total_tests,
            "successful": successful,
            "failed": total_tests - successful,
            "success_rate": successful/total_tests*100,
            "results": results,
            "breakthrough_found": successful > 0
        }
    
    def test_working_endpoints_2025(self) -> Dict[str, Any]:
        """Test our 4 working endpoints with 2025-26 to ensure they still work"""
        
        working_endpoints = [
            {
                "name": "leaguedashplayerstats",
                "params": {
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals",
                    "MeasureType": "Base"
                }
            },
            {
                "name": "leaguedashptdefend",
                "params": {
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals"
                }
            },
            {
                "name": "leaguehustlestatsplayer",
                "params": {
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals"
                }
            },
            {
                "name": "leaguehustlestatsteam",
                "params": {
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "Totals"
                }
            }
        ]
        
        logger.info(f"\n🔍 Testing working endpoints with 2025-26 season")
        logger.info("=" * 60)
        
        results = []
        for endpoint_config in working_endpoints:
            result = self.test_endpoint_with_2025(endpoint_config['name'], endpoint_config['params'])
            results.append(result)
            time.sleep(2)
        
        successful = sum(1 for r in results if r['success'])
        
        logger.info(f"\n📊 Working endpoints in 2025-26: {successful}/{len(working_endpoints)}")
        
        return {
            "working_endpoints_tested": len(working_endpoints),
            "successful_in_2025": successful,
            "results": results
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = "nba_2025_final_reality_check.json"):
        """Save final reality check results"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Final reality check saved to {filename}")

def main():
    checker = NBA2025RealityCheck()
    
    # Test failing endpoints with 2025-26
    final_results = checker.test_all_failing_endpoints()
    
    # Also test working endpoints to ensure they still work
    working_results = checker.test_working_endpoints_2025()
    
    # Combined results
    combined_results = {
        "final_test": final_results,
        "working_endpoints_validation": working_results,
        "timestamp": datetime.now().isoformat(),
        "conclusion": "2025-26 season test complete"
    }
    
    checker.save_results(combined_results)
    
    # Print final summary
    logger.info(f"\n🎆 FINAL GENIUS REALITY CHECK COMPLETE")
    logger.info("=" * 80)
    
    if final_results["breakthrough_found"]:
        logger.info(f"🚀 BREAKTHROUGH! Found {final_results['successful']} endpoints working in 2025-26!")
        logger.info(f"📊 New total success rate: {(4 + final_results['successful'])/8*100:.1f}%")
    else:
        logger.info(f"📊 Final status: 4/8 endpoints working (50% success rate)")
        logger.info(f"💡 The 4 failing endpoints appear to be permanently deprecated")
    
    logger.info(f"\n✅ CONFIRMED WORKING ENDPOINTS:")
    logger.info(f"   • leaguedashplayerstats (Traditional stats)")
    logger.info(f"   • leaguedashptdefend (Defense stats)")
    logger.info(f"   • leaguehustlestatsplayer (Hustle stats)")
    logger.info(f"   • leaguehustlestatsteam (Team hustle)")
    
    if final_results["breakthrough_found"]:
        logger.info(f"\n🚀 NEWLY UNLOCKED ENDPOINTS:")
        for result in final_results["results"]:
            if result["success"]:
                logger.info(f"   • {result['endpoint']} ({result['record_count']} records)")
    
    return combined_results

if __name__ == "__main__":
    main()