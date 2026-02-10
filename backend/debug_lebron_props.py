
import requests
import json
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.getcwd())
from scrapers.bettingpros_scraper import BettingProsScraper

scraper = BettingProsScraper()

# Get the Lakers game ID
today = datetime.utcnow().date()
today_str = today.strftime("%Y-%m-%d")

events_data = scraper._get_api("events", {
    "sport": "NBA", 
    "date": today_str,
    "lineups": "true"
})

lakers_event_id = None
for event in events_data["events"]:
    if event.get("home") == "LAL" or event.get("visitor") == "LAL":
        lakers_event_id = event.get('id')
        break

if lakers_event_id:
    print(f"Lakers game ID: {lakers_event_id}")
    
    # Check all major prop markets for LeBron
    prop_markets = {
        156: "points",
        157: "assists", 
        159: "rebounds",
        151: "threes",
        338: "pts+reb+ast",
        155: "steals",
        158: "blocks",
        154: "turnovers"
    }
    
    lebron_found = False
    
    for market_id, market_name in prop_markets.items():
        print(f"\nChecking {market_name} (market_id {market_id})...")
        
        offers_data = scraper._get_api("offers", {
            "market_id": market_id,
            "event_id": lakers_event_id,
            "sport": "NBA",
            "location": "NY"
        })
        
        if offers_data and offers_data.get("offers"):
            offer_list = offers_data.get("offers", [])
            print(f"  Found {len(offer_list)} offers")
            
            # Look for LeBron in this market
            for offer in offer_list:
                participants = offer.get("participants", [])
                if participants:
                    first_participant = participants[0]
                    player_name = first_participant.get("name", "").lower()
                    
                    if "lebron" in player_name or "james" in player_name:
                        player = first_participant.get("player", {})
                        team = player.get("team", "Unknown")
                        print(f"  🎯 FOUND LEBRON JAMES in {market_name}!")
                        print(f"    Name: {first_participant.get('name')}")
                        print(f"    Team: {team}")
                        print(f"    Player ID: {offer.get('player_id')}")
                        
                        # Show the line/odds
                        selections = offer.get("selections", [])
                        for sel in selections:
                            books = sel.get("books", [])
                            if books:
                                lines = books[0].get("lines", [])
                                if lines:
                                    line = lines[0].get("line")
                                    cost = lines[0].get("cost")
                                    selection = sel.get("selection", "").lower()
                                    print(f"    {selection.title()}: {line} @ {cost} (decimal)")
                        
                        lebron_found = True
                        break
            
            if lebron_found:
                break
        else:
            print(f"  No offers found for {market_name}")
    
    if not lebron_found:
        print(f"\n❌ LeBron James not found in any prop markets for today's game!")
        print("Possible reasons:")
        print("1. LeBron is injured/resting")
        print("2. Props haven't been posted yet")
        print("3. He's listed under a different name format")
        
        # Let's also check if there are any props with "James" in the name
        print("\nChecking all players with 'James' in name...")
        for market_id, market_name in prop_markets.items():
            offers_data = scraper._get_api("offers", {
                "market_id": market_id,
                "event_id": lakers_event_id,
                "sport": "NBA",
                "location": "NY"
            })
            
            if offers_data and offers_data.get("offers"):
                for offer in offers_data.get("offers", []):
                    participants = offer.get("participants", [])
                    if participants:
                        first_participant = participants[0]
                        player_name = first_participant.get("name", "").lower()
                        
                        if "james" in player_name:
                            print(f"  Found player with 'James' in name: {first_participant.get('name')} in {market_name}")
else:
    print("No Lakers game found")