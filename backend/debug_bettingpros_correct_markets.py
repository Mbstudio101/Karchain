
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
    
    # Now let's check if there are props for the Lakers game using the correct market IDs
    if lakers_event_id:
        print(f"\nChecking props for Lakers game (ID: {lakers_event_id}) using correct market IDs...")
        
        # Use the actual market IDs from the scraper
        market_ids = [156, 157, 159]  # Just check main markets
        
        for market_id in market_ids:
            market_name = scraper.prop_markets.get(market_id, f"Unknown_{market_id}")
            print(f"  Testing {market_name} (market_id {market_id})...")
            offers_data = scraper._get_api("offers", {
                "sport": "NBA",
                "market_id": market_id,
                "event_id": lakers_event_id,
                "live": "false"
            })
            
            if offers_data and offers_data.get("offers"):
                offers = offers_data["offers"]
                print(f"    Found {len(offers)} offers for {market_name}")
                
                lakers_count = 0
                spurs_count = 0
                
                for offer in offers:
                    participants = offer.get("participants", [])
                    if participants:
                        player = participants[0].get("player")
                        if player:
                            player_name = f"{player.get('first_name', '')} {player.get('last_name', '')}"
                            player_team = player.get("team", "Unknown")
                            
                            if player_team == "LAL":
                                lakers_count += 1
                                if lakers_count == 1:
                                    print(f"    -> FOUND LAKERS PLAYER: {player_name}")
                            elif player_team == "SAS":
                                spurs_count += 1
                
                print(f"    Summary: {lakers_count} Lakers players, {spurs_count} Spurs players")
            else:
                print(f"    No offers found for {market_name}")
else:
    print("No events found.")
    if events_data:
        print(f"Response: {json.dumps(events_data, indent=2)}")