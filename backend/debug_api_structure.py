
import requests
import json
from datetime import datetime, timedelta

# Let's test if there's a player-specific endpoint
import sys
import os
sys.path.append(os.getcwd())
from scrapers.bettingpros_scraper import BettingProsScraper

scraper = BettingProsScraper()

# Let's try to fetch player data directly
today = datetime.utcnow().date()
today_str = today.strftime("%Y-%m-%d")

print(f"Testing different API endpoints for {today_str}...")

# Test 1: Try to get player data from events with lineups
events_data = scraper._get_api("events", {
    "sport": "NBA", 
    "date": today_str,
    "lineups": "true",
    "include_players": "true"  # Try adding this parameter
})

if events_data and events_data.get("events"):
    print("\nEvent with detailed participants:")
    lakers_event = None
    
    for event in events_data["events"]:
        if isinstance(event, dict):
            home_team_abbr = event.get("home", "Unknown")
            away_team_abbr = event.get("visitor", "Unknown")
            
            # Check if this is Lakers game
            if home_team_abbr == "LAL" or away_team_abbr == "LAL":
                lakers_event = event
                print(f"Found Lakers game (ID: {event.get('id')})")
                
                # Check if we have detailed participant info
                if event.get("participants"):
                    for participant in event["participants"]:
                        print(f"  Participant: {participant}")
                        # Look for any player-related fields
                        for key, value in participant.items():
                            if isinstance(value, dict) and any(player_key in str(value).lower() for player_key in ['player', 'name', 'first', 'last']):
                                print(f"    {key}: {value}")
                
                # Also check if there's a "players" field
                if event.get("players"):
                    print(f"  Found players array: {len(event['players'])} players")
                    for player in event["players"][:3]:  # Show first 3
                        print(f"    Player: {player}")
                
                break

# Test 2: Try a different approach - maybe we need to fetch player props differently
print("\n\nTesting alternative approach - checking if offers have embedded player data...")

if lakers_event:
    # Get offers for points market
    offers_data = scraper._get_api("offers", {
        "market_id": 156,  # Points
        "event_id": lakers_event.get('id'),
        "sport": "NBA",
        "location": "NY",
        "include_players": "true"  # Try this parameter
    })
    
    if offers_data and offers_data.get("offers"):
        print(f"Found {len(offers_data['offers'])} offers")
        
        # Look for any offer with player data
        for offer in offers_data["offers"][:2]:  # Check first 2 offers
            print(f"\nOffer structure:")
            for key, value in offer.items():
                if key not in ['selections']:  # Skip the long selections array
                    print(f"  {key}: {value}")
                
                # Check if any value contains player info
                if isinstance(value, str) and any(name in value.lower() for name in ['lebron', 'james', 'luka', 'doncic']):
                    print(f"    -> FOUND PLAYER NAME IN {key}!")
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, str) and any(name in subvalue.lower() for name in ['lebron', 'james', 'luka', 'doncic']):
                            print(f"    -> FOUND PLAYER NAME IN {key}.{subkey}!")

# Test 3: Try to find if there's a players endpoint
print("\n\nTesting players endpoint...")
try:
    players_data = scraper._get_api("players", {
        "sport": "NBA",
        "date": today_str
    })
    if players_data:
        print(f"Players endpoint returned: {players_data}")
except Exception as e:
    print(f"Players endpoint not available: {e}")

print("\n\nConclusion: The API structure has changed. We need to find where player names are now stored.")