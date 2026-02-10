
import requests
import json
from datetime import datetime, timedelta

# Let's test the exact API call the scraper makes
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
    
    # Test the exact API call the scraper makes
    offers_data = scraper._get_api("offers", {
        "market_id": 156,  # Points
        "event_id": lakers_event_id,
        "sport": "NBA",
        "location": "NY"
    })
    
    if offers_data and offers_data.get("offers"):
        print(f"\nFound {len(offers_data['offers'])} offers for points market")
        
        # Test the scraper's logic step by step
        for i, offer in enumerate(offers_data["offers"][:3]):  # Test first 3 offers
            print(f"\n--- Offer {i+1} ---")
            print(f"Offer ID: {offer.get('id')}")
            
            # Step 1: Check for participants
            participants = offer.get("participants", [])
            print(f"Participants found: {len(participants)}")
            
            if participants:
                # Step 2: Get first participant
                first_participant = participants[0]
                print(f"First participant: {first_participant.get('name')} (ID: {first_participant.get('id')})")
                
                # Step 3: Get player info
                player = first_participant.get("player")
                if player:
                    print(f"Player: {player.get('first_name')} {player.get('last_name')}")
                    print(f"Team: {player.get('team')}")
                else:
                    print("No player object found in participant")
            else:
                print("No participants found - this offer will be skipped by scraper")
                
            # Show all keys in the offer to see what we're missing
            print(f"Offer keys: {list(offer.keys())}")
            
            # Also check if there's a player_id field
            player_id = offer.get("player_id")
            if player_id:
                print(f"Player ID found: {player_id}")
                
                # Try to find player by ID in participants
                for p in participants:
                    if p.get("id") == str(player_id):
                        print(f"Matched player_id {player_id} to participant: {p.get('name')}")
                        break
    else:
        print("No offers data found")
else:
    print("No Lakers game found")