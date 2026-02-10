import requests
from datetime import datetime, timedelta

headers = {
    "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
    "referer": "https://www.bettingpros.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

today = datetime.utcnow()
tomorrow = today + timedelta(days=1)

print(f"Today: {today.strftime('%Y-%m-%d')}")
print(f"Tomorrow: {tomorrow.strftime('%Y-%m-%d')}")

# Check what events are available for each date
for date_str in [today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d')]:
    url = f"https://api.bettingpros.com/v3/events"
    params = {
        "sport": "NBA", 
        "date": date_str,
        "lineups": "true"
    }
    print(f"\nFetching events for {date_str}...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('events', []))} events")
            for event in data.get('events', [])[:3]:  # Show first 3
                print(f"  - {event.get('home', 'Unknown')} vs {event.get('visitor', 'Unknown')} (ID: {event.get('id')})")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")