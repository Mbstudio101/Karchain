#!/usr/bin/env python3
"""
🔍 ULTIMATE NBA REALITY CHECK - PHASE 5
The final weapon: Scraping actual NBA.com pages to find where they moved the data.
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateNBARealityCheck:
    def __init__(self):
        self.browser_config = {
            "name": "Chrome 120 Windows",
            "impersonate": "chrome120",
            "headers": {
                'Host': 'www.nba.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"Windows"',
            }
        }
        
        # NBA.com pages to scrape for hidden API endpoints
        self.target_pages = [
            {
                "name": "Players Clutch Traditional",
                "url": "https://www.nba.com/stats/players/clutch-traditional",
                "missing_endpoint": "leaguedashplayerclutch",
                "priority": "CRITICAL"
            },
            {
                "name": "Players Shots General", 
                "url": "https://www.nba.com/stats/players/shots-general",
                "missing_endpoint": "leaguedashplayershotlocations",
                "priority": "CRITICAL"
            },
            {
                "name": "Players Transition",
                "url": "https://www.nba.com/stats/players/transition",
                "missing_endpoint": "leaguedashplayerptshot",
                "priority": "HIGH"
            },
            {
                "name": "Players Catch Shoot",
                "url": "https://www.nba.com/stats/players/catch-shoot",
                "missing_endpoint": "leaguedashplayercatchshoot",
                "priority": "HIGH"
            },
            {
                "name": "Players Shooting",
                "url": "https://www.nba.com/stats/players/shooting",
                "missing_endpoint": "leaguedashplayershotchart",
                "priority": "HIGH"
            },
            {
                "name": "Players Opponent Shooting",
                "url": "https://www.nba.com/stats/players/opponent-shooting",
                "missing_endpoint": "leaguedashplayeropponent",
                "priority": "HIGH"
            },
            {
                "name": "Players Box Outs",
                "url": "https://www.nba.com/stats/players/box-outs",
                "missing_endpoint": "leaguedashplayerrebounds",
                "priority": "HIGH"
            },
            {
                "name": "Teams Traditional",
                "url": "https://www.nba.com/stats/teams/traditional",
                "missing_endpoint": "leaguedashteamstats",
                "priority": "HIGH"
            },
            {
                "name": "Teams Clutch Traditional",
                "url": "https://www.nba.com/stats/teams/clutch-traditional",
                "missing_endpoint": "leaguedashteamclutch",
                "priority": "HIGH"
            },
            {
                "name": "Teams Shots General",
                "url": "https://www.nba.com/stats/teams/shots-general",
                "missing_endpoint": "leaguedashteamshotlocations",
                "priority": "HIGH"
            }
        ]
        
        self.found_endpoints = {}
        self.alternative_data_sources = []

    async def scrape_page_for_api_endpoints(self, page_info: Dict) -> Dict:
        """Scrape NBA.com page for hidden API endpoints"""
        logger.info(f"\n🔍 SCRAPING: {page_info['name']}")
        logger.info(f"🌐 URL: {page_info['url']}")
        logger.info(f"🎯 Target: {page_info['missing_endpoint']}")
        logger.info(f"⚡ Priority: {page_info['priority']}")
        
        try:
            session = requests.AsyncSession()
            
            # Get the actual NBA.com page
            response = await session.get(
                page_info['url'],
                headers=self.browser_config['headers'],
                impersonate=self.browser_config['impersonate'],
                timeout=30
            )
            
            await session.close()
            
            if response.status_code != 200:
                logger.warning(f"❌ Failed to load page: {response.status_code}")
                return {
                    "page": page_info['name'],
                    "status": f"HTTP_{response.status_code}",
                    "endpoints_found": [],
                    "timestamp": datetime.now().isoformat()
                }
            
            html_content = response.text
            logger.info(f"📄 Page loaded successfully ({len(html_content)} characters)")
            
            # Look for API endpoints in the HTML
            endpoints_found = []
            
            # Pattern 1: Look for stats.nba.com/stats/ endpoints
            stats_pattern = r'stats\.nba\.com/stats/([a-zA-Z0-9]+)'
            stats_matches = re.findall(stats_pattern, html_content)
            
            # Pattern 2: Look for CDN endpoints
            cdn_pattern = r'cdn\.nba\.com/[^"\']*\.json'
            cdn_matches = re.findall(cdn_pattern, html_content)
            
            # Pattern 3: Look for data.nba.net endpoints
            data_pattern = r'data\.nba\.net/[^"\']*'
            data_matches = re.findall(data_pattern, html_content)
            
            # Pattern 4: Look for GraphQL endpoints
            graphql_pattern = r'/graphql[^"\']*'
            graphql_matches = re.findall(graphql_pattern, html_content)
            
            # Pattern 5: Look for API calls in JavaScript
            js_api_pattern = r'api/([a-zA-Z0-9]+)'
            js_api_matches = re.findall(js_api_pattern, html_content)
            
            # Pattern 6: Look for fetch/axios calls
            fetch_pattern = r'fetch\(["\']([^"\']+)["\']\)'
            fetch_matches = re.findall(fetch_pattern, html_content)
            
            # Pattern 7: Look for window.nba or similar data injection
            window_data_pattern = r'window\.[a-zA-Z_]+\s*=\s*\{[^}]+\}'
            window_data_matches = re.findall(window_data_pattern, html_content)
            
            # Collect all findings
            if stats_matches:
                for endpoint in stats_matches:
                    if endpoint != page_info['missing_endpoint']:
                        endpoints_found.append({
                            "type": "stats_endpoint",
                            "endpoint": endpoint,
                            "full_url": f"https://stats.nba.com/stats/{endpoint}",
                            "confidence": "HIGH"
                        })
            
            if cdn_matches:
                for endpoint in cdn_matches:
                    endpoints_found.append({
                        "type": "cdn_endpoint",
                        "endpoint": endpoint,
                        "full_url": f"https://{endpoint}",
                        "confidence": "MEDIUM"
                    })
            
            if data_matches:
                for endpoint in data_matches:
                    endpoints_found.append({
                        "type": "data_endpoint",
                        "endpoint": endpoint,
                        "full_url": f"https://{endpoint}",
                        "confidence": "MEDIUM"
                    })
            
            if graphql_matches:
                for endpoint in graphql_matches:
                    endpoints_found.append({
                        "type": "graphql_endpoint",
                        "endpoint": endpoint,
                        "full_url": f"https://www.nba.com{endpoint}" if endpoint.startswith('/') else f"https://www.nba.com/{endpoint}",
                        "confidence": "HIGH"
                    })
            
            if js_api_matches:
                for endpoint in js_api_matches:
                    endpoints_found.append({
                        "type": "js_api_endpoint",
                        "endpoint": endpoint,
                        "full_url": f"https://www.nba.com/api/{endpoint}",
                        "confidence": "MEDIUM"
                    })
            
            if fetch_matches:
                for endpoint in fetch_matches:
                    if 'stats.nba.com' in endpoint or 'cdn.nba.com' in endpoint or 'data.nba.net' in endpoint:
                        endpoints_found.append({
                            "type": "fetch_endpoint",
                            "endpoint": endpoint,
                            "full_url": endpoint,
                            "confidence": "HIGH"
                        })
            
            # Look for embedded JSON data
            json_pattern = r'\{[^{}]*"rowSet"[^{}]*\}'
            json_matches = re.findall(json_pattern, html_content)
            
            embedded_data = []
            for json_match in json_matches[:3]:  # Check first 3 JSON objects
                try:
                    data = json.loads(json_match)
                    if 'rowSet' in data and len(data.get('rowSet', [])) > 10:  # Significant data
                        embedded_data.append({
                            "type": "embedded_json",
                            "record_count": len(data['rowSet']),
                            "headers_count": len(data.get('headers', [])),
                            "sample_data": data['rowSet'][:2] if len(data['rowSet']) > 2 else data['rowSet']
                        })
                except:
                    continue
            
            # Parse HTML with BeautifulSoup for additional clues
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for script tags with data
            script_data = []
            for script in soup.find_all('script'):
                if script.string and len(script.string) > 100:  # Substantial script content
                    if 'stats' in script.string.lower() or 'data' in script.string.lower():
                        script_data.append({
                            "type": "script_content",
                            "length": len(script.string),
                            "contains_stats": 'stats' in script.string.lower(),
                            "contains_data": 'data' in script.string.lower()
                        })
            
            result = {
                "page": page_info['name'],
                "url": page_info['url'],
                "missing_endpoint": page_info['missing_endpoint'],
                "status": "SUCCESS",
                "endpoints_found": endpoints_found,
                "embedded_data_found": embedded_data,
                "script_data_clues": script_data,
                "total_endpoints": len(endpoints_found),
                "has_embedded_data": len(embedded_data) > 0,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🔍 Found {len(endpoints_found)} potential endpoints")
            logger.info(f"📊 Found {len(embedded_data)} embedded data sources")
            logger.info(f"📝 Found {len(script_data_clues)} script data clues")
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Error scraping {page_info['name']}: {str(e)}")
            return {
                "page": page_info['name'],
                "url": page_info['url'],
                "missing_endpoint": page_info['missing_endpoint'],
                "status": "ERROR",
                "error": str(e),
                "endpoints_found": [],
                "timestamp": datetime.now().isoformat()
            }

    async def test_found_endpoints(self, findings: Dict) -> Dict:
        """Test any endpoints we found to see if they actually work"""
        if not findings.get('endpoints_found'):
            return findings
        
        logger.info(f"\n🧪 TESTING FOUND ENDPOINTS for {findings['page']}")
        
        tested_endpoints = []
        
        for endpoint_info in findings['endpoints_found']:
            try:
                session = requests.AsyncSession()
                
                # Test the endpoint
                response = await session.get(
                    endpoint_info['full_url'],
                    headers=self.browser_config['headers'],
                    impersonate=self.browser_config['impersonate'],
                    params={'Season': '2023-24', 'SeasonType': 'Regular Season'},
                    timeout=15
                )
                
                await session.close()
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        record_count = len(data.get('resultSets', [{}])[0].get('rowSet', []))
                        
                        endpoint_info['test_result'] = {
                            "status": "WORKING",
                            "status_code": 200,
                            "record_count": record_count,
                            "test_timestamp": datetime.now().isoformat()
                        }
                        
                        logger.info(f"✅ WORKING: {endpoint_info['endpoint']} - {record_count} records")
                        
                        # This is a major discovery!
                        self.alternative_data_sources.append({
                            "original_missing": findings['missing_endpoint'],
                            "alternative_endpoint": endpoint_info['endpoint'],
                            "full_url": endpoint_info['full_url'],
                            "record_count": record_count,
                            "discovery_source": findings['page']
                        })
                        
                    except json.JSONDecodeError:
                        endpoint_info['test_result'] = {
                            "status": "HTML_RESPONSE",
                            "status_code": 200,
                            "content_length": len(response.text),
                            "test_timestamp": datetime.now().isoformat()
                        }
                        logger.info(f"📄 HTML Response: {endpoint_info['endpoint']}")
                        
                else:
                    endpoint_info['test_result'] = {
                        "status": f"HTTP_{response.status_code}",
                        "status_code": response.status_code,
                        "test_timestamp": datetime.now().isoformat()
                    }
                    logger.warning(f"❌ Status {response.status_code}: {endpoint_info['endpoint']}")
                
                tested_endpoints.append(endpoint_info)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"💥 Test failed for {endpoint_info['endpoint']}: {str(e)}")
                endpoint_info['test_result'] = {
                    "status": "EXCEPTION",
                    "error": str(e),
                    "test_timestamp": datetime.now().isoformat()
                }
                tested_endpoints.append(endpoint_info)
        
        findings['endpoints_found'] = tested_endpoints
        findings['working_endpoints'] = len([e for e in tested_endpoints if e.get('test_result', {}).get('status') == 'WORKING'])
        
        return findings

    async def run_ultimate_reality_check(self) -> Dict:
        """Run the complete ultimate reality check"""
        logger.info("🔍 ULTIMATE NBA REALITY CHECK - PHASE 5")
        logger.info("=" * 60)
        logger.info("🧠 Scraping actual NBA.com pages to find where they")
        logger.info("   moved the data after deprecating the old endpoints!")
        logger.info("=" * 60)
        
        all_findings = []
        
        for page_info in self.target_pages:
            # Scrape the page
            findings = await self.scrape_page_for_api_endpoints(page_info)
            
            # Test any endpoints we found
            if findings.get('endpoints_found'):
                findings = await self.test_found_endpoints(findings)
            
            all_findings.append(findings)
            
            # Save intermediate results
            self.save_results({
                "page_findings": findings,
                "timestamp": datetime.now().isoformat()
            }, f"reality_check_{page_info['missing_endpoint']}")
            
            # Small delay between pages
            await asyncio.sleep(2)
        
        # Final summary
        total_working_alternatives = len(self.alternative_data_sources)
        total_pages_scraped = len(all_findings)
        
        final_summary = {
            "ultimate_reality_check_summary": {
                "total_pages_scraped": total_pages_scraped,
                "total_working_alternatives_found": total_working_alternatives,
                "timestamp": datetime.now().isoformat()
            },
            "alternative_data_sources": self.alternative_data_sources,
            "detailed_findings": all_findings
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("🏆 ULTIMATE REALITY CHECK COMPLETE!")
        logger.info(f"📊 Pages Scraped: {total_pages_scraped}")
        logger.info(f"🎯 Working Alternatives Found: {total_working_alternatives}")
        
        if total_working_alternatives > 0:
            logger.info("\n🚀 ALTERNATIVE DATA SOURCES DISCOVERED:")
            for alt in self.alternative_data_sources:
                logger.info(f"   ✅ {alt['alternative_endpoint']} replaces {alt['original_missing']}")
        
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
    reality_checker = UltimateNBARealityCheck()
    
    try:
        results = await reality_checker.run_ultimate_reality_check()
        reality_checker.save_results(results, "ultimate_nba_reality_check_final")
        
        # Print summary for easy viewing
        print("\n" + "="*80)
        print("🔍 ULTIMATE NBA REALITY CHECK SUMMARY")
        print("="*80)
        
        if results['alternative_data_sources']:
            print("🚀 WORKING ALTERNATIVE ENDPOINTS FOUND:")
            for alt in results['alternative_data_sources']:
                print(f"   ✅ {alt['alternative_endpoint']} ({alt['record_count']} records)")
                print(f"      Replaces: {alt['original_missing']}")
                print(f"      Source: {alt['discovery_source']}")
                print()
        else:
            print("❌ No working alternatives found")
        
        print(f"📊 Total Alternative Sources: {len(results['alternative_data_sources'])}")
        print("="*80)
        
    except Exception as e:
        logger.error(f"💥 Reality check failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())