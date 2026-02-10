import requests
import json
from datetime import datetime, timedelta

# BettingPros API headers
headers = {
    "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
    "referer": "https://www.bettingpros.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Check tomorrow's games
tomorrow = datetime.utcnow() + timedelta(days=1)
tomorrow_str = tomorrow.strftime("%Y-%m-%d")

print(f"Fetching games for tomorrow: {tomorrow_str}")

# Fetch events
url = "https://api.bettingpros.com/v3/events"
params = {
    "sport": "NBA", 
    "date": tomorrow_str,
    "lineups": "true"
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print(f"Found {len(data.get('events', []))} events for tomorrow")

for event in data.get('events', []):
    home = event.get('home', 'Unknown')
    visitor = event.get('visitor', 'Unknown')
    event_id = event.get('id')
    print(f"Event {event_id}: {visitor} @ {home}")
    
    # Check if this is Rockets vs Clippers
    if (home == 'HOU' and visitor == 'LAC') or (home == 'LAC' and visitor == 'HOU'):
        print(f"  -> Found Rockets vs Clippers game!")
        print(f"  -> Full event data: {json.dumps(event, indent=2)}")