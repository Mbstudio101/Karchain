#!/usr/bin/env python3
"""
NBA Endpoint Reality Check - Find Alternative URLs

Check if the failing endpoints exist on NBA.com or use different patterns
"""

import sys
import os
import json
import time
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from curl_cffi import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAEndpointRealityCheck:
    """
    Check if failing endpoints exist and find alternative patterns
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
    
    # Alternative endpoint patterns to test
    ALTERNATIVE_PATTERNS = {
        "leaguedashplayerclutch": [
            "leaguedashplayerclutch",
            "leaguedashplayerclutchstats",
            "playerclutch",
            "clutchstats",
            "playerclutchstats"
        ],
        "leaguedashplayershotlocations": [
            "leaguedashplayershotlocations",
            "playershotlocations",
            "shotlocations",
            "leaguedashshotlocations",
            "playershooting"
        ],
        "leaguedashptstats": [
            "leaguedashptstats",
            "ptstats",
            "playertrackingstats",
            "leaguedashplayertracking"
        ],
        "leaguedashteamstats": [
            "leaguedashteamstats",
            "teamstats",
            "leagueteamstats",
            "dashteamstats"
        ]
    }
    
    # Alternative base URLs
    ALTERNATIVE_BASE_URLS = [
        "https://stats.nba.com/stats",
        "https://data.nba.net/10s/prod/v1",
        "https://cdn.nba.com/static/json/liveData",
        "https://ak-static.cms.nba.com/wp-content/uploads/statistics"
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.results = {}
    
    def test_endpoint_variations(self, original_endpoint: str) -> Dict[str, Any]:
        """Test different endpoint name variations"""
        logger.info(f"\n🔍 Testing endpoint variations for {original_endpoint}")
        
        variations = self.ALTERNATIVE_PATTERNS.get(original_endpoint, [original_endpoint])
        results = []
        
        for variation in variations:
            url = f"{self.ALTERNATIVE_BASE_URLS[0]}/{variation}"
            params = {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00"}
            
            try:
                logger.info(f"🎯 Testing: {variation}")
                response = self.session.get(
                    url,
                    params=params,
                    headers=self.BROWSER_CONFIG['headers'],
                    impersonate=self.BROWSER_CONFIG['impersonate'],
                    timeout=15
                )
                
                result = {
                    "endpoint": variation,
                    "status_code": response.status_code,
                    "url": url,
                    "success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result["has_data"] = 'resultSets' in data and len(data['resultSets']) > 0
                        result["record_count"] = len(data['resultSets'][0].get('rowSet', [])) if result["has_data"] else 0
                        logger.info(f"✅ Found working endpoint: {variation} - {result['record_count']} records")
                    except:
                        result["has_data"] = False
                        logger.info(f"✅ Found endpoint: {variation} (invalid JSON)")
                else:
                    logger.info(f"❌ {variation}: {response.status_code}")
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"💥 Error testing {variation}: {e}")
                results.append({
                    "endpoint": variation,
                    "status_code": 0,
                    "error": str(e),
                    "success": False
                })
            
            time.sleep(1)
        
        return {
            "original_endpoint": original_endpoint,
            "variations_tested": results,
            "working_variations": [r for r in results if r.get("success")],
            "best_variation": next((r for r in results if r.get("success")), None)
        }
    
    def test_different_seasons(self, endpoint: str) -> Dict[str, Any]:
        """Test if endpoint works with different seasons"""
        logger.info(f"\n📅 Testing different seasons for {endpoint}")
        
        seasons = ["2023-24", "2022-23", "2021-22", "2020-21"]
        results = []
        
        for season in seasons:
            url = f"{self.ALTERNATIVE_BASE_URLS[0]}/{endpoint}"
            params = {"Season": season, "SeasonType": "Regular Season", "LeagueID": "00"}
            
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=self.BROWSER_CONFIG['headers'],
                    impersonate=self.BROWSER_CONFIG['impersonate'],
                    timeout=15
                )
                
                result = {
                    "season": season,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result["has_data"] = 'resultSets' in data and len(data['resultSets']) > 0
                        result["record_count"] = len(data['resultSets'][0].get('rowSet', [])) if result["has_data"] else 0
                    except:
                        result["has_data"] = False
                
                results.append(result)
                logger.info(f"📊 {season}: {response.status_code}")
                
            except Exception as e:
                results.append({
                    "season": season,
                    "status_code": 0,
                    "error": str(e),
                    "success": False
                })
            
            time.sleep(1)
        
        return {
            "endpoint": endpoint,
            "season_tests": results,
            "working_seasons": [r for r in results if r.get("success")],
            "conclusion": "Endpoint appears deprecated" if all(not r.get("success") for r in results) else "Season-specific issue"
        }
    
    def check_nba_website_references(self) -> Dict[str, Any]:
        """Check if these endpoints are referenced on NBA.com"""
        logger.info("\n🌐 Checking NBA.com for endpoint references")
        
        # URLs that might reference these stats
        nba_pages = [
            "https://www.nba.com/stats/players/clutch",
            "https://www.nba.com/stats/players/shooting",
            "https://www.nba.com/stats/players/tracking",
            "https://www.nba.com/stats/teams/traditional"
        ]
        
        results = []
        
        for page_url in nba_pages:
            try:
                logger.info(f"📄 Fetching: {page_url}")
                response = self.session.get(
                    page_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                    timeout=15
                )
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Look for API endpoint references
                    api_patterns = [
                        r'"/stats/([^"]+)"',
                        r'"stats\.nba\.com/([^"]+)"',
                        r'api[^"]*endpoint[^"]*"([^"]*)"'
                    ]
                    
                    found_endpoints = []
                    for pattern in api_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        found_endpoints.extend(matches)
                    
                    results.append({
                        "page": page_url,
                        "status": "found",
                        "endpoints_found": list(set(found_endpoints)),
                        "content_length": len(content)
                    })
                    
                    logger.info(f"✅ Found {len(found_endpoints)} potential endpoints")
                    
                else:
                    results.append({
                        "page": page_url,
                        "status": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                results.append({
                    "page": page_url,
                    "status": "error",
                    "error": str(e)
                })
            
            time.sleep(2)
        
        return {
            "pages_checked": results,
            "all_endpoints_found": list(set(
                endpoint for page in results 
                for endpoint in page.get("endpoints_found", [])
            ))
        }
    
    def run_full_reality_check(self) -> Dict[str, Any]:
        """Run comprehensive reality check"""
        logger.info("🚀 NBA ENDPOINT REALITY CHECK")
        logger.info("=" * 80)
        
        failing_endpoints = [
            "leaguedashplayerclutch",
            "leaguedashplayershotlocations", 
            "leaguedashptstats",
            "leaguedashteamstats"
        ]
        
        all_results = {}
        
        # Test endpoint variations
        logger.info("\n🔍 PHASE 1: Testing endpoint name variations")
        for endpoint in failing_endpoints:
            result = self.test_endpoint_variations(endpoint)
            all_results[endpoint] = result
            time.sleep(3)
        
        # Test different seasons
        logger.info("\n📅 PHASE 2: Testing different seasons")
        for endpoint in failing_endpoints:
            if not all_results[endpoint].get("working_variations"):
                result = self.test_different_seasons(endpoint)
                all_results[endpoint]["season_analysis"] = result
            time.sleep(2)
        
        # Check NBA website
        logger.info("\n🌐 PHASE 3: Checking NBA.com references")
        website_results = self.check_nba_website_references()
        all_results["website_analysis"] = website_results
        
        # Generate conclusions
        conclusions = []
        for endpoint, data in all_results.items():
            if endpoint == "website_analysis":
                continue
                
            working_variations = data.get("working_variations", [])
            if working_variations:
                conclusions.append(f"✅ {endpoint}: Found {len(working_variations)} working variations")
            else:
                season_conclusion = data.get("season_analysis", {}).get("conclusion", "Unknown")
                conclusions.append(f"❌ {endpoint}: {season_conclusion}")
        
        return {
            "endpoint_analysis": all_results,
            "website_analysis": website_results,
            "conclusions": conclusions,
            "recommendations": self.generate_recommendations(all_results),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        working_count = 0
        for endpoint, data in results.items():
            if endpoint == "website_analysis":
                continue
            if data.get("working_variations"):
                working_count += 1
        
        if working_count > 0:
            recommendations.append(f"🎯 Found working alternatives for {working_count} endpoints")
        
        recommendations.extend([
            "📊 Focus on the 4 working endpoints for immediate data collection",
            "🔍 Monitor NBA.com for new endpoint patterns",
            "🔄 Check these endpoints again in 1-2 weeks (server issues may resolve)",
            "💡 Consider alternative data sources (Basketball Reference, ESPN APIs)",
            "⚡ Implement fallback mechanisms for missing stats"
        ])
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any], filename: str = "nba_reality_check.json"):
        """Save reality check results"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Reality check saved to {filename}")

def main():
    checker = NBAEndpointRealityCheck()
    results = checker.run_full_reality_check()
    checker.save_results(results)
    
    # Print summary
    logger.info(f"\n🎆 REALITY CHECK COMPLETE")
    logger.info(f"📊 Conclusions:")
    for conclusion in results["conclusions"]:
        logger.info(f"   {conclusion}")
    
    logger.info(f"\n💡 Recommendations:")
    for rec in results["recommendations"]:
        logger.info(f"   {rec}")
    
    return results

if __name__ == "__main__":
    main()