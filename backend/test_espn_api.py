import requests
import json

url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
print(f"Fetching from {url}...")

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    events = data.get("events", [])
    print(f"Found {len(events)} events.")
    
    for event in events:
        status = event.get("status", {})
        type_data = status.get("type", {})
        game_status = type_data.get("description", "Unknown")
        name = event.get("name", "Unknown Game")
        date = event.get("date", "Unknown Date")
        
        eid = event.get("id", "Unknown ID")
        print(f"Game: {name} | ID: {eid} | Date: {date} | Status: {game_status}")
        # print(json.dumps(event, indent=2)) # verbose
        
except Exception as e:
    print(f"Error: {e}")
