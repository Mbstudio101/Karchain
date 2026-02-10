#!/usr/bin/env python3
"""
NBA Endpoint Parameter Analyzer - Genius Level Investigation

Deep analysis of parameter requirements for the failing endpoints
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

class NBAParameterAnalyzer:
    """
    Analyze parameter requirements for NBA endpoints
    """
    
    BASE_URL = "https://stats.nba.com/stats"
    
    # Browser config that works (Chrome 120)
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
    
    # Parameter variations to test
    PARAMETER_VARIATIONS = {
        "leaguedashplayerclutch": [
            # Minimal working set
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals"},
            # Add ClutchTime variations
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 5 Minutes"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 2 Minutes"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 1 Minute"},
            # Add PointDiff variations
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 5 Minutes", "PointDiff": 3},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 5 Minutes", "PointDiff": 5},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 5 Minutes", "PointDiff": 10},
            # Add AheadBehind variations
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 5 Minutes", "PointDiff": 5, "AheadBehind": "Ahead"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 5 Minutes", "PointDiff": 5, "AheadBehind": "Behind"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "ClutchTime": "Last 5 Minutes", "PointDiff": 5, "AheadBehind": "Ahead or Behind"},
            # Try without ClutchTime (like working endpoints)
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "MeasureType": "Base"},
        ],
        "leaguedashplayershotlocations": [
            # Minimal working set
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals"},
            # Add DistanceRange variations
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "DistanceRange": "5ft Range"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "DistanceRange": "8ft Range"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "DistanceRange": "By Zone"},
            # Try without DistanceRange (like working endpoints)
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "MeasureType": "Base"},
            # Try with MeasureType
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "MeasureType": "Base", "DistanceRange": "5ft Range"},
        ],
        "leaguedashptstats": [
            # Minimal working set
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "PerGame"},
            # Add PtMeasureType variations
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "PerGame", "PtMeasureType": "Transition"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "PerGame", "PtMeasureType": "SpeedDistance"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "PerGame", "PtMeasureType": "Rebounding"},
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "PerGame", "PtMeasureType": "Possessions"},
            # Try without PtMeasureType (like working endpoints)
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "PerGame", "MeasureType": "Base"},
            # Try with Totals instead of PerGame
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "PtMeasureType": "Transition"},
        ],
        "leaguedashteamstats": [
            # Minimal working set (like working player stats)
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "MeasureType": "Base"},
            # Try without MeasureType
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals"},
            # Try different PerMode
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "PerGame", "MeasureType": "Base"},
            # Try with minimal parameters only
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00"},
            # Try copying exact params from working player stats
            {"Season": "2023-24", "SeasonType": "Regular Season", "LeagueID": "00", "PerMode": "Totals", "MeasureType": "Base", "LastNGames": 0, "Month": 0, "OpponentTeamID": 0, "PORound": 0, "Period": 0, "VsConference": "", "VsDivision": ""},
        ]
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.results = {}
    
    def test_parameter_combination(self, endpoint: str, params: Dict[str, Any], description: str = "") -> Dict[str, Any]:
        """Test a specific parameter combination"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            logger.info(f"\n🔍 Testing {endpoint}")
            logger.info(f"📋 Parameters: {json.dumps(params, indent=2)}")
            logger.info(f"📝 Description: {description}")
            
            response = self.session.get(
                url,
                params=params,
                headers=self.BROWSER_CONFIG['headers'],
                impersonate=self.BROWSER_CONFIG['impersonate'],
                timeout=30
            )
            
            result = {
                "status_code": response.status_code,
                "description": description,
                "params": params,
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
                            "headers": data['resultSets'][0].get('headers', [])[:5]  # First 5 headers
                        })
                        logger.info(f"✅ SUCCESS - {row_count} records")
                    else:
                        logger.warning(f"⚠️ No resultSets found")
                        result["error"] = "No resultSets"
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON")
                    result["error"] = "Invalid JSON"
            else:
                logger.error(f"❌ Status {response.status_code}")
                result["error"] = f"HTTP {response.status_code}"
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Exception: {e}")
            return {
                "status_code": 0,
                "description": description,
                "params": params,
                "success": False,
                "error": str(e)
            }
    
    def analyze_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Analyze all parameter combinations for an endpoint"""
        logger.info(f"\n🎯 ANALYZING {endpoint}")
        logger.info("=" * 60)
        
        variations = self.PARAMETER_VARIATIONS.get(endpoint, [])
        results = []
        
        for i, params in enumerate(variations):
            description = f"Variation {i+1}: {list(params.keys())}"
            result = self.test_parameter_combination(endpoint, params, description)
            results.append(result)
            
            # Add delay between tests
            if i < len(variations) - 1:
                time.sleep(2)
        
        # Find successful combinations
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        analysis = {
            "endpoint": endpoint,
            "total_tests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100 if results else 0,
            "successful_combinations": successful,
            "failed_combinations": failed,
            "recommended_params": successful[0]["params"] if successful else None
        }
        
        return analysis
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run analysis on all failing endpoints"""
        logger.info("🚀 STARTING GENIUS PARAMETER ANALYSIS")
        logger.info("=" * 80)
        
        failing_endpoints = [
            "leaguedashplayerclutch",
            "leaguedashplayershotlocations", 
            "leaguedashptstats",
            "leaguedashteamstats"
        ]
        
        all_results = {}
        
        for endpoint in failing_endpoints:
            analysis = self.analyze_endpoint(endpoint)
            all_results[endpoint] = analysis
            
            # Add longer delay between endpoints
            if endpoint != failing_endpoints[-1]:
                time.sleep(5)
        
        # Generate summary
        summary = {
            "total_endpoints": len(failing_endpoints),
            "endpoints_with_success": sum(1 for r in all_results.values() if r["successful"] > 0),
            "endpoints_fully_failed": sum(1 for r in all_results.values() if r["successful"] == 0),
            "overall_success_rate": sum(r["successful"] for r in all_results.values()) / 
                                  sum(r["total_tests"] for r in all_results.values()) * 100,
            "breakthrough_endpoints": [ep for ep, r in all_results.items() if r["successful"] > 0]
        }
        
        return {
            "summary": summary,
            "detailed_analysis": all_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = "nba_parameter_analysis.json"):
        """Save analysis results"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Analysis saved to {filename}")

def main():
    analyzer = NBAParameterAnalyzer()
    results = analyzer.run_full_analysis()
    analyzer.save_results(results)
    
    # Print summary
    summary = results["summary"]
    logger.info(f"\n🎆 GENIUS ANALYSIS COMPLETE")
    logger.info(f"📊 Total endpoints analyzed: {summary['total_endpoints']}")
    logger.info(f"✅ Endpoints with working params: {summary['endpoints_with_success']}")
    logger.info(f"❌ Endpoints still failing: {summary['endpoints_fully_failed']}")
    logger.info(f"📈 Overall success rate: {summary['overall_success_rate']:.1f}%")
    
    if summary["breakthrough_endpoints"]:
        logger.info(f"🚀 BREAKTHROUGH! Found working parameters for:")
        for ep in summary["breakthrough_endpoints"]:
            logger.info(f"   ✅ {ep}")
    
    return results

if __name__ == "__main__":
    main()