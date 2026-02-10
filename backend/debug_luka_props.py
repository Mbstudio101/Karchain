
import requests
import json
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.getcwd())
from scrapers.bettingpros_scraper import BettingProsScraper

scraper = BettingProsScraper()

# Get the Dallas game ID
today = datetime.utcnow().date()
today_str = today.strftime("%Y-%m-%d")

events_data = scraper._get_api("events", {
    "sport": "NBA", 
    "date": today_str,
    "lineups": "true"
})

dallas_event_id = None
for event in events_data["events"]:
    if event.get("home") == "DAL" or event.get("visitor") == "DAL":
        dallas_event_id = event.get('id')
        break

if dallas_event_id:
    print(f"Dallas game ID: {dallas_event_id}")
    
    # Check all major prop markets for Luka
    prop_markets = {
        156: "points",
        157: "assists", 
        159: "rebounds",
        151: "threes",
        338: "pts+reb+ast"
    }
    
    luka_found = False
    
    for market_id, market_name in prop_markets.items():
        print(f"\nChecking {market_name} (market_id {market_id})...")
        
        offers_data = scraper._get_api("offers", {
            "market_id": market_id,
            "event_id": dallas_event_id,
            "sport": "NBA",
            "location": "NY"
        })
        
        if offers_data and offers_data.get("offers"):
            offer_list = offers_data.get("offers", [])
            print(f"  Found {len(offer_list)} offers")
            
            # Look for Luka in this market
            for offer in offer_list:
                participants = offer.get("participants", [])
                if participants:
                    first_participant = participants[0]
                    player_name = first_participant.get("name", "").lower()
                    
                    if "luka" in player_name or "doncic" in player_name:
                        player = first_participant.get("player", {})
                        team = player.get("team", "Unknown")
                        print(f"  🎯 FOUND LUKA DONCIC in {market_name}!")
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
                        
                        luka_found = True
                        break
            
            if luka_found:
                break
        else:
            print(f"  No offers found for {market_name}")
    
    if not luka_found:
        print(f"\n❌ Luka Doncic not found in any prop markets for today's game!")
        
        # Let's also check what Dallas players ARE available
        print(f"\nAvailable Dallas players in prop markets:")
        for market_id, market_name in prop_markets.items():
            offers_data = scraper._get_api("offers", {
                "market_id": market_id,
                "event_id": dallas_event_id,
                "sport": "NBA",
                "location": "NY"
            })
            
            if offers_data and offers_data.get("offers"):
                for offer in offers_data.get("offers", []):
                    participants = offer.get("participants", [])
                    if participants:
                        first_participant = participants[0]
                        player = first_participant.get("player", {})
                        team = player.get("team", "Unknown")
                        
                        if team == "DAL":
                            print(f"  {first_participant.get('name')} in {market_name}")
else:
    print("No Dallas game found")