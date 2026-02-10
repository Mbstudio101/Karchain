#!/usr/bin/env python3
"""
NBA Alternative Data Sources - Genius Deep Dive

Find alternative ways to get Clutch, Shot Locations, and Tracking stats
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

class NBAAlternativeDataFinder:
    """
    Find alternative data sources for the deprecated endpoints
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
    
    # Alternative NBA data sources
    ALTERNATIVE_SOURCES = {
        "clutch_stats": [
            {
                "name": "NBA Stats Clutch Page",
                "url": "https://www.nba.com/stats/players/clutch",
                "description": "Clutch stats from NBA.com stats page"
            },
            {
                "name": "NBA Stats Clutch Traditional",
                "url": "https://stats.nba.com/stats/leaguedashplayerstats",
                "description": "Use traditional stats with clutch filters"
            }
        ],
        "shot_locations": [
            {
                "name": "NBA Stats Shooting Page",
                "url": "https://www.nba.com/stats/players/shooting",
                "description": "Shooting stats from NBA.com stats page"
            },
            {
                "name": "NBA Stats Shot Dashboard",
                "url": "https://stats.nba.com/stats/leaguedashplayershotdefend",
                "description": "Alternative shot tracking endpoint"
            }
        ],
        "tracking_stats": [
            {
                "name": "NBA Stats Tracking Page",
                "url": "https://www.nba.com/stats/players/tracking",
                "description": "Player tracking stats from NBA.com"
            },
            {
                "name": "NBA Stats Defense Dashboard",
                "url": "https://stats.nba.com/stats/leaguedashptdefend",
                "description": "Defense tracking (already working)"
            }
        ]
    }
    
    # Alternative base URLs and endpoints
    ALTERNATIVE_ENDPOINTS = {
        "clutch": [
            "leaguedashplayerclutch",
            "leaguedashplayerbiostats",  # Bio stats might include clutch
            "playerdashboardbyclutch",   # Individual player clutch
            "leaguedashplayerstats",     # Traditional with clutch filters
        ],
        "shooting": [
            "leaguedashplayershotlocations",
            "leaguedashplayershotdefend",
            "playerdashboardbyshooting",
            "leaguedashplayershotstats",
            "shotdashboard",
        ],
        "tracking": [
            "leaguedashptstats",
            "leaguedashptdefend",        # Already working!
            "playerdashboardbytracking",
            "leaguedashplayertracking",
            "leaguedashplayerspeeddistance",
        ]
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.discovered_endpoints = []
    
    def scrape_nba_stats_pages(self) -> Dict[str, Any]:
        """Scrape NBA.com stats pages to find hidden API calls"""
        
        pages_to_scrape = [
            "https://www.nba.com/stats/players/clutch",
            "https://www.nba.com/stats/players/shooting", 
            "https://www.nba.com/stats/players/tracking",
            "https://www.nba.com/stats/teams/traditional"
        ]
        
        all_endpoints = []
        
        for page_url in pages_to_scrape:
            try:
                logger.info(f"\n🔍 Scraping: {page_url}")
                
                response = self.session.get(
                    page_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                    timeout=15
                )
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Look for API endpoint patterns
                    patterns = [
                        r'"(/stats/[^"]+)"',           # /stats/ endpoints
                        r'"(stats\.nba\.com/[^"]+)"',  # Full NBA stats URLs
                        r'"api[^"]*"[^"]*"([^"]+)"',   # Generic API patterns
                        r'"endpoint"[^"]*"([^"]+)"',  # Explicit endpoint references
                        r'fetch\([^)]*"([^"]+)"',      # JavaScript fetch calls
                        r'axios\.get\([^)]*"([^"]+)"', # Axios calls
                    ]
                    
                    page_endpoints = []
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if 'stats' in match.lower() and match not in page_endpoints:
                                page_endpoints.append(match)
                    
                    all_endpoints.extend(page_endpoints)
                    logger.info(f"✅ Found {len(page_endpoints)} potential endpoints")
                    
                    # Also look for specific stat types mentioned
                    stat_types = []
                    clutch_terms = ['clutch', 'last5minutes', 'last2minutes', 'last1minute']
                    shooting_terms = ['shooting', 'shot', 'distance', 'range', 'zone']
                    tracking_terms = ['tracking', 'speed', 'distance', 'transition', 'possession']
                    
                    content_lower = content.lower()
                    
                    for term in clutch_terms:
                        if term in content_lower:
                            stat_types.append(f"clutch_{term}")
                    
                    for term in shooting_terms:
                        if term in content_lower:
                            stat_types.append(f"shooting_{term}")
                            
                    for term in tracking_terms:
                        if term in content_lower:
                            stat_types.append(f"tracking_{term}")
                    
                    if stat_types:
                        logger.info(f"📊 Found stat types: {stat_types[:5]}")
                        
                else:
                    logger.error(f"❌ Failed to fetch {page_url}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"💥 Error scraping {page_url}: {e}")
            
            time.sleep(2)
        
        # Remove duplicates and clean up
        unique_endpoints = list(set(all_endpoints))
        cleaned_endpoints = []
        
        for endpoint in unique_endpoints:
            # Clean up the endpoint
            if endpoint.startswith('http'):
                # Extract path from full URL
                endpoint = endpoint.split('stats.nba.com')[-1]
            
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]
            
            if endpoint and 'stats' in endpoint:
                cleaned_endpoints.append(endpoint)
        
        return {
            "total_found": len(cleaned_endpoints),
            "endpoints": cleaned_endpoints[:20],  # Top 20
            "by_category": {
                "clutch": [ep for ep in cleaned_endpoints if any(term in ep.lower() for term in ['clutch', 'last'])],
                "shooting": [ep for ep in cleaned_endpoints if any(term in ep.lower() for term in ['shot', 'shoot', 'distance'])],
                "tracking": [ep for ep in cleaned_endpoints if any(term in ep.lower() for term in ['track', 'speed', 'distance', 'pt'])]
            }
        }
    
    def test_alternative_endpoints(self, category: str, endpoints: List[str]) -> Dict[str, Any]:
        """Test alternative endpoints for a specific category"""
        
        logger.info(f"\n🚀 Testing alternative {category} endpoints")
        logger.info("=" * 60)
        
        results = []
        
        for endpoint in endpoints[:10]:  # Test top 10
            try:
                url = f"https://stats.nba.com/stats/{endpoint}"
                
                # Use parameters that might work for this category
                if category == "clutch":
                    params = {
                        "Season": "2023-24",
                        "SeasonType": "Regular Season", 
                        "LeagueID": "00",
                        "PerMode": "Totals",
                        "ClutchTime": "Last 5 Minutes"
                    }
                elif category == "shooting":
                    params = {
                        "Season": "2023-24",
                        "SeasonType": "Regular Season",
                        "LeagueID": "00", 
                        "PerMode": "Totals",
                        "DistanceRange": "5ft Range"
                    }
                else:  # tracking
                    params = {
                        "Season": "2023-24",
                        "SeasonType": "Regular Season",
                        "LeagueID": "00",
                        "PerMode": "PerGame"
                    }
                
                logger.info(f"\n🎯 Testing: {endpoint}")
                
                response = self.session.get(
                    url,
                    params=params,
                    headers=self.BROWSER_CONFIG['headers'],
                    impersonate=self.BROWSER_CONFIG['impersonate'],
                    timeout=15
                )
                
                result = {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "success": False
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'resultSets' in data and len(data['resultSets']) > 0:
                            row_count = len(data['resultSets'][0].get('rowSet', []))
                            result.update({
                                "success": True,
                                "record_count": row_count,
                                "headers": data['resultSets'][0].get('headers', [])[:3]
                            })
                            logger.info(f"✅ SUCCESS - {row_count} records!")
                        else:
                            logger.info(f"⚠️ Valid response but no data")
                            result["error"] = "No resultSets"
                    except json.JSONDecodeError:
                        logger.info(f"⚠️ Valid response but invalid JSON")
                        result["error"] = "Invalid JSON"
                else:
                    logger.info(f"❌ Status {response.status_code}")
                    result["error"] = f"HTTP {response.status_code}"
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"💥 Error testing {endpoint}: {e}")
                results.append({
                    "endpoint": endpoint,
                    "status_code": 0,
                    "error": str(e),
                    "success": False
                })
            
            time.sleep(2)
        
        successful = [r for r in results if r["success"]]
        
        return {
            "category": category,
            "total_tested": len(results),
            "successful": len(successful),
            "success_rate": len(successful) / len(results) * 100 if results else 0,
            "working_endpoints": successful,
            "all_results": results
        }
    
    def find_working_alternatives(self) -> Dict[str, Any]:
        """Find working alternatives for our failing endpoints"""
        
        logger.info("🚀 GENIUS ALTERNATIVE DATA SOURCE HUNT")
        logger.info("=" * 80)
        
        # Step 1: Scrape NBA.com pages
        logger.info("\n📄 STEP 1: Scraping NBA.com stats pages")
        scraped_data = self.scrape_nba_stats_pages()
        
        # Step 2: Test alternative endpoints by category
        all_results = {}
        
        for category, endpoints in self.ALTERNATIVE_ENDPOINTS.items():
            # Add scraped endpoints to our test list
            scraped_for_category = scraped_data["by_category"].get(category, [])
            all_endpoints = list(set(endpoints + scraped_for_category))
            
            logger.info(f"\n🔍 Testing {len(all_endpoints)} {category} endpoints")
            result = self.test_alternative_endpoints(category, all_endpoints)
            all_results[category] = result
        
        # Step 3: Summary
        total_working = sum(r["successful"] for r in all_results.values())
        total_tested = sum(r["total_tested"] for r in all_results.values())
        
        summary = {
            "total_working_alternatives": total_working,
            "total_tested": total_tested,
            "overall_success_rate": total_working / total_tested * 100 if total_tested > 0 else 0,
            "breakthroughs": {},
            "by_category": all_results
        }
        
        # Identify breakthroughs
        for category, result in all_results.items():
            if result["successful"] > 0:
                summary["breakthroughs"][category] = result["working_endpoints"]
        
        return summary
    
    def save_results(self, results: Dict[str, Any], filename: str = "nba_alternative_data_sources.json"):
        """Save alternative data source findings"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Alternative data sources saved to {filename}")

def main():
    finder = NBAAlternativeDataFinder()
    
    # Find working alternatives
    results = finder.find_working_alternatives()
    
    finder.save_results(results)
    
    # Print summary
    logger.info(f"\n🎆 ALTERNATIVE DATA SOURCE HUNT COMPLETE")
    logger.info("=" * 80)
    logger.info(f"📊 Total working alternatives found: {results['total_working_alternatives']}")
    logger.info(f"📈 Overall success rate: {results['overall_success_rate']:.1f}%")
    
    if results["breakthroughs"]:
        logger.info(f"\n🚀 BREAKTHROUGH ALTERNATIVES FOUND:")
        for category, endpoints in results["breakthroughs"].items():
            logger.info(f"\n📍 {category.upper()}:")
            for ep in endpoints:
                logger.info(f"   ✅ {ep['endpoint']}: {ep['record_count']} records")
                if 'headers' in ep:
                    logger.info(f"      📋 Headers: {ep['headers']}")
    else:
        logger.info(f"\n❌ No breakthrough alternatives found")
    
    logger.info(f"\n💡 RECOMMENDATIONS:")
    logger.info(f"   • Use working alternatives immediately")
    logger.info(f"   • Monitor NBA.com for new endpoint patterns")
    logger.info(f"   • Consider external data sources (Basketball Reference, ESPN)")
    logger.info(f"   • Focus on the 4 confirmed working endpoints")
    
    return results

if __name__ == "__main__":
    main()