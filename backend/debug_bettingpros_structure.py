
import requests
import json
from datetime import datetime, timedelta

# Let's import the scraper class instead
import sys
import os
sys.path.append(os.getcwd())
from scrapers.bettingpros_scraper import BettingProsScraper

scraper = BettingProsScraper()

# Fetch events for today
today = datetime.utcnow().date()
today_str = today.strftime("%Y-%m-%d")

print(f"Fetching events for {today_str}...")
events_data = scraper._get_api("events", {
    "sport": "NBA", 
    "date": today_str,
    "lineups": "true"
})

if events_data and events_data.get("events"):
    print(f"Found {len(events_data['events'])} events:")
    
    lakers_event_id = None
    
    for event in events_data["events"]:
        if isinstance(event, dict):
            home_team_abbr = event.get("home", "Unknown")
            away_team_abbr = event.get("visitor", "Unknown")
            
            # Get full names from participants
            home_team_name = "Unknown"
            away_team_name = "Unknown"
            
            for participant in event.get("participants", []):
                if participant.get("id") == home_team_abbr:
                    home_team_name = participant.get("name", home_team_abbr)
                elif participant.get("id") == away_team_abbr:
                    away_team_name = participant.get("name", away_team_abbr)
            
            print(f"  - {home_team_name} vs {away_team_name} (ID: {event.get('id')})")
            
            if "Lakers" in home_team_name or "Lakers" in away_team_name:
                print("    -> FOUND LAKERS GAME!")
                lakers_event_id = event.get('id')
                print(f"    Event ID: {lakers_event_id}")
    
    if lakers_event_id:
        print(f"\nChecking props for Lakers game (ID: {lakers_event_id}) using offers endpoint...")
        
        # Check standard player prop markets
        prop_markets = {
            156: "points",
            157: "assists", 
            159: "rebounds",
            151: "threes",
            338: "pts+reb+ast"
        }
        
        for market_id, market_name in prop_markets.items():
            print(f"  Testing {market_name} (market_id {market_id})...")
            offers = scraper._get_api("offers", {
                "market_id": market_id,
                "event_id": lakers_event_id,
                "sport": "NBA",
                "location": "NY"
            })
            
            if offers and offers.get("offers"):
                offer_list = offers.get("offers", [])
                print(f"    Found {len(offer_list)} offers for {market_name}")
                
                # Show first offer structure
                if offer_list:
                    first_offer = offer_list[0]
                    print(f"    First offer keys: {list(first_offer.keys())}")
                    print(f"    First offer: {json.dumps(first_offer, indent=2)}")
                    break  # Just show first one
            else:
                print(f"    No offers found for {market_name}")
else:
    print("No events found.")