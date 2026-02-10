#!/usr/bin/env python3
"""
NBA API Endpoint Mapping and Detailed Analysis

This script provides detailed mapping of all NBA.com stats pages to their
underlying API endpoints with exact parameter configurations.
"""

import requests
import json
from datetime import datetime

class NBAEndpointMapper:
    """Maps NBA.com stats pages to their API endpoints"""
    
    # Base NBA stats API URL
    BASE_URL = "https://stats.nba.com/stats"
    
    # Required headers for NBA API access
    HEADERS = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'stats.nba.com',
        'Origin': 'https://www.nba.com',
        'Referer': 'https://www.nba.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-nba-stats-origin': 'stats',
        'x-nba-stats-token': 'true'
    }
    
    # Detailed mapping of NBA.com pages to API endpoints
    DETAILED_ENDPOINT_MAPPING = {
        # PLAYER STATISTICS ENDPOINTS
        "https://www.nba.com/stats/players/traditional": {
            "endpoint": "leaguedashplayerstats",
            "description": "Traditional Player Statistics",
            "measure_type": "Base",
            "per_mode": "Totals",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "MeasureType": "Base"
            },
            "key_stats": [
                "PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", 
                "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT"
            ]
        },
        
        "https://www.nba.com/stats/players/clutch-traditional": {
            "endpoint": "leaguedashplayerclutch",
            "description": "Player Clutch Statistics (Last 5 min, +/- 5 points)",
            "measure_type": "Base",
            "per_mode": "Totals", 
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "ClutchTime": "Last 5 Minutes",
                "PointDiff": 5
            },
            "key_stats": [
                "PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", 
                "REB", "AST", "PLUS_MINUS", "FG_PCT", "FG3_PCT"
            ]
        },
        
        "https://www.nba.com/stats/players/shots-general": {
            "endpoint": "leaguedashplayershotlocations",
            "description": "Player Shot Locations and General Shooting Stats",
            "measure_type": "Base",
            "per_mode": "Totals",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season", 
                "LeagueID": "00",
                "PerMode": "Totals",
                "DistanceRange": "5ft Range"
            },
            "key_stats": [
                "PLAYER_NAME", "TEAM_ABBREVIATION", "FGM", "FGA", "FG_PCT",
                "FG3M", "FG3A", "FG3_PCT", "EFG_PCT", "SHOT_DISTANCE"
            ]
        },
        
        "https://www.nba.com/stats/players/defense-dash-overall": {
            "endpoint": "leaguedashptdefend",
            "description": "Player Defense Statistics (Defended FG%, etc.)",
            "measure_type": "Base",
            "per_mode": "Totals",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00", 
                "PerMode": "Totals",
                "DefenseCategory": "Overall"
            },
            "key_stats": [
                "PLAYER_NAME", "TEAM_ABBREVIATION", "DEF_RIM_FGM", "DEF_RIM_FGA",
                "DEF_RIM_FG_PCT", "DREB", "STL", "BLK"
            ]
        },
        
        "https://www.nba.com/stats/players/transition": {
            "endpoint": "leaguedashptstats",
            "description": "Player Transition Statistics (Fast break, etc.)",
            "measure_type": "Transition",
            "per_mode": "PerGame",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "PerGame",
                "PtMeasureType": "Transition"
            },
            "key_stats": [
                "PLAYER_NAME", "TEAM_ABBREVIATION", "TRANSITION_FGM", "TRANSITION_FGA",
                "TRANSITION_FG_PCT", "TRANSITION_PTS", "TRANSITION_POSS"
            ]
        },
        
        "https://www.nba.com/stats/players/catch-shoot": {
            "endpoint": "leaguedashptstats",
            "description": "Player Catch and Shoot Statistics",
            "measure_type": "CatchShoot",
            "per_mode": "PerGame",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "PerGame", 
                "PtMeasureType": "CatchShoot"
            },
            "key_stats": [
                "PLAYER_NAME", "TEAM_ABBREVIATION", "CATCH_SHOOT_FGM", "CATCH_SHOOT_FGA",
                "CATCH_SHOOT_FG_PCT", "CATCH_SHOOT_PTS", "CATCH_SHOOT_EFG_PCT"
            ]
        },
        
        "https://www.nba.com/stats/players/hustle": {
            "endpoint": "leaguehustlestatsplayer",
            "description": "Player Hustle Statistics (Loose balls, charges, etc.)",
            "measure_type": "Base",
            "per_mode": "Totals",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals"
            },
            "key_stats": [
                "PLAYER_NAME", "TEAM_ABBREVIATION", "SCREEN_ASSISTS", "SCREEN_AST_PTS",
                "LOOSE_BALLS_RECOVERED", "CHARGES_DRAWN", "DEFLECTIONS"
            ]
        },
        
        # TEAM STATISTICS ENDPOINTS
        "https://www.nba.com/stats/teams/traditional": {
            "endpoint": "leaguedashteamstats",
            "description": "Traditional Team Statistics",
            "measure_type": "Base",
            "per_mode": "Totals",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "MeasureType": "Base"
            },
            "key_stats": [
                "TEAM_NAME", "GP", "W", "L", "W_PCT", "MIN", "PTS", "REB", 
                "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT"
            ]
        },
        
        "https://www.nba.com/stats/teams/defense-dash-overall": {
            "endpoint": "leaguedashptdefend",
            "description": "Team Defense Statistics",
            "measure_type": "Base", 
            "per_mode": "Totals",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals",
                "DefenseCategory": "Overall"
            },
            "key_stats": [
                "TEAM_NAME", "DEF_RIM_FGM", "DEF_RIM_FGA", "DEF_RIM_FG_PCT",
                "DREB", "STL", "BLK", "OPP_PTS"
            ]
        },
        
        "https://www.nba.com/stats/teams/hustle": {
            "endpoint": "leaguehustlestatsteam",
            "description": "Team Hustle Statistics",
            "measure_type": "Base",
            "per_mode": "Totals",
            "season_type": "Regular Season",
            "example_params": {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "LeagueID": "00",
                "PerMode": "Totals"
            },
            "key_stats": [
                "TEAM_NAME", "SCREEN_ASSISTS", "SCREEN_AST_PTS", "LOOSE_BALLS_RECOVERED",
                "CHARGES_DRAWN", "DEFLECTIONS", "CONTESTED_SHOTS_2PT", "CONTESTED_SHOTS_3PT"
            ]
        }
    }
    
    def test_endpoint(self, endpoint_info: dict, season: str = "2023-24") -> dict:
        """Test a specific NBA API endpoint"""
        url = f"{self.BASE_URL}/{endpoint_info['endpoint']}"
        
        # Build parameters
        params = endpoint_info['example_params'].copy()
        params['Season'] = season
        
        try:
            response = requests.get(url, headers=self.HEADERS, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract result set information
            if 'resultSets' in data and len(data['resultSets']) > 0:
                result_set = data['resultSets'][0]
                return {
                    "status": "success",
                    "endpoint": endpoint_info['endpoint'],
                    "row_count": len(result_set.get('rowSet', [])),
                    "headers": result_set.get('headers', []),
                    "sample_data": result_set.get('rowSet', [])[:3] if result_set.get('rowSet') else [],
                    "url": response.url
                }
            else:
                return {
                    "status": "no_data",
                    "endpoint": endpoint_info['endpoint'],
                    "message": "No result sets returned",
                    "url": response.url
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "endpoint": endpoint_info['endpoint'],
                "error": str(e),
                "url": url
            }
    
    def discover_all_endpoints(self, season: str = "2023-24"):
        """Test all mapped NBA API endpoints"""
        print("🔍 NBA API Endpoint Discovery")
        print("=" * 50)
        
        working_endpoints = []
        failed_endpoints = []
        
        for page_url, endpoint_info in self.DETAILED_ENDPOINT_MAPPING.items():
            print(f"\n📊 Testing: {endpoint_info['description']}")
            print(f"🔗 Page: {page_url}")
            print(f"🎯 API: {endpoint_info['endpoint']}")
            
            result = self.test_endpoint(endpoint_info, season)
            
            if result['status'] == 'success':
                print(f"✅ SUCCESS - Rows: {result['row_count']}, Headers: {len(result['headers'])}")
                print(f"📋 Sample headers: {', '.join(result['headers'][:5])}...")
                working_endpoints.append(endpoint_info['endpoint'])
            elif result['status'] == 'no_data':
                print(f"⚠️  NO DATA - {result['message']}")
            else:
                print(f"❌ FAILED - {result['error']}")
                failed_endpoints.append(endpoint_info['endpoint'])
            
            # Rate limiting
            import time
            time.sleep(1)
        
        print("\n" + "=" * 50)
        print("📈 SUMMARY")
        print(f"✅ Working endpoints: {len(working_endpoints)}")
        print(f"❌ Failed endpoints: {len(failed_endpoints)}")
        print(f"📋 Working: {', '.join(working_endpoints)}")
        
        return working_endpoints, failed_endpoints
    
    def generate_api_calls(self):
        """Generate ready-to-use API call examples"""
        print("\n🚀 NBA API Call Examples")
        print("=" * 50)
        
        examples = []
        
        for page_url, endpoint_info in self.DETAILED_ENDPOINT_MAPPING.items():
            params = endpoint_info['example_params']
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.BASE_URL}/{endpoint_info['endpoint']}?{param_str}"
            
            example = {
                "description": endpoint_info['description'],
                "page_url": page_url,
                "api_url": url,
                "endpoint": endpoint_info['endpoint'],
                "key_stats": endpoint_info['key_stats']
            }
            
            examples.append(example)
            
            print(f"\n📊 {endpoint_info['description']}")
            print(f"🔗 NBA Page: {page_url}")
            print(f"🎯 API Endpoint: {endpoint_info['endpoint']}")
            print(f"📡 Full URL: {url}")
            print(f"📋 Key Stats: {', '.join(endpoint_info['key_stats'][:5])}...")
        
        return examples
    
    def save_mapping_to_file(self, filename: str = "nba_api_mapping.json"):
        """Save the endpoint mapping to a JSON file"""
        mapping_data = {
            "created_at": datetime.now().isoformat(),
            "base_url": self.BASE_URL,
            "headers": self.HEADERS,
            "endpoints": self.DETAILED_ENDPOINT_MAPPING,
            "total_endpoints": len(self.DETAILED_ENDPOINT_MAPPING)
        }
        
        with open(filename, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        print(f"💾 Saved NBA API mapping to {filename}")

def main():
    """Main function to run the NBA API endpoint discovery"""
    mapper = NBAEndpointMapper()
    
    print("🎯 Starting NBA API Endpoint Discovery...")
    print("This will test all the endpoints mapped from your NBA links")
    
    # Discover all endpoints
    working, failed = mapper.discover_all_endpoints(season="2023-24")
    
    # Generate API call examples
    examples = mapper.generate_api_calls()
    
    # Save mapping to file
    mapper.save_mapping_to_file("nba_api_complete_mapping.json")
    
    print(f"\n🎉 Discovery complete!")
    print(f"Found {len(working)} working NBA API endpoints")
    print(f"Check nba_api_complete_mapping.json for complete details")

if __name__ == "__main__":
    main()