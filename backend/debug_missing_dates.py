import requests
from datetime import datetime, timedelta

headers = {
    "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
    "referer": "https://www.bettingpros.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Check what games are available for the dates with missing odds
dates_to_check = ["2026-02-10", "2026-02-12", "2026-02-13"]

for date_str in dates_to_check:
    url = f"https://api.bettingpros.com/v3/events"
    params = {
        "sport": "NBA", 
        "date": date_str,
        "lineups": "true"
    }
    
    print(f"\n=== Fetching events for {date_str} ===")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"Found {len(events)} events")
            for event in events:
                home = event.get('home', 'Unknown')
                away = event.get('visitor', 'Unknown')
                print(f"  - {home} vs {away}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")