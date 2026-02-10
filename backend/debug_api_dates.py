import requests
import json
from datetime import datetime, timedelta

# Check what dates the API is returning
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

today = datetime.utcnow()
tomorrow = today + timedelta(days=1)

print(f"Today: {today.strftime('%Y-%m-%d')}")
print(f"Tomorrow: {tomorrow.strftime('%Y-%m-%d')}")

# Check what events are available for each date
for date_str in [today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d')]:
    url = f"https://api.bettingpros.com/v3/events?league=nba&date={date_str}"
    print(f"\nFetching events for {date_str}...")
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('events', []))} events")
            for event in data.get('events', [])[:3]:  # Show first 3
                print(f"  - {event.get('home_team', 'Unknown')} vs {event.get('away_team', 'Unknown')}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")