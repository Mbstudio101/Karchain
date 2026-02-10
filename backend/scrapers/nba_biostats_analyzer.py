#!/usr/bin/env python3
"""
NBA Bio Stats Deep Dive - Analyze the new working endpoint
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

class NBABioStatsAnalyzer:
    """
    Analyze what data the biostats endpoint contains
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
    
    def analyze_biostats_endpoint(self) -> Dict[str, Any]:
        """Deep dive into the biostats endpoint"""
        
        logger.info("🧬 ANALYZING NBA BIO STATS ENDPOINT")
        logger.info("=" * 60)
        
        url = "https://stats.nba.com/stats/leaguedashplayerbiostats"
        params = {
            "Season": "2023-24",
            "SeasonType": "Regular Season",
            "LeagueID": "00",
            "PerMode": "Totals"
        }
        
        try:
            logger.info(f"🎯 Fetching biostats data...")
            response = self.session.get(
                url,
                params=params,
                headers=self.BROWSER_CONFIG['headers'],
                impersonate=self.BROWSER_CONFIG['impersonate'],
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'resultSets' in data and len(data['resultSets']) > 0:
                    result_set = data['resultSets'][0]
                    headers = result_set.get('headers', [])
                    row_set = result_set.get('rowSet', [])
                    
                    logger.info(f"✅ SUCCESS - {len(row_set)} records found")
                    logger.info(f"📊 Headers ({len(headers)}): {headers}")
                    
                    # Analyze first few records
                    if row_set:
                        logger.info(f"\n🔍 SAMPLE DATA (first 3 records):")
                        for i, row in enumerate(row_set[:3]):
                            logger.info(f"\nRecord {i+1}:")
                            for j, header in enumerate(headers[:10]):  # First 10 columns
                                if j < len(row):
                                    logger.info(f"  {header}: {row[j]}")
                    
                    # Categorize the data
                    categories = self.categorize_headers(headers)
                    
                    return {
                        "success": True,
                        "record_count": len(row_set),
                        "headers": headers,
                        "categories": categories,
                        "sample_data": row_set[:2] if row_set else [],
                        "data_quality": self.assess_data_quality(headers, row_set)
                    }
                else:
                    logger.error("❌ No resultSets found")
                    return {"success": False, "error": "No resultSets"}
            else:
                logger.error(f"❌ HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"💥 Exception: {e}")
            return {"success": False, "error": str(e)}
    
    def categorize_headers(self, headers: List[str]) -> Dict[str, List[str]]:
        """Categorize headers by type"""
        categories = {
            "player_info": [],
            "traditional_stats": [],
            "advanced_stats": [],
            "physical_stats": [],
            "experience_stats": [],
            "other": []
        }
        
        for header in headers:
            header_lower = header.lower()
            
            if any(term in header_lower for term in ['player', 'name', 'team', 'id']):
                categories["player_info"].append(header)
            elif any(term in header_lower for term in ['age', 'height', 'weight', 'years']):
                categories["physical_stats"].append(header)
            elif any(term in header_lower for term in ['gp', 'min', 'pts', 'reb', 'ast', 'fg', 'ft', '3p']):
                categories["traditional_stats"].append(header)
            elif any(term in header_lower for term in ['per', 'usage', 'ts', 'efg', 'ws', 'bpm']):
                categories["advanced_stats"].append(header)
            elif any(term in header_lower for term in ['draft', 'exp', 'season']):
                categories["experience_stats"].append(header)
            else:
                categories["other"].append(header)
        
        return categories
    
    def assess_data_quality(self, headers: List[str], data: List[List]) -> Dict[str, Any]:
        """Assess the quality and completeness of the data"""
        
        if not data:
            return {"quality": "poor", "reason": "No data"}
        
        # Check for missing values in first 100 records
        sample_data = data[:100] if len(data) > 100 else data
        total_cells = len(sample_data) * len(headers)
        missing_cells = 0
        
        for row in sample_data:
            for value in row:
                if value is None or value == "" or (isinstance(value, (int, float)) and value == 0):
                    missing_cells += 1
        
        missing_percentage = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
        
        # Check for key stats
        key_stats = ['PTS', 'REB', 'AST', 'MIN', 'GP']
        available_key_stats = [stat for stat in key_stats if stat in headers]
        
        quality_score = 100 - missing_percentage
        
        return {
            "quality_score": quality_score,
            "missing_percentage": missing_percentage,
            "available_key_stats": available_key_stats,
            "total_headers": len(headers),
            "sample_size": len(sample_data)
        }
    
    def compare_with_missing_endpoints(self) -> Dict[str, Any]:
        """Compare biostats with what we're missing from clutch/shooting/tracking"""
        
        logger.info(f"\n🔄 COMPARING BIOSTATS WITH MISSING ENDPOINTS")
        logger.info("=" * 60)
        
        # What we're missing
        missing_data = {
            "clutch": ["Last 5 Minutes PTS", "Last 5 Minutes REB", "Last 5 Minutes AST", "Clutch FG%", "Clutch FT%"],
            "shooting": ["FGM by Distance", "FGA by Distance", "FG% by Zone", "Corner 3P%", "Above Break 3P%"],
            "tracking": ["Speed", "Distance", "Touches", "Passing", "Defensive Impact"]
        }
        
        # Get biostats data
        biostats_result = self.analyze_biostats_endpoint()
        
        if not biostats_result["success"]:
            return biostats_result
        
        headers = biostats_result["headers"]
        
        # Check if biostats can partially substitute missing data
        substitutions = {}
        
        for category, missing_fields in missing_data.items():
            found_substitutes = []
            
            for field in missing_fields:
                # Look for similar fields in biostats
                field_lower = field.lower()
                
                for header in headers:
                    header_lower = header.lower()
                    
                    # Simple similarity check
                    if any(term in header_lower for term in field_lower.split()):
                        found_substitutes.append(f"{field} → {header}")
                        break
            
            substitutions[category] = {
                "missing_fields": len(missing_fields),
                "found_substitutes": len(found_substitutes),
                "substitutes": found_substitutes
            }
        
        return {
            "success": True,
            "biostats_analysis": biostats_result,
            "substitution_potential": substitutions,
            "overall_coverage": self.calculate_coverage(substitutions)
        }
    
    def calculate_coverage(self, substitutions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate how well biostats covers missing data"""
        
        total_missing = sum(data["missing_fields"] for data in substitutions.values())
        total_found = sum(data["found_substitutes"] for data in substitutions.values())
        
        coverage_percentage = (total_found / total_missing * 100) if total_missing > 0 else 0
        
        return {
            "total_missing_fields": total_missing,
            "total_found_substitutes": total_found,
            "coverage_percentage": coverage_percentage,
            "by_category": {
                category: {
                    "missing": data["missing_fields"],
                    "found": data["found_substitutes"],
                    "coverage": (data["found_substitutes"] / data["missing_fields"] * 100) if data["missing_fields"] > 0 else 0
                }
                for category, data in substitutions.items()
            }
        }
    
    def save_analysis(self, analysis: Dict[str, Any], filename: str = "nba_biostats_analysis.json"):
        """Save the biostats analysis"""
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"📄 Analysis saved to {filename}")

def main():
    analyzer = NBABioStatsAnalyzer()
    
    # Comprehensive analysis
    analysis = analyzer.compare_with_missing_endpoints()
    
    analyzer.save_analysis(analysis)
    
    # Print summary
    if analysis["success"]:
        biostats = analysis["biostats_analysis"]
        coverage = analysis["overall_coverage"]
        
        logger.info(f"\n🎆 BIOSTATS ANALYSIS COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Records: {biostats['record_count']}")
        logger.info(f"📋 Headers: {biostats['total_headers']}")
        logger.info(f"⭐ Quality Score: {biostats['data_quality']['quality_score']:.1f}%")
        
        logger.info(f"\n🎯 SUBSTITUTION POTENTIAL:")
        logger.info(f"📈 Overall Coverage: {coverage['coverage_percentage']:.1f}%")
        
        for category, data in coverage["by_category"].items():
            logger.info(f"   {category.title()}: {data['found']}/{data['missing']} ({data['coverage']:.1f}%)")
        
        logger.info(f"\n💡 CONCLUSION:")
        if coverage['coverage_percentage'] > 50:
            logger.info(f"✅ BIOSTATS provides significant coverage for missing data!")
            logger.info(f"🚀 Implement biostats immediately for enhanced predictions")
        else:
            logger.info(f"⚠️ BIOSTATS has limited substitution potential")
            logger.info(f"🔍 Focus on the 4 core working endpoints")
    
    return analysis

if __name__ == "__main__":
    main()