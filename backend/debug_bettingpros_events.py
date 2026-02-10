
import requests
import json
from datetime import datetime, timedelta

API_URL = "https://api.bettingpros.com/v3"
API_KEY = "your_api_key_here"  # Wait, I don't have the API key. It's in the code.

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
            # The API uses 'home' and 'visitor' as team abbreviations, not objects
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
                print(f"    Home: {home_team_abbr} ({home_team_name})")
                print(f"    Away: {away_team_abbr} ({away_team_name})")
        else:
            print(f"  Event is not a dict: {event}")
    
    # Now let's check if there are props for the Lakers game
    if lakers_event_id:
        print(f"\nChecking props for Lakers game (ID: {lakers_event_id})...")
        props_data = scraper._get_api("player-props", {
            "eventId": lakers_event_id,
            "market": "all"
        })
        
        if props_data:
            print(f"Found props data: {json.dumps(props_data, indent=2)}")
        else:
            print("No props data found for Lakers game")
else:
    print("No events found.")
    if events_data:
        print(f"Response: {json.dumps(events_data, indent=2)}")